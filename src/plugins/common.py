# -*- coding:utf-8 -*-
#*************************************************************************
#	> File Name: common.py
#	> Author: ThierryCao
#	> Mail: sycao@listenai.com
#	> Created Time: Thu 13 Mar 2021 12:54:08 PM CST
# ************************************************************************


import os
import platform


def extpath(path):
    path = os.path.abspath(path)
    if platform.system() == "Windows" and not path.startswith(u'\\\\?\\'):
        if path.startswith(u'\\\\.\\'):
            path = u'\\\\?\\' + path[4:]
        elif path.startswith(u'\\\\'):
            path = u'\\\\?\\UNC\\' + path[2:]
        else:
            path = u'\\\\?\\' + path
    return path


def dirs(dirs):
    try:
        if not os.path.exists(dirs):
            os.makedirs(dirs)
    except Exception as e:
        print(e)
    return dirs


def is_windows():
    if platform.system() == "Windows":
        return True
    else:
        return False
