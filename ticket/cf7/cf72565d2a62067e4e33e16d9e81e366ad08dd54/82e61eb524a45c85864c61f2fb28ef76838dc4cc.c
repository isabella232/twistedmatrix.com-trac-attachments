/*
 * A Deferred implementation in C. Cover most of the Deferred API but try
 * to be faster.
 *
 */

#include <Python.h>
#include "structmember.h"

/* Py_VISIT and Py_CLEAR are defined here to be compatible with Python 2.3 */

#ifndef Py_VISIT
#define Py_VISIT(op) \
    do { \
        if (op) { \
            int vret = visit((PyObject *)(op), arg); \
            if (vret) \
                return vret; \
        } \
    } while (0)
#endif

#ifndef Py_CLEAR
#define Py_CLEAR(op) \
    do { \
        if (op) { \
            PyObject *tmp = (PyObject *)(op); \
            (op) = NULL; \
            Py_DECREF(tmp); \
        } \
    } while (0)
#endif

PyObject * failure_class;
PyObject * already_called;

typedef struct {
    PyObject_HEAD
    PyObject *result;
    int paused;
    PyObject *callbacks;
    int called;
} cdefer_Deferred;

/* Prototypes */

static PyObject * cdefer_Deferred_new(PyTypeObject *type, PyObject *args,
        PyObject *kwargs);

static void cdefer_Deferred_dealloc(PyObject *o);

static int cdefer_Deferred_traverse(PyObject *o, visitproc visit, void *arg);

static int cdefer_Deferred_clear(PyObject *o);

static int cdefer_Deferred_clear(PyObject *o);

static int cdefer_Deferred___init__(cdefer_Deferred *self, PyObject *args,
        PyObject *kwargs);

static PyObject *cdefer_Deferred__addCallbacks(cdefer_Deferred *self,
        PyObject *callback, PyObject *errback, PyObject *callbackArgs,
        PyObject *callbackKeywords, PyObject *errbackArgs,
        PyObject *errbackKeywords);

static PyObject *cdefer_Deferred_addCallback(cdefer_Deferred *self,
        PyObject *args, PyObject *kwargs);

static PyObject *cdefer_Deferred_addErrback(cdefer_Deferred *self,
        PyObject *args, PyObject *kwargs);

static PyObject *cdefer_Deferred_addBoth(cdefer_Deferred *self, PyObject *args,
        PyObject *kwargs);

static PyObject *cdefer_Deferred_pause(cdefer_Deferred *self, PyObject *args);

static PyObject *cdefer_Deferred_unpause(cdefer_Deferred *self,
        PyObject *args);

static PyObject *cdefer_Deferred_chainDeferred(cdefer_Deferred *self,
        PyObject *args, PyObject *kwargs);

static PyObject *cdefer_Deferred__runCallbacks(cdefer_Deferred *self);

static PyObject *cdefer_Deferred__startRunCallbacks(cdefer_Deferred *self,
        PyObject *result);

static PyObject *cdefer_Deferred_callback(cdefer_Deferred *self, PyObject *args,
        PyObject *kwargs);

static PyObject *cdefer_Deferred_errback(cdefer_Deferred *self, PyObject *args,
        PyObject *kwargs);

static PyObject *cdefer_Deferred__continue(cdefer_Deferred *self,
        PyObject *args, PyObject *kwargs);

static PyTypeObject cdefer_DeferredType;

static PyObject * cdefer_Deferred_new(PyTypeObject *type, PyObject *args,
        PyObject *kwargs) {
    cdefer_Deferred *self;
    self = (cdefer_Deferred *)type->tp_alloc(type, 0);
    return (PyObject *)self;
}

static void cdefer_Deferred_dealloc(PyObject *o) {
    cdefer_Deferred *self;
    self = (cdefer_Deferred *)o;
    PyObject_GC_UnTrack(self);
    Py_XDECREF(self->result);
    Py_XDECREF(self->callbacks);
    (*o->ob_type->tp_free)(o);
}

static int cdefer_Deferred_traverse(PyObject *o, visitproc visit, void *arg) {
    cdefer_Deferred *self;
    self = (cdefer_Deferred *)o;
    Py_VISIT(self->result);
    Py_VISIT(self->callbacks);
    return 0;
}

static int cdefer_Deferred_clear(PyObject *o) {
    cdefer_Deferred *self;
    self = (cdefer_Deferred *)o;
    Py_CLEAR(self->result);
    Py_CLEAR(self->callbacks);
    return 0;
}

static int cdefer_Deferred___init__(cdefer_Deferred *self, PyObject *args,
        PyObject *kwargs) {
    static char *argnames[] = {NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "", argnames)) {
        return -1;
    }
    self->paused = 0;
    self->callbacks = PyList_New(0);
    if (!self->callbacks) {
        return -1;
    }
    return 0;
}

static PyObject *cdefer_Deferred__addCallbacks(cdefer_Deferred *self,
        PyObject *callback, PyObject *errback, PyObject *callbackArgs,
        PyObject *callbackKeywords, PyObject *errbackArgs,
        PyObject *errbackKeywords) {
    PyObject *result;
    PyObject *cbs = 0;

    if (callback != Py_None) {
        if (!PyCallable_Check(callback)) {
            PyErr_SetNone(PyExc_AssertionError);
            return NULL;
        }
    }
    if (errback != Py_None) {
        if (!PyCallable_Check(errback)) {
            PyErr_SetNone(PyExc_AssertionError);
            return NULL;
        }
    }

    Py_INCREF(callback);
    Py_INCREF(callbackArgs);
    Py_INCREF(callbackKeywords);
    Py_INCREF(errback);
    Py_INCREF(errbackArgs);
    Py_INCREF(errbackKeywords);

    cbs = Py_BuildValue("(OOOOOO)", callback, callbackArgs, callbackKeywords,
                                    errback, errbackArgs, errbackKeywords);
    if (!cbs) {
        return NULL;
    }

    if (PyList_Append(self->callbacks, cbs) == -1) {
        return NULL;
    }
    Py_CLEAR(cbs);

    Py_DECREF(callback);
    Py_DECREF(callbackArgs);
    Py_DECREF(callbackKeywords);
    Py_DECREF(errback);
    Py_DECREF(errbackArgs);
    Py_DECREF(errbackKeywords);

    if (self->called) {
        if (cdefer_Deferred__runCallbacks(self) == NULL) {
            return NULL;
        }
    }

    result = (PyObject *)self;
    Py_INCREF(result);
    return result;
}

static char cdefer_Deferred_addCallbacks_doc[] = "Add a pair of callbacks (success and error) to this Deferred.\n\nThese will be executed when the \'master\' callback is run.";

static PyObject *cdefer_Deferred_addCallbacks(cdefer_Deferred *self,
        PyObject *args, PyObject *kwargs) {
    PyObject *callback;
    PyObject *errback;
    PyObject *callbackArgs;
    PyObject *callbackKeywords;
    PyObject *errbackArgs;
    PyObject *errbackKeywords;
    PyObject *result;
    errback = Py_None;
    callbackArgs = Py_None;
    callbackKeywords = Py_None;
    errbackArgs = Py_None;
    errbackKeywords = Py_None;
    static char *argnames[] = {"callback", "errback", "callbackArgs",
        "callbackKeywords", "errbackArgs", "errbackKeywords", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O|OOOOO", argnames,
                &callback, &errback, &callbackArgs,
                &callbackKeywords, &errbackArgs, &errbackKeywords)) {
        return NULL;
    }
    result = cdefer_Deferred__addCallbacks(self, callback, errback,
        callbackArgs, callbackKeywords, errbackArgs, errbackKeywords);
    return result;
}

static char cdefer_Deferred_addCallback_doc[] = "Convenience method for adding just a callback.\n\nSee L{addCallbacks}.";

static PyObject *cdefer_Deferred_addCallback(cdefer_Deferred *self,
        PyObject *args, PyObject *kwargs) {
    PyObject *callback;
    PyObject *callbackArgs;
    PyObject *callbackKeywords;
    PyObject *result;
    if (PyTuple_Size(args) > 0) {
        callback = PyTuple_GET_ITEM(args, 0);
        if (!callback) {
            return NULL;
        }
        callbackArgs = PyTuple_GetSlice(args, 1, PyTuple_Size(args));
        if (!callbackArgs) {
            return NULL;
        }
    } else {
        callback = PyDict_GetItemString(kwargs, "callback");
        if (!callback) {
            return NULL;
        }
        callbackArgs = Py_None;
        if (PyDict_DelItemString(kwargs, "callback") == -1) {
            return NULL;
        }
    }
    callbackKeywords = kwargs;
    if (!callbackKeywords) {
        callbackKeywords = Py_None;
    }
    result = cdefer_Deferred__addCallbacks(self, callback, Py_None, callbackArgs,
        callbackKeywords, Py_None, Py_None);
    Py_DECREF(callbackArgs);
    return result;
}

static char cdefer_Deferred_addErrback_doc[] = "Convenience method for adding just an errback.\n\nSee L{addCallbacks}.";

static PyObject *cdefer_Deferred_addErrback(cdefer_Deferred *self,
        PyObject *args, PyObject *kwargs) {
    PyObject *errback;
    PyObject *errbackArgs;
    PyObject *errbackKeywords;
    PyObject *result;
    if (PyTuple_Size(args) > 0) {
        errback = PyTuple_GET_ITEM(args, 0);
        if (!errback) {
            return NULL;
        }
        errbackArgs = PyTuple_GetSlice(args, 1, PyTuple_Size(args));
        if (!errbackArgs) {
            return NULL;
        }
    } else {
        errback = PyDict_GetItemString(kwargs, "errback");
        if (!errback) {
            return errback;
        }
        errbackArgs = Py_None;
        if (PyDict_DelItemString(kwargs, "errback") == -1) {
            return NULL;
        }
    }
    errbackKeywords = kwargs;
    if (!errbackKeywords) {
        errbackKeywords = Py_None;
    }
    result = cdefer_Deferred__addCallbacks(self, Py_None, errback, Py_None,
        Py_None, errbackArgs, errbackKeywords);
    Py_DECREF(errbackArgs);
    return result;
}

static char cdefer_Deferred_addBoth_doc[] = "Convenience method for adding a single callable as both a callback\nand an errback.\n\nSee L{addCallbacks}.";

static PyObject *cdefer_Deferred_addBoth(cdefer_Deferred *self, PyObject *args,
        PyObject *kwargs) {
    PyObject *callback;
    PyObject *callbackArgs;
    PyObject *callbackKeywords;
    PyObject *result;
    if (PyTuple_Size(args) > 0) {
        callback = PyTuple_GET_ITEM(args, 0);
        if (!callback) {
            return NULL;
        }
        callbackArgs = PyTuple_GetSlice(args, 1, PyTuple_Size(args));
        if (!callbackArgs) {
            return NULL;
        }
    } else {
        callback = PyDict_GetItemString(kwargs, "callback");
        if (!callback) {
            return NULL;
        }
        callbackArgs = Py_None;
        if (PyDict_DelItemString(kwargs, "callback") == -1) {
            return NULL;
        }
    }
    callbackKeywords = kwargs;
    if (!callbackKeywords) {
        callbackKeywords = Py_None;
    }
    result = cdefer_Deferred__addCallbacks(self, callback, callback,
        callbackArgs, callbackKeywords, callbackArgs, callbackKeywords);
    Py_DECREF(callbackArgs);
    return result;
}

static char cdefer_Deferred_pause_doc[] = "Stop processing on a Deferred until L{unpause}() is called.";

static PyObject *cdefer_Deferred_pause(cdefer_Deferred *self, PyObject *args) {
    PyObject *result;
    self->paused++;
    result = Py_None;
    Py_INCREF(Py_None);
    return result;
}

static char cdefer_Deferred_unpause_doc[] = "Process all callbacks made since L{pause}() was called.";

static PyObject *cdefer_Deferred_unpause(cdefer_Deferred *self,
        PyObject *args) {
    self->paused--;
    if (!self->paused && self->called) {
        return cdefer_Deferred__runCallbacks(self);
    }
    Py_INCREF(Py_None);
    return Py_None;
}

static char cdefer_Deferred_chainDeferred_doc[] = "Chain another Deferred to this Deferred.\n\nThis method adds callbacks to this Deferred to call d\'s callback or\nerrback, as appropriate.";

static PyObject *cdefer_Deferred_chainDeferred(cdefer_Deferred *self,
        PyObject *args, PyObject *kwargs) {
    PyObject *d;
    PyObject *callback;
    PyObject *errback;
    PyObject *result;
    static char *argnames[] = {"d", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O", argnames, &d)) {
        return NULL;
    }
    callback = PyObject_GetAttrString(d, "callback");
    if (!callback) {
        return NULL;
    }
    errback = PyObject_GetAttrString(d, "errback");
    if (!errback) {
        return NULL;
    }
    result = cdefer_Deferred__addCallbacks(self, callback, errback, Py_None,
        Py_None, Py_None, Py_None);
    Py_DECREF(callback);
    Py_DECREF(errback);
    return result;
}

static PyObject *cdefer_Deferred__runCallbacks(cdefer_Deferred *self) {
    PyObject *cb;
    PyObject *item;
    PyObject *callback;
    PyObject *args;
    PyObject *newArgs;
    PyObject *newArgs2;
    PyObject *kwargs;
    PyObject *_continue;
    PyObject *type, *value, *traceback, *failArgs;
    PyObject *tmp;
    int i;
    int size;
    int offset;

    if (!self->paused) {
        cb = self->callbacks;
        size = PyList_GET_SIZE(cb);
        if (size == -1) {
            return NULL;
        }
        for (i = 0; i < size; i++) {
            item = PyList_GET_ITEM(cb, i);
            if (!item) {
                return NULL;
            }

            offset = 0;
            if (PyObject_IsInstance(self->result, failure_class)) {
                offset = 3;
            }

            callback = PyTuple_GET_ITEM(item, offset + 0);
            if (!callback) {
                return NULL;
            }
            if (callback == Py_None) {
                continue;
            }

            args = PyTuple_GET_ITEM(item, offset + 1);
            if (!args) {
                return NULL;
            }

            kwargs = PyTuple_GET_ITEM(item, offset + 2);
            if (!kwargs) {
                return NULL;
            }

            newArgs = Py_BuildValue("(O)", self->result);
            if (!newArgs) {
                return NULL;
            }

            if (args != Py_None) {
                newArgs2 = PySequence_InPlaceConcat(newArgs, args);
                if (!newArgs2) {
                    return NULL;
                }
            } else {
                newArgs2 = newArgs;
            }

            if (kwargs == Py_None) {
                tmp = PyObject_Call(callback, newArgs2, NULL);
            } else {
                tmp = PyObject_Call(callback, newArgs2, kwargs);
            }
            Py_DECREF(self->result);
            self->result = tmp;

            Py_CLEAR(newArgs2);
            Py_CLEAR(newArgs);

            if (!self->result) {
                PyErr_Fetch(&type, &value, &traceback);
                PyErr_NormalizeException(&type, &value, &traceback);
                if (!value) {
                    value = Py_None;
                    Py_INCREF(value);
                }
                if (!traceback) {
                    traceback = Py_None;
                    Py_INCREF(traceback);
                }

                failArgs = Py_BuildValue("(OOO)", value, type, traceback);
                if (!failArgs) {
                    PyErr_Restore(type, value, traceback);
                    return NULL;
                }
                self->result = PyObject_CallObject(failure_class, failArgs);
                Py_INCREF(self->result);
                continue;
            }
            Py_INCREF(self->result);
            if (PyObject_TypeCheck(self->result, &cdefer_DeferredType)) {
                if (PyList_SetSlice(cb, 0, i+1, NULL) == -1) {
                    return NULL;
                }
                if (!PyObject_CallMethod((PyObject *)self, "pause", NULL)) {
                    return NULL;
                }
                _continue = PyObject_GetAttrString((PyObject *)self,
                                                   "_continue");
                if (!_continue) {
                    return NULL;
                }
                if (!cdefer_Deferred__addCallbacks(
                            (cdefer_Deferred *)self->result, _continue,
                            _continue, Py_None, Py_None, Py_None, Py_None)) {
                    return NULL;
                }
                goto endLabel;
            }
        }
        if (PyList_SetSlice(cb, 0, PyList_GET_SIZE(cb), NULL) == -1) {
            return NULL;
        }
    }
endLabel:;
    if (PyObject_IsInstance(self->result, failure_class)) {
        if (!PyObject_CallMethod((PyObject *)self->result,
                                 "cleanFailure", NULL)) {
            return NULL;
        }
    }
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *cdefer_Deferred__startRunCallbacks(cdefer_Deferred *self,
        PyObject *result) {
    if (self->called) {
        PyErr_SetNone(already_called);
        return NULL;
    }
    self->called = 1;
    Py_XDECREF(self->result);
    self->result = result;
    Py_INCREF(self->result);
    return cdefer_Deferred__runCallbacks(self);
}

static char cdefer_Deferred_callback_doc[] = "Run all success callbacks that have been added to this Deferred.\n\nEach callback will have its result passed as the first\nargument to the next; this way, the callbacks act as a\n\'processing chain\'. Also, if the success-callback returns a Failure\nor raises an Exception, processing will continue on the *error*-\ncallback chain.";

static PyObject *cdefer_Deferred_callback(cdefer_Deferred *self, PyObject *args,
        PyObject *kwargs) {
    PyObject *result;
    static char *argnames[] = {"result", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O", argnames, &result)) {
        return NULL;
    }
    return cdefer_Deferred__startRunCallbacks(self, result);
}

static char cdefer_Deferred_errback_doc[] = "Run all error callbacks that have been added to this Deferred.\n\nEach callback will have its result passed as the first\nargument to the next; this way, the callbacks act as a\n\'processing chain\'. Also, if the error-callback returns a non-Failure\nor doesn\'t raise an Exception, processing will continue on the\n*success*-callback chain.\n\nIf the argument that\'s passed to me is not a Failure instance,\nit will be embedded in one. If no argument is passed, a Failure\ninstance will be created based on the current traceback stack.\n\nPassing a string as `fail\' is deprecated, and will be punished with\na warning message.";

static PyObject *cdefer_Deferred_errback(cdefer_Deferred *self, PyObject *args,
        PyObject *kwargs) {
    PyObject *fail;
    PyObject *tpl;
    PyObject *tmp;
    static char *argnames[] = {"fail", NULL};
    fail = Py_None;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "|O", argnames, &fail)) {
        return NULL;
    }
    if (!PyObject_IsInstance(fail, failure_class)) {
        tpl = Py_BuildValue("(O)", fail);
        if (!tpl) {
            return NULL;
        }
        Py_INCREF(fail);
        tmp = PyObject_CallObject(failure_class, tpl);
        Py_CLEAR(tpl);
        Py_DECREF(fail);
        fail = tmp;
    }
    return cdefer_Deferred__startRunCallbacks(self, fail);
}

static PyObject *cdefer_Deferred__continue(cdefer_Deferred *self,
        PyObject *args, PyObject *kwargs) {
    PyObject *result;
    static char *argnames[] = {"result", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "O", argnames, &result)) {
        return NULL;
    }
    Py_XDECREF(self->result);
    self->result = result;
    Py_INCREF(self->result);
    return PyObject_CallMethod((PyObject *)self, "unpause", NULL);
}

static struct PyMethodDef cdefer_Deferred_methods[] = {
  {"addCallbacks", (PyCFunction)cdefer_Deferred_addCallbacks,
                   METH_VARARGS|METH_KEYWORDS, cdefer_Deferred_addCallbacks_doc},
  {"addCallback", (PyCFunction)cdefer_Deferred_addCallback,
                  METH_VARARGS|METH_KEYWORDS, cdefer_Deferred_addCallback_doc},
  {"addErrback", (PyCFunction)cdefer_Deferred_addErrback,
                 METH_VARARGS|METH_KEYWORDS, cdefer_Deferred_addErrback_doc},
  {"addBoth", (PyCFunction)cdefer_Deferred_addBoth,
               METH_VARARGS|METH_KEYWORDS, cdefer_Deferred_addBoth_doc},
  {"chainDeferred", (PyCFunction)cdefer_Deferred_chainDeferred,
                    METH_VARARGS|METH_KEYWORDS, cdefer_Deferred_chainDeferred_doc},
  {"callback", (PyCFunction)cdefer_Deferred_callback,
               METH_VARARGS|METH_KEYWORDS, cdefer_Deferred_callback_doc},
  {"errback", (PyCFunction)cdefer_Deferred_errback,
              METH_VARARGS|METH_KEYWORDS, cdefer_Deferred_errback_doc},
  {"pause", (PyCFunction)cdefer_Deferred_pause,
            METH_VARARGS, cdefer_Deferred_pause_doc},
  {"unpause", (PyCFunction)cdefer_Deferred_unpause,
              METH_VARARGS, cdefer_Deferred_unpause_doc},
  {"_continue", (PyCFunction)cdefer_Deferred__continue,
                METH_VARARGS|METH_KEYWORDS, ""},
  {0, 0, 0, 0}
};

static struct PyMemberDef cdefer_Deferred_members[] = {
  {"result", T_OBJECT, offsetof(cdefer_Deferred, result), 0, 0},
  {"paused", T_INT, offsetof(cdefer_Deferred, paused), READONLY, 0},
  {"called", T_INT, offsetof(cdefer_Deferred, called), READONLY, 0},
  {"callbacks", T_OBJECT, offsetof(cdefer_Deferred, callbacks), READONLY, 0},
  {0, 0, 0, 0, 0}
};

static PyTypeObject cdefer_DeferredType = {
    PyObject_HEAD_INIT(0)
    0,                          /*ob_size*/
    "cdefer.Deferred",          /*tp_name*/
    sizeof(cdefer_Deferred),    /*tp_basicsize*/
    0,                          /*tp_itemsize*/
    (destructor)cdefer_Deferred_dealloc,    /*tp_dealloc*/
    0,                          /*tp_print*/
    0,                          /*tp_getattr*/
    0,                          /*tp_setattr*/
    0,                          /*tp_compare*/
    0,                          /*tp_repr*/
    0,                          /*tp_as_number*/
    0,                          /*tp_as_sequence*/
    0,                          /*tp_as_mapping*/
    0,                          /*tp_hash */
    0,                          /*tp_call*/
    0,                          /*tp_str*/
    0,                          /*tp_getattro*/
    0,                          /*tp_setattro*/
    0,                          /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE|Py_TPFLAGS_HAVE_GC, /*tp_flags*/
    "This is a callback which will be put off until later.\n\nWhy do we want this? Well, in cases where a function in a threaded\nprogram would block until it gets a result, for Twisted it should\nnot block. Instead, it should return a Deferred.\n\nThis can be implemented for protocols that run over the network by\nwriting an asynchronous protocol for twisted.internet. For methods\nthat come from outside packages that are not under our control, we use\nthreads (see for example L{twisted.enterprise.adbapi}).\n\nFor more information about Deferreds, see doc/howto/defer.html or\nU{http://www.twistedmatrix.com/documents/howto/defer}.", /*tp_doc*/
    (traverseproc)cdefer_Deferred_traverse,   /*tp_traverse*/
    (inquiry)cdefer_Deferred_clear,           /*tp_clear*/
    0,                          /*tp_richcompare*/
    0,                          /*tp_weaklistoffset*/
    0,                          /*tp_iter*/
    0,                          /*tp_iternext*/
    cdefer_Deferred_methods,    /*tp_methods*/
    cdefer_Deferred_members,    /*tp_members*/
    0,                          /*tp_getset*/
    0,                          /*tp_base*/
    0,                          /*tp_dict*/
    0,                          /*tp_descr_get*/
    0,                          /*tp_descr_set*/
    0,                          /*tp_dictoffset*/
    (initproc)cdefer_Deferred___init__,   /*tp_init*/
    0,                          /*tp_alloc*/
    cdefer_Deferred_new,        /*tp_new*/
    PyObject_GC_Del,            /*tp_free*/
    0,                          /*tp_is_gc*/
    0,                          /*tp_bases*/
    0,                          /*tp_mro*/
    0,                          /*tp_cache*/
    0,                          /*tp_subclasses*/
    0,                          /*tp_weaklist*/
};

static PyMethodDef cdefer_methods[] = {
    {NULL}  /* Sentinel */
};

#ifndef PyMODINIT_FUNC  /* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC initcdefer(void) {
    PyObject* m;
    PyObject* f;
    PyObject* d;

    if (PyType_Ready(&cdefer_DeferredType) < 0) {
        return;
    }

    m = Py_InitModule3("cdefer", cdefer_methods,
                       "cdefer");

    if (!m) {
        return;
    }

    Py_INCREF(&cdefer_DeferredType);
    PyModule_AddObject(m, "Deferred", (PyObject *)&cdefer_DeferredType);

    f = PyImport_ImportModule("twisted.python.failure");
    if (!f) {
        return;
    }
    failure_class = PyObject_GetAttrString(f, "Failure");
    if (!failure_class) {
        return;
    }

    d = PyImport_ImportModule("twisted.internet.defer");
    if (!d) {
        return;
    }
    already_called = PyObject_GetAttrString(d, "AlreadyCalledError");
    if (!already_called) {
        return;
    }
}

