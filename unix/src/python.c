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
#include <fcntl.h>
#include <sys/types.h>
#include <string.h>
#include <errno.h>
#include "nova-agent_int.h"
#include "libagent_int.h"


struct _agent_python_info
{
    PyThreadState *main_thread_state;
    PyObject *main_dict;
};


static PyObject *_agent_python_get_code(const char *filename)
{
    int fd;
    int err;
    char *python_code;
    struct stat sb;
    PyObject *code_obj;

    fd = open(filename, O_RDONLY);
    if (fd < 0)
    {
        agent_error("Couldn't open '%s'\n", filename);
        return NULL;
    }

    err = fstat(fd, &sb);
    if (err < 0)
    {
        agent_error("Couldn't fstat '%s'\n", filename);
        close(fd);
        return NULL;
    }

    python_code = malloc(sb.st_size + 1);
    if (python_code == NULL)
    {
        agent_error("Out of memory allocating space for '%s'\n", filename);
        close(fd);
        return NULL;
    }

    err = read(fd, python_code, sb.st_size);
    if (err != sb.st_size)
    {
        agent_error("Error reading from '%s'\n", filename);
        close(fd);
        free(python_code);
        return NULL;
    }

    close(fd);

    /* Terminate the data we read */
    python_code[sb.st_size] = '\0';

    code_obj = Py_CompileString(python_code, filename, Py_file_input);

    free(python_code);

    return code_obj;
}

/* Assumes GIL is acquired */
static PyObject *_agent_python_run_file(const char *filename, PyObject *dict)
{
    PyObject *code_obj;
    PyObject *result;

    code_obj = _agent_python_get_code(filename);
    if (code_obj == NULL)
    {
        if (PyErr_Occurred())
        {
            agent_log_python_error("Failed to compile python code");
        }
        return NULL;
    }

    result = PyEval_EvalCode((PyCodeObject *)code_obj, dict, dict);

    /* Don't with the code object */
    Py_DECREF(code_obj);

    if (PyErr_Occurred() != NULL)
    { 
        PyObject *ptype = NULL;
        PyObject *pvalue = NULL;
        PyObject *ptraceback = NULL;

        PyErr_Fetch(&ptype, &pvalue, &ptraceback);

        if (!PyErr_GivenExceptionMatches(ptype, PyExc_SystemExit))
        { 
            PyErr_Restore(ptype, pvalue, ptraceback);

            agent_log_python_error("Failed to run python code");
        }
        else
        {
            Py_XDECREF(ptype);
            Py_XDECREF(pvalue);
            Py_XDECREF(ptraceback);

            Py_RETURN_NONE;
        }
    }

    return result;
}

#if 0
static PyObject *_agent_python_load_module(const char *filename, const char *mod_name)
{
    PyObject *code_obj;
    PyObject *result;

    code_obj = _agent_python_get_code(filename);
    if (code_obj == NULL)
    {
        return NULL;
    }

    result = PyImport_ExecCodeModule((char *)mod_name, code_obj);

    Py_DECREF(code_obj);

    if (PyErr_Occurred() != NULL)
    { 
        PyObject *ptype = NULL;
        PyObject *pvalue = NULL;
        PyObject *traceback = NULL;

        PyErr_Print();
        PyErr_Fetch(&ptype, &pvalue, &traceback);

        if (!PyErr_GivenExceptionMatches(ptype, PyExc_SystemExit))
        { 
            agent_error("Failed to run Python code");

            PyErr_Clear();

            Py_XDECREF(result);
            result = NULL;
        }

        if (ptype != NULL)
        {
            Py_DECREF(ptype);
        }

        if (pvalue != NULL)
        {
            Py_DECREF(pvalue);
        }

        if (traceback != NULL)
        {
            Py_DECREF(traceback);
        }
    }

    return result;
}
#endif

agent_python_info_t *agent_python_init(int argc, char * const *argv, int syspython)
{
    agent_python_info_t *pi;
    PyObject *main_module;

    if (!syspython)
        Py_SetPythonHome(DATA_DIR);

    Py_Initialize();

    if (!syspython)
        PyRun_SimpleString("import sys; sys.path.append('" DATA_DIR "')\n");

    PyEval_InitThreads();

    main_module = PyImport_AddModule("__main__");
    if (main_module == NULL)
    {
        Py_Finalize();
        return NULL;
    }

    /* Note: main_module is a borrowed reference, so we won't need to
     * DECREF it
     */
    
    pi = calloc(1, sizeof(agent_python_info_t));
    if (pi == NULL)
    {
        Py_Finalize();
        return NULL;
    }

    pi->main_dict = PyModule_GetDict(main_module);

    PySys_SetArgv(argc, (char **)argv);

    /* Swap out and return current thread state and release the GIL */
    pi->main_thread_state = PyEval_SaveThread();

    return pi;
}

void agent_python_deinit(agent_python_info_t *pi)
{
    if (pi->main_thread_state != NULL)
    {
        /* Acquire the GIL before shutting down */
        PyEval_RestoreThread(pi->main_thread_state);
    }

    Py_Finalize();
    free(pi);
}

int agent_python_run_file(agent_python_info_t *pi, const char *filename)
{
    PyGILState_STATE gstate;
    PyObject *result;
    int err;

    /* Acquire GIL */
    gstate = PyGILState_Ensure();

    result = _agent_python_run_file(filename, pi->main_dict);

    if (result == NULL)
        err = -1;
    else
        err = 0;

    Py_XDECREF(result);

    /* Release GIL */
    PyGILState_Release(gstate); 

    return err;
}

int agent_python_test_mode(agent_python_info_t *pi)
{
    PyGILState_STATE gstate;
    PyObject *obj;
    int ret;

    /* Acquire GIL */
    gstate = PyGILState_Ensure();

    obj = PyDict_GetItemString(pi->main_dict, "test_mode");
    if (obj == NULL)
    {
        /* Release GIL */
        PyGILState_Release(gstate); 
        return 0;
    }

    if (PyInt_Check(obj))
    {
        ret = (PyInt_AsLong(obj) != 0) ? 1 : 0;
        /* Release GIL */
        PyGILState_Release(gstate); 
        return ret;
    }

    if (PyBool_Check(obj))
    {
        ret = (obj == Py_True) ? 1 : 0;
        /* Release GIL */
        PyGILState_Release(gstate); 
        return ret;
    }

    PyErr_Format(PyExc_TypeError, "If test_mode is set, it should be an int or bool");

    /* Release GIL */
    PyGILState_Release(gstate); 

    return -1;
}

int agent_python_start_interpreter(agent_python_info_t *pi)
{
    PyGILState_STATE gstate;
    int err;

    /* Acquire GIL */
    gstate = PyGILState_Ensure();

    err = PyRun_InteractiveLoop(stdin, "<stdin>");

    /* Release GIL */
    PyGILState_Release(gstate); 

    return err;
}
