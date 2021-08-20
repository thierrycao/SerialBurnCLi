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


global_big_end = 'little'

global_frame_count = 0
global_frame_head_len = 16

GLOMAL_SPI_NORMAL = False

global_output_directory = {
    'cut_out_images': {
        'dir': 'out/cut_out_images'
    },

    'stitching_images': {
                            'dir':'out/stitching_images',
                            'file': 'out/stitching_images/final.bmp'
    },
    'binary_images': {
        'dir': 'out/binary_images'
    }
    
}

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


def is_little_endian():
    global global_big_end
    return True if global_big_end == 'little' else False

def get_spi_frame_mosi_data(data):
    if data[2] == '':
        return 0
    else:
        return int(data[2], 16)

def get_spi_frame_tag(index, frame_list):
    if is_little_endian():
        return ( get_spi_frame_mosi_data(frame_list[index+0]) + get_spi_frame_mosi_data(frame_list[index+1]) * (2**8) )
    else:
        return ( get_spi_frame_mosi_data(frame_list[index+1]) + get_spi_frame_mosi_data(frame_list[index+0]) * (2**8) )

def get_spi_frame_version(index, frame_list):
    return get_spi_frame_mosi_data(frame_list[index+2])

def get_spi_frame_fuid(index, frame_list):
    if is_little_endian():
        return ( get_spi_frame_mosi_data(frame_list[index+3]) + get_spi_frame_mosi_data(frame_list[index+4]) * (2**8) )
    else:
        return ( get_spi_frame_mosi_data(frame_list[index+4]) + get_spi_frame_mosi_data(frame_list[index+3]) * (2**8) )

def get_spi_frame_type(index, frame_list):
    return get_spi_frame_mosi_data(frame_list[index+5])

def get_spi_frame_fmt(index, frame_list):
    return get_spi_frame_mosi_data(frame_list[index+6])


def get_spi_frame_xset(index, frame_list):
    if get_spi_frame_mosi_data(frame_list[index+7]) > 128:
        return (get_spi_frame_mosi_data(frame_list[index+7])  - 0x100 )
    else:
        return get_spi_frame_mosi_data(frame_list[index+7])

def get_spi_frame_yset(index, frame_list):
    if get_spi_frame_mosi_data(frame_list[index+8]) > 128:
        return (get_spi_frame_mosi_data(frame_list[index+8]) - 0x100)
    else:
        return get_spi_frame_mosi_data(frame_list[index+8])

def get_spi_frame_width(index, frame_list):
    if is_little_endian():
        return ( get_spi_frame_mosi_data(frame_list[index+9]) + get_spi_frame_mosi_data(frame_list[index+10]) * (2**8) )
    else:
        return ( get_spi_frame_mosi_data(frame_list[index+10]) + get_spi_frame_mosi_data(frame_list[index+9]) * (2**8) )

def get_spi_frame_heigh(index, frame_list):
    if is_little_endian():
        return ( get_spi_frame_mosi_data(frame_list[index+11]) + get_spi_frame_mosi_data(frame_list[index+12]) * (2**8) )
    else:
        return ( get_spi_frame_mosi_data(frame_list[index+12]) + get_spi_frame_mosi_data(frame_list[index+11]) * (2**8) )

def get_spi_frame_depth(index, frame_list):
    return get_spi_frame_mosi_data(frame_list[index+13])
 
def get_spi_frame_checksum(index, frame_list):
    if is_little_endian():
        return ( get_spi_frame_mosi_data(frame_list[index+14]) + get_spi_frame_mosi_data(frame_list[index+15]) * (2**8) )
    else:
        return ( get_spi_frame_mosi_data(frame_list[index+15]) + get_spi_frame_mosi_data(frame_list[index+14]) * (2**8) )   

def print_spi_frame_head(index, frame_list):
    logger.LOGV('TAG:', get_spi_frame_tag(index, frame_list), \
          'version', get_spi_frame_version(index, frame_list), \
          'fuid', get_spi_frame_fuid(index, frame_list), \
          'type', get_spi_frame_type(index, frame_list), \
          'fmt', get_spi_frame_fmt(index, frame_list), \
          'xset', get_spi_frame_xset(index, frame_list), \
          'yset', get_spi_frame_yset(index, frame_list), \
          'width', get_spi_frame_width(index, frame_list), \
          'heigh', get_spi_frame_heigh(index, frame_list), \
          'depth', get_spi_frame_depth(index, frame_list), \
          'checksum', get_spi_frame_checksum(index, frame_list)
        )

def get_spi_rda_line_start_data(index, frame_list):
    line_start = [ 0xff, 0xff, 0xff, 0x2, 0x0, 0x28 ]
    data_start = [ 0xff, 0xff, 0xff, 0x40, 0x0, 0x80 ]
    line_start_data = line_start + data_start
    if is_little_endian():
        return frame_list[index:index + 12] == line_start_data 
    else:
        return frame_list[index:index + 12] == line_start_data 

def get_spi_rda_data_index(index, frame_list):
    return get_spi_rda_line_start_data(index, frame_list) 


def get_spi_frame_data(index, frame_list):
    local_width = get_spi_frame_width(index, frame_list)
    local_heigh = get_spi_frame_heigh(index, frame_list)

    if GLOMAL_SPI_NORMAL:
        return [ get_spi_frame_mosi_data(i) for i in frame_list[index + global_frame_head_len : index + global_frame_head_len + local_width * local_heigh] ]

    frames = int( (global_frame_head_len + local_heigh * local_width) / 128 )
    frames_remainder = int( (global_frame_head_len + local_heigh * local_width) % 128 )
    if frames_remainder > 0:
        frames += 1

    jump_count = 0
    line_count = 0
    frame_data = []
    raw_data = [ get_spi_frame_mosi_data(i) for i in frame_list[index + global_frame_head_len : (index + global_frame_head_len + (frames -1 )*12 + local_width * local_heigh) ] ]
    # print('raw_data:', raw_data)
    logger.LOGV('raw_data', 'frames:',frames, 'len:', len(raw_data))
    logger.print_hex(raw_data)

    for i, value in enumerate(raw_data):
        if i > len(raw_data) - 12:
            frame_data.extend(raw_data[i:])
            break

        if jump_count > 0:
            jump_count += -1
            continue
        is_rda_line_start = get_spi_rda_data_index(i, raw_data)
        if is_rda_line_start:
            jump_count = 11
            is_rda_line_start = False
            line_count += 1
            
            continue
        frame_data.append(value)
    logger.LOGV('frame_data', 'len:', len(frame_data), 'line_count:', line_count) 
    return frame_data


def camera_spi_parse(frame, index, frame_list):
    global global_frame_count
    global_frame_count += 1
    logger.LOGV(index, global_frame_count)
    print_spi_frame_head(index, frame_list)

    spi_frame_data = get_spi_frame_data(index, frame_list)

    print('camera_spi_parse: ', len(spi_frame_data))
    # print(spi_frame_data)

    # 生成bin文件
    binary_images_save_path = os.path.join( global_output_directory.get('binary_images').get('dir'), f'{global_frame_count}_{get_spi_frame_width(index, frame_list)}_{get_spi_frame_heigh(index, frame_list)}.bin')
    generate_binary_images(spi_frame_data, output= binary_images_save_path)

    # 生成裁剪图片
    cut_out_images_save_path = os.path.join(global_output_directory.get('cut_out_images').get('dir'), f'{global_frame_count}_{get_spi_frame_width(index, frame_list)}_{get_spi_frame_heigh(index, frame_list)}.bmp')
    generate_cut_out_images(spi_frame_data, width=get_spi_frame_width(index, frame_list), height=get_spi_frame_heigh(index, frame_list), output=cut_out_images_save_path)
    
    return {'width':get_spi_frame_width(index, frame_list), \
            'heigh': get_spi_frame_heigh(index, frame_list), \
            'xset': get_spi_frame_xset(index, frame_list), \
            'yset': get_spi_frame_yset(index, frame_list), \
            'file_path': cut_out_images_save_path }

def get_spi_frame_info(frame, index, frame_list):
    if is_little_endian():
        if frame[2] == '0x46' and frame_list[index+1][2] == '0x5A' and frame_list[index+2][2] == '0x00':
            return True
        else:
            return False

def get_spi_data(file_name):
    frame_info = list()
    
    spi_data_list = utils.read_list_from_csv(file_name, column_num=-1)
    if not spi_data_list:
        return
    # logger.LOGV(spi_data_list)
    for index, frame in enumerate(spi_data_list):
        if get_spi_frame_info(frame, index, spi_data_list):
            info = {}
            info = camera_spi_parse(frame, index, spi_data_list)
            frame_info.append(info)

    # 生成拼接图片
    generate_stitch_image(frame_info, global_output_directory.get('stitching_images').get('file') )

def generate_cut_out_images(frame_data, width, height, output):
    utils.write_bin_list_to_bmp(frame_data, width, height, output)

def generate_binary_images(frame_data, output):
    utils.write_bin_list_to_file(frame_data, output)

def generate_stitch_image(frame_info, output):
    utils.connect_bmp(frame_info, output)
    

def app_main(file_name):
    if not os.path.isfile(file_name):
        logger.LOGE(f"can't found {file_name}")
        return

    for item in global_output_directory.keys():
        if 'dir' in global_output_directory.get(item).keys():
            utils.dirs(global_output_directory.get(item).get('dir'))

    get_spi_data(file_name)

def version_print():
    description = '''
Version: v1.0\n 
Time: 2021/8/17\n  
Author: theirrycao\n
RELEASE:\n
支持SPI协议和RDA协议解析，默认是SPI协议

'''
    description = logger.get_yellow_text(description)
    return description

def parse_user_choice():
    import argparse
    args = None
    try:
        parser = argparse.ArgumentParser(description='欢迎使用本打包工具')
        # parser.add_argument("-c", type=int, choices=[1,2], help="芯片类型[1:300x 2:4002][已废弃，使用默认资源，不支持修改]")
        parser.add_argument("-p", type=str, required = True, choices=['spi','rda'], help="协议形式: spi 或者 rda")
        parser.add_argument("-f", type=str, required = True, help="逻辑分析仪协议导出数据[*.csv]")
        parser.add_argument("-v", action="version", version=version_print())
        
        args = parser.parse_args()
        print(args)
        # args = parser.parse_args(choice.split())
    # args = parser.parse_args(['-main', './main.bin', '-cmd', './cmd.bin', '-bias', './bias.bin', '-mlp', './mlp.bin'])
    except Exception as e:
        eprint(e)

    finally:
        return args if args else None

def main():
    global GLOMAL_SPI_NORMAL
    init()

    args = parse_user_choice()
    if not args:
        return
    GLOMAL_SPI_NORMAL = True if args.p == 'spi' else False

    logger.LOGI(args)
    app_main(args.f)


if __name__ == '__main__':
    main()
