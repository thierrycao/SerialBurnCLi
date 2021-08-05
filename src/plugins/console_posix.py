#!/bin/python


import sys
import time

CSI = '\033['

def cursor_prev_line():
    return CSI + '1F'

def cursor_clean_screen():
    return CSI + '5A'

def erase_screen(mode = 0):
    sys.stdout.write(cursor_clean_screen())
    sys.stdout.flush()


def restore_last_position(row = 0 , col = 0):
    sys.stdout.write(cursor_prev_line())
    sys.stdout.flush()
