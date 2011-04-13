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


typedef struct agent_plugin_info agent_plugin_info_t;

struct agent_plugin_info
{
    pthread_t thr_id;
    PyObject *exchange;
    PyObject *parser;
    PyObject *get_request;
    PyObject *put_response;
    PyObject *parse_request;
};

pthread_mutex_t _plugins_lock;
static agent_plugin_info_t *_plugins = NULL;
static int _num_plugins = 0;

static int _plugins_running = 0;
static int _plugins_die = 0;


static void _plugin_info_init(agent_plugin_info_t *pi,
        PyObject *exchange, PyObject *parser)
{
    memset(pi, 0, sizeof(agent_plugin_info_t));

    Py_INCREF(exchange);
    Py_INCREF(parser);

    pi->exchange = exchange;
    pi->parser = parser;
}

static void _plugin_info_free(agent_plugin_info_t *pi)
{
    Py_XDECREF(pi->exchange);
    Py_XDECREF(pi->parser);
    Py_XDECREF(pi->get_request);
    Py_XDECREF(pi->put_response);
    Py_XDECREF(pi->parse_request);
}


static void *_plugin_exchange_thread(void *arg)
{
    agent_plugin_info_t *pi = arg;
    PyGILState_STATE gstate;
    PyObject *req;
    PyObject *resp;

    pthread_mutex_lock(&_plugins_lock);

    if (_plugins_running == 0)
    {
        pthread_mutex_unlock(&_plugins_lock);
        return NULL;
    }

    pthread_mutex_unlock(&_plugins_lock);

    /* Acquire GIL */
    gstate = PyGILState_Ensure();

    PyGILState_Release(gstate);

    for(;;)
    {
        /* check for shut down */

        gstate = PyGILState_Ensure();

        if (_plugins_die)
        {
            break;
        }

        req = PyObject_CallFunctionObjArgs(pi->get_request, NULL);

        if ((req == NULL) || (req == Py_None))
        {
            if (PyErr_Occurred())
            {
                agent_log_python_error("Error receiving request");
            }

            Py_XDECREF(req);
            PyGILState_Release(gstate);
            sleep(1);
            continue;
        }

        resp = PyObject_CallFunctionObjArgs(pi->parse_request, req, NULL);
        if (resp == NULL)
        {
            agent_log_python_error("Error parsing request");

            Py_DECREF(req);
            PyGILState_Release(gstate);
            continue;
        }

        PyObject_CallFunctionObjArgs(pi->put_response, req, resp, NULL);
        if (PyErr_Occurred())
        {
            agent_log_python_error("Error putting response");
        }

        Py_DECREF(req);
        Py_DECREF(resp);

        PyGILState_Release(gstate);
    }

    PyGILState_Release(gstate);

    return NULL;
}

static int _exchange_plugin_check(agent_plugin_info_t *pi)
{
    PyObject *cls = pi->exchange;

    pi->get_request = PyObject_GetAttrString(cls, "get_request");
    if (pi->get_request == NULL)
    {
        PyErr_Format(PyExc_AttributeError, "%s", "An 'exchange' plugin needs to define a 'get_request' method");
        return -1;
    }

    pi->put_response = PyObject_GetAttrString(cls, "put_response");
    if (pi->put_response == NULL)
    {
        PyErr_Format(PyExc_AttributeError, "%s", "An 'exchange' plugin needs to define a 'put_response' method");

        Py_DECREF(pi->get_request);
        pi->get_request= NULL;

        return -1;
    }

    return 0;
}

static int _parser_plugin_check(agent_plugin_info_t *pi)
{
    PyObject *cls = pi->parser;

    pi->parse_request = PyObject_GetAttrString(cls, "parse_request");
    if (pi->parse_request == NULL)
    {
        PyErr_Format(PyExc_AttributeError, "A 'parser' plugin needs to define a 'parse_request' method");
        return -1;
    }

    return 0;
}

int LIBAGENT_PUBLIC_API agent_plugin_register(PyObject *exchange, PyObject *parser)
{
    agent_plugin_info_t pi;

    _plugin_info_init(&pi, exchange, parser);

    if (_exchange_plugin_check(&pi) < 0)
    {
        _plugin_info_free(&pi);
        return -1;
    }

    if (_parser_plugin_check(&pi) < 0)
    {
        _plugin_info_free(&pi);
        return -1;
    }

    pthread_mutex_lock(&_plugins_lock);

    void *vptr = realloc(_plugins,
            sizeof(agent_plugin_info_t) * (_num_plugins + 1));

    if (vptr == NULL)
    {
        pthread_mutex_unlock(&_plugins_lock);
        _plugin_info_free(&pi);

        PyErr_Format(PyExc_SystemError, "Out of memory");

        return -1;
    }

    _plugins = vptr;

    memcpy(&(_plugins[_num_plugins]), &pi, sizeof(pi));
    _num_plugins++;

    pthread_mutex_unlock(&_plugins_lock);

    return 0;
}

int LIBAGENT_PUBLIC_API agent_plugin_init(void)
{
    pthread_mutex_init(&_plugins_lock, NULL);

    return 0;
}

void LIBAGENT_PUBLIC_API agent_plugin_deinit(void)
{
    int i;

    for(i = 0;i < _num_plugins;i++)
    {
        _plugin_info_free(&(_plugins[i]));
    }

    free(_plugins);
    _plugins = NULL;
    _num_plugins = 0;

    pthread_mutex_destroy(&_plugins_lock);
}

int LIBAGENT_PUBLIC_API agent_plugin_run_threads(void)
{
    int i;
    int err;
    int num_started = 0;

    pthread_mutex_lock(&_plugins_lock);

    for(i = 0;i < _num_plugins;i++)
    {
        err = pthread_create(&(_plugins[i].thr_id), NULL,
                _plugin_exchange_thread, &(_plugins[i]));
        if (err != 0)
        {   
            int ii;

            agent_error("Error creating thread: %d", err);

            /* 
             * Leaving 'running' at 0 will cause threads to die
             * when we unlock
             */

            pthread_mutex_unlock(&_plugins_lock);

            for(ii = i;ii >= 0;ii--)
            {
                pthread_join(_plugins[i].thr_id, NULL);
            }

            return err > 0 ? -err : err;
        }

        num_started++;
    }

    if (num_started == 0)
    {
        pthread_mutex_unlock(&_plugins_lock);
        agent_debug("no exchange plugins found to run");
        return -1;
    }

    _plugins_running = 1;

    pthread_mutex_unlock(&_plugins_lock);

    return 0;
}

int LIBAGENT_PUBLIC_API agent_plugin_stop_threads(void)
{
    int i;

    pthread_mutex_lock(&_plugins_lock);

    _plugins_die = 1;

    for(i = 0;i < _num_plugins;i++)
    {
        pthread_join(_plugins[i].thr_id, NULL);
    }

    pthread_mutex_unlock(&_plugins_lock);

    return 0;
}

