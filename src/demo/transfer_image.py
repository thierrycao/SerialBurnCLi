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

def transfer(input_img, output_img):
    width = 128
    height = 180
    # 创建空白图片
    img_gray_8 = Image.new('L', (width, height), 128)
    img1 = Image.open(input_img).convert("L").resize((128, 180),Image.ANTIALIAS)
    img_gray_8.paste(img1, (0, 0))
    img_gray_8.save(output_img)

def print_bmp_header(file_name):
    import numpy as np
    import struct
    import matplotlib.pyplot as plt

    f = open(file_name, 'rb')  # 只读，二进制打开，

    #'1、文件头:一共14字节'
    bfType = f.read(2)  # 文件类型
    bfSize1 = f.read(4)  # 该bmp文件总大小
    f.seek(f.tell() + 4)  # 跳过保留字
    bfOffBits1 = f.read(4)  # 从文件开始到数据开始的偏移量，    偏移1078 加上256*256正好是文件的大小（单位：B）

    # struct.unpack('i',*) 也可以
    bfSize = int.from_bytes(bfSize1, byteorder='little', signed=True)
    bfOffBits = int.from_bytes(bfOffBits1, byteorder='little', signed=True)

    #'2、信息头：40B'
    biSize = f.read(4)  # 这部分长度为40字节
    biWidth1 = f.read(4)
    biHeight1 = f.read(4)
    biPlanes = f.read(2)  # 1,位图的位面数
    biBitCount1 = f.read(4)

    # struct.unpack('i',*) 也可以
    biWidth = int.from_bytes(biWidth1, byteorder='little', signed=True)
    biHeight = int.from_bytes(biHeight1, byteorder='little', signed=True)
    biBitCount = int.from_bytes(biBitCount1, byteorder='little', signed=True)

    print('文件类型{0}，大小{1}，偏移量{2}，位图宽度（列）{3}，高度（行）{4}，每个像素所占位数{5}'.format(bfType, bfSize, bfOffBits, biWidth, biHeight,
                                                                        biBitCount))
    f.close()


def get_bmp_offset(file_name):
    if not os.path.isfile(file_name):
        return
    import numpy as np
    import struct
    import matplotlib.pyplot as plt

    f = open(file_name, 'rb')  # 只读，二进制打开，

    #'1、文件头:一共14字节'
    bfType = f.read(2)  # 文件类型
    bfSize1 = f.read(4)  # 该bmp文件总大小
    f.seek(f.tell() + 4)  # 跳过保留字
    bfOffBits1 = f.read(4)  # 从文件开始到数据开始的偏移量，    偏移1078 加上256*256正好是文件的大小（单位：B）

    # struct.unpack('i',*) 也可以
    bfSize = int.from_bytes(bfSize1, byteorder='little', signed=True)
    bfOffBits = int.from_bytes(bfOffBits1, byteorder='little', signed=True)

    #'2、信息头：40B'
    biSize = f.read(4)  # 这部分长度为40字节
    biWidth1 = f.read(4)
    biHeight1 = f.read(4)
    biPlanes = f.read(2)  # 1,位图的位面数
    biBitCount1 = f.read(4)

    # struct.unpack('i',*) 也可以
    biWidth = int.from_bytes(biWidth1, byteorder='little', signed=True)
    biHeight = int.from_bytes(biHeight1, byteorder='little', signed=True)
    biBitCount = int.from_bytes(biBitCount1, byteorder='little', signed=True)

    # print('文件类型{0}，大小{1}，偏移量{2}，位图宽度（列）{3}，高度（行）{4}，每个像素所占位数{5}'.format(bfType, bfSize, bfOffBits, biWidth, biHeight,
                                                                        # biBitCount))
    f.close()

    return bfOffBits


def bmp_to_binary(bmp_file, output_binary):
    offset = get_bmp_offset(bmp_file)
    print(offset)
    try:
        with open(bmp_file, "rb") as image_file , open(output_binary, "wb") as binary_file:
            # Blindly skip the BMP header. 
            image_file.seek(offset)
            data = image_file.read()
            binary_file.write(data)
            #binary_file.write(data[len(data)-128*180:])
    except Exception as err:
        print(err)

def binary_to_cheader(binary_file, output_cheader):
    #import commands
    cmd = 'xxd -i {} {}'.format(binary_file, output_cheader)
    #output_info = commands.getoutput(cmd)
    ret = utils.run_shell(cmd)
    print(ret)    
    
def main():
    init()
    input_img = 'res/default.jpg'
    output_img = 'out/img_gray_8.bmp'
    output_binary = os.path.join(os.path.dirname(output_img), '{}.bin'.format(os.path.splitext( os.path.basename(output_img) )[0] ) )

    output_cheader = os.path.join(os.path.dirname(output_img), '{}.h'.format(os.path.splitext( os.path.basename(output_img) )[0] ) )
    utils.dirs(os.path.dirname(output_img))

    transfer(input_img, output_img)
    print_bmp_header(output_img)
    bmp_to_binary(output_img, output_binary)
    binary_to_cheader(output_binary, output_cheader)

    # get_spi_data('2.csv')


if __name__ == '__main__':
    main()
