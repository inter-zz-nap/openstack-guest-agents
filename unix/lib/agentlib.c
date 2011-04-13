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

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <signal.h>
#include <string.h>
#include <pthread.h>
#include <assert.h>
#include <errno.h>
#include "libagent_int.h"
#include "agentlib.h"

#define AGENTLIB_MODULE_NAME "agentlib"

static PyObject *_agentlib_get_version(PyObject *self, PyObject *args)
{
    return PyString_FromString(AGENT_VERSION);
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

PyMODINIT_FUNC AGENTLIB_PUBLIC_API initagentlib(void)
{
    static PyMethodDef _agentlib_methods[] =
    {
        { "get_version", (PyCFunction)_agentlib_get_version,
                METH_NOARGS, "Get the agent version string" },
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
