
# -*- coding:utf-8 -*-
#*************************************************************************
#	> File Name: raw_input.py
#	> Author: ThierryCao
#	> Mail: sycao@listenai.com
#	> Created Time: Thu 13 Mar 2021 12:54:08 PM CST
# ************************************************************************

import os

import audio_task.utils.logger as logger


def input_str(desc):
    return input(desc)


def input_path(desc, retryTimes):
    pathStr = input_str(desc)
    if(os.path.exists(pathStr)):
        return pathStr
    else:
        if(retryTimes > 1):
            logger.LOGW('文件不存在，请重新输入。')
            return input_path(desc, retryTimes - 1)
        else:
            logger.LOGE('错误次数过多，即将退出程序。')
            exit(1)


def input_int(desc, retryTimes):
    str_in = input_str(desc)
    try:
        return int(str_in)
    except Exception:
        if(retryTimes > 1):
            logger.LOGW('只能输出数字，请重新输入。')
            return input_int(desc, retryTimes - 1)
        else:
            logger.LOGE('错误次数过多，即将退出程序。')
            exit(1)


def input_options(desc, values, retryTimes):
    pathStr = input_str(desc)
    if pathStr in values:
        return pathStr
    else:
        if(retryTimes > 1):
            logger.LOGW('找不到该选项, 请重新输入')
            return input_options(desc, values, retryTimes - 1)
        else:
            logger.LOGE('错误次数过多，即将退出程序。')
            exit(1)
