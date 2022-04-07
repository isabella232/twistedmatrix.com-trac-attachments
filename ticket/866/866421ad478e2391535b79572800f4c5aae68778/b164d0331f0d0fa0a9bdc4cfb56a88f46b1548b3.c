/*
 *  * Copyright (c) 2001-2006 Twisted Matrix Laboratories.
 *  * See LICENSE for details.
 *
 */

#include <Python.h>
#include <sys/epoll.h>

static char epoll__doc__[] =
"Interface to epoll I/O event notification facility.\n";

/*
 * Wrapper around epoll_create
 * 
 */
static PyObject * _epoll_create(PyObject *self, PyObject *args) {
    int size;
    int kdpfd;

    if (!PyArg_ParseTuple(args, "i", &size)) {
        return NULL;
    }

    // Real call to epoll_create, I should get the epoll fd
    kdpfd = epoll_create(size);

    if (kdpfd == -1) {
        return PyErr_SetFromErrno(PyExc_IOError);
    } else {
        return Py_BuildValue("i", kdpfd);
    }
}

/*
 * Wrapper around epoll_ctl
 *
 */
static PyObject * _epoll_control(PyObject *self, PyObject *args) {
    int kdpfd;
    int epop;
    int fd;
    int epevents;
    int ret;
    struct epoll_event ev;

    if (!PyArg_ParseTuple(args, "iiik", &kdpfd, &epop, &fd, &epevents)) {
        return NULL;
    }

    ev.events = epevents;
    ev.data.fd = fd;

    // Reall call to epoll_ctl 
    ret = epoll_ctl(kdpfd, epop, fd, &ev);

    if (ret == -1) {
        return PyErr_SetFromErrno(PyExc_IOError);
    } else {
        return Py_BuildValue("i", ret);
    }
}

/*
 * Wrapper around epoll_wait. Warning: it uses threads.
 *
 */
static PyObject * _epoll_wait(PyObject *self, PyObject *args) {
    struct epoll_event *events;
    int kdpfd;
    unsigned int maxevents;
    int timeout;
    int nfds;
    int i;
    int nbytes;
    PyObject *eplist;

    if (!PyArg_ParseTuple(args, "iIi", &kdpfd, &maxevents, &timeout)) {
        return NULL;
    }

    nbytes = sizeof(struct epoll_event) * maxevents;
    events = (struct epoll_event*) malloc(nbytes);
    if (!events) {
        return NULL;
    }
    memset(events, 0, nbytes);

    // Here the job is done: allow threading, and then call to epoll_wait
    Py_BEGIN_ALLOW_THREADS;
    nfds = epoll_wait(kdpfd, events, maxevents, timeout);
    Py_END_ALLOW_THREADS;

    if (nfds == -1) {
        free(events);
        return PyErr_SetFromErrno(PyExc_IOError);
    }

    eplist = PyList_New(nfds);
    if (!eplist) {
        free(events);
        return NULL;
    }

    for (i = 0; i < nfds; i++) {
        int evevents;
        int evdatafd;
        PyObject *eptuple;

        evevents = events[i].events;
        evdatafd = events[i].data.fd;
        eptuple = Py_BuildValue("ik", evdatafd, evevents);

        PyList_SET_ITEM(eplist, i, eptuple);
    }
    free(events);
    return eplist;
}

/*
 * Close the epoll fd returned by create.
 *
 * For now it's a simple close(), but the function is here to do more job
 * if necessary.
 * 
 */
static PyObject * _epoll_close(PyObject *self, PyObject *args) {
    int kdpfd;
    int ret;

    if (!PyArg_ParseTuple(args, "i", &kdpfd)) {
        return NULL;
    }

    // Call close on the given fd.
    ret = close(kdpfd);

    if (ret == -1) {
        return PyErr_SetFromErrno(PyExc_IOError);
    } else {
        return Py_BuildValue("i", ret);
    }
}

static PyMethodDef epoll__methods__[] = {
    {"wait", _epoll_wait, METH_VARARGS,
     "Wait for events on the epoll fd for a maximum time of timeout.\n\n It "
     "returns a list of (fd, events)."},
    {"close", _epoll_close, METH_VARARGS,
     "Close the epoll fd."},
    {"control", _epoll_control, METH_VARARGS,
     "Control an epoll fd with given operation.\n\n The following operations "
     "can be used: CTL_ADD, CTL_DEL, CTL_MOD."},
    {"create", _epoll_create, METH_VARARGS,
     "Create a new epoll file descriptor.\n\nThe fd returned should be used "
     "with the control and wait functions."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

PyMODINIT_FUNC initepoll(void) {
    PyObject *epoll_module;

    epoll_module = Py_InitModule3("epoll", epoll__methods__, epoll__doc__);
 
    PyModule_AddIntConstant(epoll_module, "IN", EPOLLIN);
    PyModule_AddIntConstant(epoll_module, "OUT", EPOLLOUT);
    PyModule_AddIntConstant(epoll_module, "PRI", EPOLLPRI);
    PyModule_AddIntConstant(epoll_module, "ERR", EPOLLERR);
    PyModule_AddIntConstant(epoll_module, "HUP", EPOLLHUP);
    PyModule_AddIntConstant(epoll_module, "ET", EPOLLET);
    PyModule_AddIntConstant(epoll_module, "ONESHOT", EPOLLONESHOT);
    PyModule_AddIntConstant(epoll_module, "CTL_ADD", EPOLL_CTL_ADD);
    PyModule_AddIntConstant(epoll_module, "CTL_DEL", EPOLL_CTL_DEL);
    PyModule_AddIntConstant(epoll_module, "CTL_MOD", EPOLL_CTL_MOD);
}

