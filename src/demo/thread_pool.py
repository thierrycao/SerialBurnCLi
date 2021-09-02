import threading
import time
import inspect
import ctypes
import traceback


threads = []


def put_thread(thread):
    global threads

    if thread not in threads:
        threads.append(thread)


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    try:
        # 如果调用的时候线程已经执行完了，那么会结束异常，直接忽略
        _async_raise(thread.ident, SystemExit)
    except:
        pass


def clear_thread():
    '''
    保底清子线程，避免子线程卡住导致无法退出主线程
    '''
    for thread in threads:
        # thread.join()
        stop_thread(thread)
