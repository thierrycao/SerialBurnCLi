# -*- coding:utf-8 -*-
#*************************************************************************
#	> File Name: LSFactoryPacker.py
#	> Author: ThierryCao
#	> Mail: sycao@listenai.com
#	> Created Time: Thu 13 Mar 2021 12:54:08 PM CST
# ************************************************************************

import os, sys, hashlib, signal, shutil
sys.path.append("..") 
from plugins import utils as utils
from plugins import logger as logger

from PIL import Image
import numpy as np


global_big_end = 'little'

global_frame_count = 0
global_frame_head_len = 16

if os.name == 'posix':
    from plugins import console_posix as console
else:
    from plugins import console as console


def exit_app(_signum, _frame):
    import traceback
    try:
        # 等一等子线程销毁
        # time.sleep(0.5)
        sys.exit(1)
    except:
        traceback.print_exc()
        os._exit(0)

def init():
    signal.signal(signal.SIGINT, exit_app)
    signal.signal(signal.SIGTERM, exit_app)


def connect_bmp():

    width = 300
    height = 180
    # 创建空白图片
    img_gray_8 = Image.new('L', (width, height), 128)
    img1 = Image.open('out/bmp/1_10_180.bmp').convert("L")
    img2 = Image.open('out/bmp/2_18_180.bmp').convert("L")
    img3 = Image.open('out/bmp/3_32_180.bmp').convert("L")
    img4 = Image.open('out/bmp/4_46_180.bmp').convert("L")
    img5 = Image.open('out/bmp/5_60_180.bmp').convert("L")
    img6 = Image.open('out/bmp/6_60_180.bmp').convert("L")
    img7 = Image.open('out/bmp/7_58_180.bmp').convert("L")
    
    
    # img = img.resize((718,327))
    # img = img.convert("L")
    img_gray_8.paste(img1, (0, 0))
    img_gray_8.paste(img2, (10, 0))
    img_gray_8.paste(img3, (10+18, 0))
    img_gray_8.paste(img4, (10+18+32, 0))
    img_gray_8.paste(img5, (10+18+32+46, 0))
    img_gray_8.paste(img6, (10+18+32+46+60, 0))
    img_gray_8.paste(img7, (10+18+32+46+60+60, 0))

    img_gray_8.save("img_gray_8.bmp")

    # target = Image.new('RGBA', (width, hight+504), (255, 255, 255))

    # 创建header Image对象，paste拼接到空白图片指定位置target.paste(img_h, (0, 0))
    # img_h = img_header(os.path.join(tasktheme_img_path, task_img))
    # 图片合成paste 参数中img_h表示Image对象，(0, 0)表示x,y轴位置 单位像素 target的左上角为原点 y轴向下 

def main():
    init()
    connect_bmp()

    # get_spi_data('2.csv')


if __name__ == '__main__':
    main()