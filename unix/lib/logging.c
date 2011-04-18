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

#include "libagent_int.h"


static PyObject *logging = NULL;


#define VSMPRINTF(p, fmt) \
    va_list ap;	\
    int n, size = 100;	\
    p = malloc(size);	\
    if (!p)	\
    {		\
        fprintf(stderr, "couldn't allocate %d bytes for buffer\n", size);	\
        return;	\
    }		\
    while (1)	\
    {		\
        va_start(ap, fmt);	\
        n = vsnprintf(p, size, fmt, ap);	\
        va_end(ap);		\
        if (n > -1 && n < size)	\
            break;		\
        if (n > -1)		\
            size = n + 1;	\
        else			\
            size *= 2;		\
        char *np = realloc(p, size);	\
        if (!np)		\
        {			\
            free(p);		\
            fprintf(stderr, "couldn't allocate %d bytes for buffer\n", size);	\
            return;		\
        }			\
        p = np;			\
    }


static int basic_config(char *filename, char *level)
{
    PyObject *args = PyTuple_New(0);
    if (!args)
        goto err_args;

    PyObject *kwargs = PyDict_New();
    if (!args)
        goto err_kwargs;

    /*
     * "-" means stdout, so don't set filename in the dictionary
     * in this case
     */
    if (filename && strcmp(filename, "-"))
    {
        PyObject *value = PyString_FromString(filename);
        if (!value)
            goto err_value;

        int ret = PyDict_SetItemString(kwargs, "filename", value);
        Py_DECREF(value);
        if (ret < 0)
            goto err_value;
    }

    if (level)
    {
        char *buf = strdup(level);
        if (!buf)
        {
            PyErr_NoMemory();
            goto err_value;
        }

        char *p;
        for (p = buf; *p; p++)
            *p = toupper(*p);

        PyObject *value = PyObject_GetAttrString(logging, buf);
        free(buf);
        if (!value)
            goto err_value;

        if (!PyInt_Check(value))
        {
            Py_DECREF(value);
            PyErr_Format(PyExc_ValueError, "logging level must resolve to integer");
            goto err_value;
        }

        int ret = PyDict_SetItemString(kwargs, "level", value);
        Py_DECREF(value);
        if (ret < 0)
            goto err_value;
    }

    PyObject *value = PyString_FromString("%(asctime)s [%(levelname)s] %(message)s");
    PyDict_SetItemString(kwargs, "format", value);
    Py_DECREF(value);

    PyObject *callable = PyObject_GetAttrString(logging, "basicConfig");
    if (!callable)
        goto err_callable;

    PyObject *ret = PyObject_Call(callable, args, kwargs);
    Py_DECREF(callable);
    Py_DECREF(args);
    Py_DECREF(kwargs);

    int retcode = -1;
    if (ret)
    {
        retcode = 0;
        Py_DECREF(ret);
    }

    return retcode;

err_callable:
err_value:
    Py_DECREF(kwargs);

err_kwargs:
    Py_DECREF(args);

err_args:
    return -1;
}

static void _log(char *level, char *p)
{
    PyObject *ret = NULL;
    if (logging)
    {
        PyGILState_STATE gstate = PyGILState_Ensure();

        ret = PyObject_CallMethod(logging, level, "s", p);
        Py_XDECREF(ret);

        if (!ret)
        {
            PyErr_Print();
            PyErr_Clear();
        }

        PyGILState_Release(gstate);
    }

    if (!ret)
        fprintf(stderr, "%s\n", p);
}

int LIBAGENT_PUBLIC_API agent_open_log(char *filename, char *level)
{
    PyGILState_STATE gstate = PyGILState_Ensure();

    logging = PyImport_ImportModule("logging");
    if (!logging)
    {
        fprintf(stderr, "unable to import logging module\n");
        goto err;
    }

    if (filename || level)
    {
        int ret = basic_config(filename, level);
        if (ret < 0)
        {
            fprintf(stderr, "could not setup basic config\n");
            goto err;
        }
    }

    PyGILState_Release(gstate);

    return 0;

err:
    Py_CLEAR(logging);

    PyErr_Print();
    PyErr_Clear();

    PyGILState_Release(gstate);

    return -1;
}

/*
 * The logging calls below should be exported to modules
 */

int LIBAGENT_PUBLIC_API agent_log_python_error(char *log_prefix)
{
    PyObject *ptype;
    PyObject *pvalue;
    PyObject *ptraceback;

    /* Acquire GIL */
    PyGILState_STATE gstate = PyGILState_Ensure();

    PyErr_Fetch(&ptype, &pvalue, &ptraceback);

    if (ptype == NULL)
    {
        agent_error("%s: No python error available", log_prefix);

        /* Just in case */
        Py_XDECREF(pvalue);
        Py_XDECREF(ptraceback);

        /* Release GIL */
        PyGILState_Release(gstate); 
        return -1;
    }

    if (ptraceback == NULL)
    {
        PyObject *obj;

        agent_error("%s: A python exception has occurred:", log_prefix);

        if (pvalue != NULL)
        {
            obj = PyObject_Str(pvalue);
        }
        else
        {
            obj = PyObject_Str(ptype);
        }

        agent_error("[EXC] %s", PyString_AsString(obj));

        Py_DECREF(obj);
        Py_DECREF(ptype);
        Py_XDECREF(pvalue);

        /* Release GIL */
        PyGILState_Release(gstate); 
        return 0;
    }

    PyObject *tb_mod = PyImport_AddModule("traceback");
    if (tb_mod == NULL)
    {
        PyErr_Clear();

        Py_DECREF(ptype);
        Py_XDECREF(pvalue);
        Py_XDECREF(ptraceback);

        agent_error("%s: [Couldn't find traceback module "
                "to print the error]", log_prefix);

        /* Release GIL */
        PyGILState_Release(gstate); 
        return -1;
    }

    /*
     * Call traceback.format_exception(ptype, pvalue, ptraceback)
     */

    PyObject *pobj_list = PyObject_CallMethod(tb_mod, "format_exception",
            "OOO", ptype, pvalue, ptraceback);
    if (pobj_list == NULL)
    {
        PyErr_Clear();

        Py_DECREF(ptype);
        Py_XDECREF(pvalue);
        Py_XDECREF(ptraceback);

        agent_error("%s: [Couldn't format traceback]", log_prefix);

        /* Release GIL */
        PyGILState_Release(gstate); 
        return -1;
    }

    Py_DECREF(ptype);
    Py_XDECREF(pvalue);
    Py_XDECREF(ptraceback);

    /*
     * Now we have a list of 'lines'.  Each 'line' might actually be
     * multiple lines, however ('line' might contain '\n's).  So, we
     * need to go through every list entry and log each real line
     * (looking for \n separator)
     */

    agent_error("%s: A python exception has occurred:", log_prefix);

    Py_ssize_t list_sz = PyList_Size(pobj_list);
    PyObject *pobj_str;

    Py_ssize_t i;

    for(i = 0;i < list_sz;i++)
    {
        pobj_str = PyList_GetItem(pobj_list, i);

        char *obj_str = strdup(PyString_AsString(pobj_str));

        Py_DECREF(pobj_str);
    
        if (obj_str == NULL)
        {
            agent_error("Out of memory");

            Py_DECREF(pobj_list);
    
            /* Release GIL */
            PyGILState_Release(gstate); 
            return 0;
        }
    
        char *ptr = strchr(obj_str, '\n');
        if (ptr == NULL)
        {
            /* No \n... just log this element and go to the next */
            agent_error("[EXC] %s", obj_str);
            free(obj_str);

            continue;
        }

        char *start = obj_str;
        *(ptr++) = '\0';

        agent_error("[EXC] %s", start);
    
        while((ptr != NULL) && (*ptr != '\0'))
        {
            start = ptr;
            ptr = strchr(start, '\n');
            if (ptr != NULL)
            {
                *ptr++ = '\0';
            }

            agent_error("[EXC] %s", start);
        }
    
        free(obj_str);
    }

    /* Release GIL */
    PyGILState_Release(gstate); 

    return 0;
}

void LIBAGENT_PUBLIC_API agent_debug(char *fmt, ...)
{
    char *p;
    VSMPRINTF(p, fmt);
    _log("debug", p);
    free(p);
}


void LIBAGENT_PUBLIC_API agent_error(char *fmt, ...)
{
    char *p;
    VSMPRINTF(p, fmt);
    _log("error", p);
    free(p);
}

void LIBAGENT_PUBLIC_API agent_info(char *fmt, ...)
{
    char *p;
    VSMPRINTF(p, fmt);
    _log("info", p);
    free(p);
}

void LIBAGENT_PUBLIC_API agent_warn(char *fmt, ...)
{
    char *p;
    VSMPRINTF(p, fmt);
    _log("warn", p);
    free(p);
}

