/*
 * vim: tabstop=4 shiftwidth=4 softtabstop=4
 *
 * Copyright (c) 2011 Openstack, LLC.
 * All Rights Reserved.
 *
 *    Licensed under the Apache License, Version 2.0 (the "License"); you may
 *    not use this file except in compliance with the License. You may obtain
 *    a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 *    Unless required by applicable law or agreed to in writing, software
 *    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 *    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 *    License for the specific language governing permissions and limitations
 *    under the License.
 */

#define _BSD_SOURCE

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <signal.h>
#include <string.h>
#if HAVE_CRYPT_H
#include <crypt.h>
#endif
#include <pthread.h>
#include <assert.h>
#include <errno.h>
#include <sys/socket.h>
#include <net/if.h>
#include <net/ethernet.h>
#if defined(__linux__)
#include <netpacket/packet.h>
#include <net/if_arp.h>
#elif defined(__FreeBSD__)
#include <net/if_dl.h>
#include <net/if_types.h>
#else
#error Unknown operating system
#endif
#include <ifaddrs.h>
#include "libagent_int.h"
#include "agentlib.h"

#define AGENTLIB_MODULE_NAME "agentlib"

static PyObject *_agentlib_get_version(PyObject *self, PyObject *args)
{
    return PyString_FromString(AGENT_VERSION);
}

static PyObject *_agentlib_get_interfaces(PyObject *self, PyObject *args)
{
    struct ifaddrs *ifa;
    if (getifaddrs(&ifa) < 0)
        return PyErr_SetFromErrno(PyExc_OSError);

    PyObject *interfaces = PyList_New(0);
    if (!interfaces)
        return NULL;

    while (ifa) {
        if (ifa->ifa_flags & IFF_LOOPBACK)
            goto next;

#if defined(__linux__)
        if (ifa->ifa_addr->sa_family != PF_PACKET)
            goto next;

        struct sockaddr_ll *sll = (struct sockaddr_ll *)ifa->ifa_addr;
        if (sll->sll_hatype != ARPHRD_ETHER)
            goto next;

        unsigned char *lladdr = sll->sll_addr;
#elif defined(__FreeBSD__)
        if (ifa->ifa_addr->sa_family != AF_LINK)
            goto next;

        struct sockaddr_dl *sdl = (struct sockaddr_dl *)ifa->ifa_addr;
        if (sdl->sdl_type != IFT_ETHER)
            goto next;

        unsigned char *lladdr = (unsigned char *)LLADDR(sdl);
#endif

        char macaddr[sizeof("00:11:22:33:44:55") + 1];
        snprintf(macaddr, sizeof(macaddr), "%02x:%02x:%02x:%02x:%02x:%02x",
                lladdr[0], lladdr[1], lladdr[2],
                lladdr[3], lladdr[4], lladdr[5]);

        PyObject *arg = Py_BuildValue("ss", ifa->ifa_name, macaddr);
        if (!arg)
            goto err;

        int ret = PyList_Append(interfaces, arg);
        Py_DECREF(arg);
        if (ret < 0)
            goto err;

next:
        ifa = ifa->ifa_next;
    }
    freeifaddrs(ifa);

    return interfaces;

err:
    Py_DECREF(interfaces);
    freeifaddrs(ifa);

    return NULL;
}


static PyObject *_agentlib_register(PyObject *self, PyObject *args)
{
    PyObject *exchange_plugin;
    PyObject *parser_plugin;
    int err;

    if (!PyArg_ParseTuple(args, "OO",
                &exchange_plugin,
                &parser_plugin))
    {
        return PyErr_Format(PyExc_TypeError, "run() requires 2 plugin instances as arguments");
    }

    err = agent_plugin_register(exchange_plugin, parser_plugin);
    if (err < 0)
    {
        /* Exception is already set */
        return NULL;
    }

    Py_RETURN_NONE;
}

static PyObject *_agentlib_sethostname(PyObject *self, PyObject *args)
{
    char *host_string;
    int err;
    size_t host_len;

    if (!PyArg_ParseTuple(args, "s", &host_string))
    {
        return NULL;
    }

    host_len = strlen(host_string);
    if (host_len > 63)
        host_len = 63;

    err = sethostname(host_string, host_len);
    if (err < 0)
    {
        err = errno;
        return PyErr_Format(PyExc_SystemError,
                "sethostname() failed with errno '%d'", err);
    }

    Py_RETURN_NONE;
}

static PyObject *_agentlib_encrypt_password(PyObject *self, PyObject *args)
{
    char *password;
    char *salt;
    char *enc_pass;

    if (!PyArg_ParseTuple(args, "ss", &password, &salt))
    {
        return NULL;
    }

    /* XXX crypt() is normally not reentrant, but since we're using this
     * module in python and the GIL is still locked, this prevents more
     * than 1 crypt() from happening at the same time
     */
    enc_pass = crypt(password, salt);
    if (enc_pass == NULL)
    {
        return PyErr_Format(PyExc_SystemError,
                "crypt() failed with errno: %d", errno);
    }

    return PyString_FromString(enc_pass);
}

PyMODINIT_FUNC AGENTLIB_PUBLIC_API initagentlib(void)
{
    static PyMethodDef _agentlib_methods[] =
    {
        { "get_version", (PyCFunction)_agentlib_get_version,
                METH_NOARGS, "Get the agent version string" },
        { "get_interfaces", (PyCFunction)_agentlib_get_interfaces,
                METH_NOARGS, "Get the network interface names and "
                             "MAC addresses" },
        { "sethostname", (PyCFunction)_agentlib_sethostname,
                METH_VARARGS, "Set the system hostname" },
        { "encrypt_password", (PyCFunction)_agentlib_encrypt_password,
                METH_VARARGS, "Encrypt a password" },
        { "register", (PyCFunction)_agentlib_register,
                METH_VARARGS, "Register an exchange plugin to run" },
        { NULL, NULL, METH_NOARGS, NULL }
    };

    PyGILState_STATE gstate;
    int err;

    /* Acquire GIL */
    gstate = PyGILState_Ensure();

    err = agent_plugin_init();
    if (err < 0)
    {
        PyErr_Format(PyExc_SystemError, "Couldn't init the plugin interface");

        /* Release GIL */
        PyGILState_Release(gstate);

        return;
    }

    /* Create a new module */
    PyObject *pymod = Py_InitModule(AGENTLIB_MODULE_NAME,
            _agentlib_methods);
    if (pymod == NULL)
    {
        agent_plugin_deinit();

        /* Release GIL */
        PyGILState_Release(gstate);

        return;
    }

    PyObject *main_mod = PyImport_AddModule("__main__");

    Py_INCREF(pymod);

    /* Add the new module to the __main__ dictionary */
    PyModule_AddObject(main_mod, AGENTLIB_MODULE_NAME, pymod);

    /* Release GIL */
    PyGILState_Release(gstate);

    return;
}
