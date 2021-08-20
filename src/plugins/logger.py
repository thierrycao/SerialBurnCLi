# -*- coding:utf-8 -*-
# *************************************************************************
#	> File Name: logger.py
#	> Author: ThierryCao
#	> Mail: sycao@listenai.com
#	> Created Time: Thu 28 May 2020 12:54:08 PM CST
# ************************************************************************
import datetime
from colorama import init, Fore
import os

init(autoreset=True)

log_file = None

# print(Fore.GREEN + 'it use green color to print str' + Fore.RESET)

LOG_LEVEL= 4

LOG_ERROR = 1
LOG_WARN = 2
LOG_INFO = 3
LOG_VERBOSE = 4

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    BOLDBLUE = '\033[1;94m'
    BOLDGREEN = '\033[1;92m'
    BOLDYELLOW = '\033[1;93m'
    BOLDPURPLE = '\033[1;94m'
    BOLDRED = '\033[1;91m'
    OKRED = '\033[32m'
    OKYELLOW = '\033[34m'
    OKPURPLE = '\033[35m'
    TITILEBLUE = '\033[1;36;40m'
    TITILEGREEN = '\033[1;32;40m'
    TITILEPURPLE = '\033[1;35;40m'
    TITILEYELLOW = '\033[1;33;40m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def init_log_file(path):
    global log_file
    if log_file:
        log_file.close()
    else:
        log_file = open(path, 'w+')


def LOGIB(msg):
    print_with_color(msg, bcolors.OKRED, "INFO")

def LOGR(msg):
    print_with_color(msg, bcolors.OKGREEN, time_flag=False)

def LOGG(msg):
    print_with_color(msg, bcolors.OKGREEN, time_flag=False)

def LOGB(msg):
    print_with_color(msg, bcolors.OKBLUE, time_flag=False)


def LOGIG(msg):
    print_with_color(msg, bcolors.OKGREEN, "INFO")

def print_hex(*msg):
    # print(type(msg))
    length = len(*msg)
    data = []
    # print('hhhh', length)

    if isinstance(*msg, list):
        data = list(*msg)
    for i in range(0, length, 16):
        if i == length -1:
            print("%05x   %s"%(i, ' '.join([ '%02x'%(j) for j in data[i:] ] )))
        else:
            # print("%x %s"%(i*16, ' '.join(msg[i, i+16] )))
            print("%05x   %s"%(i, ' '.join( [ '%02x'%(j) for j in data[i:i+16] ] ) ))

def LOGV(*msg):
    msg_info = ''
    # for single_item in msg:
    #     msg_info += str(single_item)
    msg_info = [str(i) for i in msg ]
    msg_info = ','.join(msg_info)

    print_with_color(msg_info, bcolors.HEADER, tag = "VERB")

def LOGI(*msg):
    msg_info = ''
    for single_item in msg:
        msg_info += str(single_item)
    print_with_color(msg_info, bcolors.HEADER, tag = "INFO")

def LOGW(*msg):
    msg_info = ''
    for single_item in msg:
        msg_info += str(single_item)
    print_with_color(msg_info, bcolors.HEADER, tag = "WARN")


def LOGE(*msg):
    msg_info = ''
    for single_item in msg:
        msg_info += str(single_item)
    print_with_color(msg_info, bcolors.HEADER, tag = "ERRO")

def get_appoint_color_text(msg='', fg='', bg='', bold=True):
    fg_color = {'black': 30, 'red': 31, 'green': 32, 'yellow': 33, 'blue': 34, 'purple': 35, 'cyan': 36, 'white': 37}
    bg_color = {'black': 40, 'red': 41, 'green': 42, 'yellow': 43, 'blue': 44, 'purple': 45, 'cyan': 46, 'white': 47}
    temp_list = []
    if bold:
        temp_list.append(1)
    if fg in fg_color.keys():
        temp_list.append(fg_color[fg])
    else:
        temp_list.append(fg_color['white'])
    if bg in bg_color.keys():
        temp_list.append(bg_color[bg])
    # else:
    #     temp_list.append(bg_color['black'])
    temp_list = [str(i) for i in temp_list]
    temp = ';'.join(temp_list)
    color = '\033[{}m'.format(temp)
    return get_color_text(msg, color, time_flag=False)

def get_blue_title(msg):
    return get_color_text(msg, bcolors.TITILEBLUE, time_flag=False)
def get_green_title(msg):
    return get_color_text(msg, bcolors.TITILEGREEN, time_flag=False)
def get_purple_title(msg):
    return get_color_text(msg, bcolors.TITILEPURPLE, time_flag=False)
def get_yellow_title(msg):
    return get_color_text(msg, bcolors.TITILEYELLOW, time_flag=False)
def get_red_text(msg, bold=True, intent=False):
    return get_color_text(msg, bcolors.OKRED if not bold else bcolors.BOLDRED, time_flag=False, intent=intent)
def get_blue_text(msg, bold=True, intent=False):
    return get_color_text(msg, bcolors.OKBLUE if not bold else bcolors.BOLDBLUE, time_flag=False, intent=intent)
def get_green_text(msg, bold=False, intent=False):
    return get_color_text(msg, bcolors.OKGREEN if not bold else bcolors.BOLDGREEN, time_flag=False, intent=intent)
def get_purple_text(msg, bold=True, intent=False):
    return get_color_text(msg, bcolors.OKPURPLE if not bold else bcolors.BOLDPURPLE, time_flag=False, intent=intent)
def get_yellow_text(msg, bold=True, intent=False):
    return get_color_text(msg, bcolors.OKYELLOW if not bold else bcolors.BOLDYELLOW, time_flag=False, intent=intent)

def get_color_text(msg, color, time_flag=False, tag='', intent=False, aligh_len=24):
    
    def aligns(msg, aligh_len=16):
        isChinese = lambda ch: True if (ch >='\u4e00' and ch <= '\u9fa5') else False
        count = 0
        for line in msg:
            count = (count + 2) if isChinese(line) else (count + 1)
        return msg + " " * (aligh_len - count)

    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if tag:
        if intent:
            log = '{:<20}\t{:<10}\t{}'.format(time, f'[{tag}]', msg)
        else:
            log = '{}{}{}'.format(time, f'[{tag}]', msg)
    else:
        if intent:
            log = '{:<20}\t{}'.format(time, msg) if time_flag else '{0:{1}<{2}}\t'.format(aligns(msg, aligh_len), chr(12288), aligh_len)
        else:
            log = '{}{}'.format(time, msg) if time_flag else '{}'.format(msg)
    # log = f'{time}\t[{tag}]\t{msg}'
    # print('----------------------------')
    # print(f"{color}{log}{bcolors.ENDC}")
    # print(log, len(log))
    # print('----------------------------')
    # text = f"{color}{log}{bcolors.ENDC}"
    
    text = "{}{}{}".format(color,log,bcolors.ENDC)
   
    return text

def print_with_color(msg, color, time_flag=True, tag=''):
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    LOG_LEVEL_DIC = {
        'ERRO' : 1,
        'WARN' : 2,
        'INFO' : 3,
        'VERB' : 4
    }

    if LOG_LEVEL < LOG_LEVEL_DIC.get(tag):
        return 

    if tag:
        log = '{:<20}\t{:<10}\t{}'.format(time, f'[{tag}]', msg)
    else:
        log = '{:<20}\t{}'.format(time, msg) if time_flag else '{}'.format(msg)
    # log = f'{time}\t[{tag}]\t{msg}'
    print(f"{color}{log}{bcolors.ENDC}")
    if not log.endswith('\n'):
        log += '\n'
    if log_file:
        try:
            log_file.write(log)
        except Exception:
            return
