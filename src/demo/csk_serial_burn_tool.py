# -*- coding:utf-8 -*-
#*************************************************************************
#	> File Name: LSFactoryPacker.py
#	> Author: ThierryCao
#	> Mail: sycao@listenai.com
#	> Created Time: Thu 13 Mar 2021 12:54:08 PM CST
# ************************************************************************
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
from pycallgraph import Config
from pycallgraph import GlobbingFilter

import os, sys, time
sys.path.append("..") 
sys.path.append(".") 
from plugins import utils as utils
from plugins import logger as logger
from plugins.utils import getmd5 as getmd5
from plugins.utils import getmd5_fromlist as getmd5_fromlist
from tqdm import tqdm

from csk_burn_protocol_client import CSKBurnProtocolClient as CSKBurnProtocolClient
from csk_read_thread import ReadSerialThread as ReadSerialThread

g_serial_raw_dump_dbg = False
g_serial_interaction_dump_dbg = False
g_serial_print_funcname_dbg = False


g_serial_baudrate = 115200
default_baud_rate=1536000
global_big_end = 'little'
g_serial_status = 'uninit'

gSerialClientInstance = None
gSerialInstance = None

# burn partiion info
g_burn_resource_dict = {}
# lpk resouce
g_resource_burn_lpk = ''


# if os.name == 'posix':
#     from plugins import console_posix as console
# else:
#     from plugins import console as console

def exit_app(_signum = 0, _frame = 0):
    #import traceback
    try:
        # 等一等子线程销毁
        # time.sleep(0.5)
        global gSerialClientInstance,gSerialInstance

        if gSerialClientInstance:
            gSerialClientInstance.deinit_serial()
        gSerialInstance.notice_end_read()
        sys.exit(1)
    except:
        # traceback.print_exc()
        os._exit(0)

def init():
    from signal import SIGINT, SIGTERM
    from signal import signal
    signal(SIGINT, exit_app)
    signal(SIGTERM, exit_app)


def is_little_endian():
    global global_big_end
    return True if global_big_end == 'little' else False


def init_serial(com = None):
    """初始化串口
    """
    gSerialInstance = None
    # logger.LOGI(f"初化串口成功：{port}")
    try:
        gSerialInstance = ReadSerialThread(g_serial_raw_dump_dbg, com)
        gSerialInstance.start()
        gSerialInstance.mark_start()
        logger.LOGI('初始化串口成功: {}'.format(gSerialInstance.serial_com))
    except Exception as err:
        logger.LOGE("初始化串口失败 {}".format(err))
        exit_app(1, 0)
    finally:
        return gSerialInstance

def task_retry(func, count, notice = '完成了', param = None, time_sep = 0.5):
    total_count = count
    while count > 0:
        logger.LOGB(f'\r设备正在连接...[{count}/{total_count}]', end='')
        count -= 1
        if param:
            ret = func(param)
        else:
            ret = func()
        if ret == True:
            logger.LOGB('\r%s '%notice, end='\n')
            return True
        time.sleep(time_sep)
    logger.LOGE('失败了')
    return False
        
def _serial_enter(instance = gSerialClientInstance, change_baud=True):

    global g_burn_resource_dict, gSerialClientInstance, g_serial_status
    if not instance:
        instance = gSerialClientInstance

    RAM_BLOCK_SIZE = 0x800
    burner_len = os.path.getsize(g_burn_resource_dict.get('burner').get('file'))
    blocks = instance.BLOCKS(burner_len, RAM_BLOCK_SIZE)
    if not instance.cmd_mem_begin(burner_len, blocks, RAM_BLOCK_SIZE, 0):
        logger.LOGE('cmd_mem_begin fails')
        return False

    data = utils.read_hex_from_bin(g_burn_resource_dict.get('burner').get('file'))
    offset = 0

    with tqdm(total = blocks + 1, desc= 'burner', leave = True, ncols = 50, unit='Blocks', unit_scale = True) as pbar:
        for i in range(blocks):
            offset = RAM_BLOCK_SIZE * i
            length = RAM_BLOCK_SIZE

            if offset + length > burner_len:
                length = burner_len - offset

            if not instance.cmd_mem_block(data[offset:offset + length], length, i):
                logger.LOGE('cmd_mem_block fails')
                return False
            pbar.update(1)

        if not instance.cmd_mem_end():
            logger.LOGE('cmd_mem_end fails')
            return False
        pbar.update(1)


    time.sleep(0.5)

    if not instance.cmd_sync(2):
        logger.LOGE('错误: 无法识别设备')
        return False
    else:
        logger.LOGI('同步成功')
    if change_baud:
        if not instance.cmd_change_baud(default_baud_rate):
            logger.LOGE('错误: 无法设置串口速率')
            return False
        else:
            logger.LOGI('波特率更改成功')
        # 设置完波特率后需要再次同步
        if not serial_connect():
            return False
       
    g_serial_status = 'enter'

    return True

def _serial_enter_no_change_baud(instance = gSerialClientInstance, change_baud=False):
    global gSerialClientInstance
    if not instance:
        instance = gSerialClientInstance
    def _serial_enter_no_change_baud_():
        return _serial_enter(instance, change_baud)
    
    if not task_retry(_serial_enter_no_change_baud_, 4, '设备连接成功'):
        logger.LOGE('设备连接失败')
        return False
    else:
        return True
    
def _serial_verify(addr, size, instance = gSerialClientInstance): 
    global gSerialClientInstance  
    if not instance:
        instance = gSerialClientInstance 
    if not g_serial_keep_enter():
        return ''
    #print('_serial_verify', 'addr', addr, 'size', size)
    return instance.cmd_flash_md5sum(addr, size) 


def g_serial_verify(partition_info):
    if partition_info:
        if not g_serial_keep_enter():
            logger.LOGE('未进入ram模式,请先短接pb16或者检查串口是否正常连接')
            return False
    #serial_burn_status_show()
    result_list = []
    logger.LOGB('分区校验结果: ')
    for p in partition_info: 
        if isinstance(p, dict) and 'addr' in p.keys() and 'size' in p.keys():
            ret = _serial_verify(p.get('addr'), p.get('size'))
            if ret:
                result = 'md5 (0x%08X-0x%08X): %s'%(p.get('addr'), p.get('addr') + p.get('size'), ret.replace('0x', '')) 
                result_list.append([p.get('name'), result])
            else:
                result = 'md5 (0x%08X-0x%08X): %s'%(p.get('addr'), p.get('adrr') + p.get('size'), 'serial_verify err: ' + ret)
                result_list.append([p.get('name'), result])
                logger.LOGE(result)
    serial_burn_status_show(result_list)
    


def g_serial_keep_enter(instance = gSerialClientInstance):
    global gSerialClientInstance, g_serial_status

    if not instance:
        instance = gSerialClientInstance

    if g_serial_status == 'connect':
        if not _serial_enter_no_change_baud():
            return False
    elif g_serial_status == 'enter':
        pass
    else:
        if not serial_connect():
            return False
        if not _serial_enter_no_change_baud():
            return False
    return True

def g_serial_read_chipid(instance = gSerialClientInstance):
    global gSerialClientInstance, g_serial_status

    EFUSE_BASE = 0xF1800000

    if not instance:
        instance = gSerialClientInstance

    if not g_serial_keep_enter():
        return False

    id1 = instance.cmd_read_reg(EFUSE_BASE + 0x80 + 0x0A)

    time.sleep(0.1)
    id0 = instance.cmd_read_reg(EFUSE_BASE + 0x80 + 0x0E)
    #logger.LOGI(f'id0:{id0}, id1:{id1}')
    if (not utils.is_number(id0) ) or ( not utils.is_number(id1) ):
        return False

    #chipid = hex( (id0 << 32) | id1 ).replace('0x', '')
    chipid = '%08x%08x'%(id0, id1)

    logger.LOGB(f'chipid: {chipid}')

    return True




def burn_image(addr, data, lens, md5sum, instance = gSerialClientInstance):
    def burn_bunch(addr, data, lens, md5sum, instance = gSerialInstance):
        global gSerialClientInstance
        if not instance:
            instance = gSerialClientInstance

        FLASH_BLOCK_SIZE = 0x1000

        blocks = instance.BLOCKS(lens, FLASH_BLOCK_SIZE)
        
        if not instance.cmd_flash_begin(lens, blocks, FLASH_BLOCK_SIZE, addr, md5sum):
            logger.LOGE('cmd_flash_begin fails')
            return False;
        index = 0
        with tqdm(total = blocks, desc= '分区', leave = True, ncols = 50, unit='B', unit_scale = True) as pbar:
            while index < blocks:
                offset = FLASH_BLOCK_SIZE * index
                length = FLASH_BLOCK_SIZE

                if (offset + length > lens):
                    length = lens - offset

                FLASH_BLOCK_TRIES = 5
                next = 0
                for i in range(FLASH_BLOCK_TRIES):
                    if i > 0:
                        logger.LOGW('第 %d 次重试写入数据块 %d' %(i, index))
                    ret = instance.cmd_flash_block(data[offset: offset+length], length, index)
                    next = ret.get('res_ret').get('value')
                    if (not ret.get('ret') ) and (i == FLASH_BLOCK_TRIES -1):
                        logger.LOGE('cmd_flash_block fails')
                        return False
                    elif ret.get('ret'):
                        break

                if next != index + 1:
                    logger.LOGW('指针由 %d 跳至 %d' %(index, next))
                    logger.LOGW('忽略该错误，用实际的index %d' %(index))
                    next = index + 1
                    time.sleep(1)
                    logger.LOGW('延时1s')
                    
                    # next = index + 1

                # 更新进度条
                pbar.update(next - index)

                index = next



    # FLASH_BLOCK_TRIES = 5
    # for i in range(FLASH_BLOCK_TRIES):
    #     if (not instance.cmd_flash_md5_challenge()) and (i == FLASH_BLOCK_TRIES -1):
    #         logger.LOGE("错误: MD5 校验失败")
    #         return False

    global gSerialClientInstance

    partions_info = []
    if not instance:
        instance = gSerialClientInstance

    FLASH_BLOCK_SIZE = 0x1000
    blocks = instance.BLOCKS(lens, FLASH_BLOCK_SIZE)

    bunch_size = 191
    

    for index in range( int((blocks + bunch_size - 1) / bunch_size) ):
        burn_bunch_lens = int(lens - index * bunch_size * FLASH_BLOCK_SIZE) if (lens - index * bunch_size * FLASH_BLOCK_SIZE) < bunch_size * FLASH_BLOCK_SIZE else int(bunch_size * FLASH_BLOCK_SIZE)
        burn_bunch_md5sum = getmd5_fromlist(data[index * bunch_size * FLASH_BLOCK_SIZE: index * bunch_size * FLASH_BLOCK_SIZE + burn_bunch_lens])
        print('addr:{:#x}, lens:{:d}, md5sum:{:#x}'.format(addr + index * bunch_size * FLASH_BLOCK_SIZE, burn_bunch_lens, burn_bunch_md5sum) )
        partions_info.append({'addr': addr + index * bunch_size * FLASH_BLOCK_SIZE, 'size': burn_bunch_lens})
        burn_bunch(addr + index * bunch_size * FLASH_BLOCK_SIZE, data[index * bunch_size * FLASH_BLOCK_SIZE: index * bunch_size * FLASH_BLOCK_SIZE + burn_bunch_lens], burn_bunch_lens, burn_bunch_md5sum, instance)
        time.sleep(0.1)

    logger.LOGB('烧录完成')

    g_serial_verify(partions_info)
    
    return True
        

    

def g_serial_burn_partition(partition, index_part=0, total_part=1):
    global g_burn_resource_dict, gSerialClientInstance

    file_exist_lambda = lambda f: f and os.path.isfile(f)

    if partition and partition in g_burn_resource_dict.keys() and file_exist_lambda(g_burn_resource_dict.get(partition).get('file')):
        md5sum = getmd5(g_burn_resource_dict.get(partition).get('file'))
        addr = g_burn_resource_dict.get(partition).get('addr')
        data = utils.read_hex_from_bin(g_burn_resource_dict.get(partition).get('file'))
        lens = len(data)
        logger.LOGB('正在烧录分区 %d/%d… (0x%08X, %.2f KB)' %(index_part+1, total_part, addr, lens/1024))
        burn_image(addr, data, lens, md5sum)

def g_serial_burn_lpk():
    global g_burn_resource_dict
    global gSerialClientInstance
    global g_resource_burn_lpk

    # 判断lpk资源是否存在
    choice = g_resource_burn_lpk 
    choice = utils.user_choice('请输入lpk路径: ', lambda f: f and utils.is_file_exists(f), choice, debug=True)
    g_resource_burn_lpk = os.path.expanduser(choice)

    # 加载lpk资源
    load_lpk_resource(g_resource_burn_lpk)

    # 判断设备的状态
    if g_serial_status == 'connect':
        logger.LOGB("2.正在进入烧录模式…")
        if not serial_enter():
            return False
    elif g_serial_status == 'enter':
        pass
    else:
        logger.LOGB('1.正在等待设备接入…')
        if not serial_connect():
            return False
        logger.LOGB("2.正在进入烧录模式…")
        if not serial_enter():
            return False

    # 读取芯片ID
    logger.LOGB("3.正在读取芯片ID…")
    g_serial_read_chipid()

    # 烧录资源
    for index, key in enumerate(g_burn_resource_dict.keys()):
        if key == 'burner':
            continue
        g_serial_burn_partition(key, index_part=index, total_part=len( [ ikey for ikey in g_burn_resource_dict.keys() if ikey != 'burner' ] ))


def serial_status_set(fn):
    global g_serial_status
    def wrapper(*arg, **kw):
        if g_serial_print_funcname_dbg:
            logger.LOGB('%s' % fn.__name__)
        ret = fn(*arg, **kw)
        if ret:
            if fn.__name__ == 'serial_connect':
                g_serial_status = 'connect'
            elif fn.__name__ == 'serial_enter':
                g_serial_status = 'enter'
        return ret
    return wrapper

@serial_status_set
def serial_connect():
    def _serial_connect(instance = gSerialClientInstance):
        if not instance:
            instance = gSerialClientInstance
        return instance.cmd_sync()

    if not task_retry(_serial_connect, 10, '设备同步成功'):
        logger.LOGE('设备连接失败')
        return False
    else:
        return True

@serial_status_set
def serial_enter(instance = gSerialClientInstance):
    if not instance:
        instance = gSerialClientInstance

    if not task_retry(_serial_enter, 1, '进入烧录模式'):
        logger.LOGE('进入烧录模式失败')
        return False
    else:
        return True
            
def g_serial_reboot(instance = gSerialClientInstance):
    global g_serial_status
    if not instance:
        instance = gSerialClientInstance

    if g_serial_status == 'connect':
        if not _serial_enter_no_change_baud():
            return False
    elif g_serial_status == 'enter':
        pass
    else:
        if not serial_connect():
            return False
        if not _serial_enter_no_change_baud():
            return False

    ret = instance.cmd_flash_finish()
    g_serial_status = ''
    instance.serialInstance.init_serial()

    return True

def serial_burn_status_show(insert_row=None):
    global gSerialClientInstance
    import prettytable as pt
    tb = pt.PrettyTable()
    tb.field_names = ["名称", "详情"]
    row_list = []
    serial_info = ['串口状态', '打开:{}, 端口:{}, 波特率: {}'.format(gSerialClientInstance.serialInstance.serial_is_open, gSerialClientInstance.serialInstance.serial_com, default_baud_rate)]
    #serial_info = ['串口状态','2']
    row_list.append(serial_info)
    if insert_row:
        if isinstance(insert_row, list):
            for item in insert_row:
                if isinstance(item, list):
                    row_list.append(item)
                else:
                    row_list.append(insert_row)
                    break

    for item in row_list:
        tb.add_row(item)
    print(tb)
    return tb

def command_prompt():
    import prettytable as pt
    tb = pt.PrettyTable()
    tb.field_names = ["item", "名称", "快捷指令"]
    tb.add_row(["1","设备连接", "c"])
    tb.add_row(["2","进入烧录", "e"])
    tb.add_row(["3","读取chipid", "r"])
    tb.add_row(["4","校验分区md5sum", "v"])
    tb.add_row(["5","烧录lpk资源", "l"])
    tb.add_row(["6","烧录flashboot", "bf"])
    tb.add_row(["7","烧录master", "bm"])
    tb.add_row(["8","烧录respak", "br"])
    tb.add_row(["9","烧录zero", "bz"])
    tb.add_row(["10","重启", "rb"])
    tb.add_row(["0","退出", "b"])
    tb.add_row(["*","查看当前波特率", "cb"])
    tb.add_row(["-","监测并连接串口", "detect"])
    return tb

def g_serial_detect(com = None):
    global gSerialClientInstance, gSerialInstance, g_serial_interaction_dump_dbg, g_serial_print_funcname_dbg
    gSerialInstance = init_serial(com)
    choice = ''

    if gSerialInstance:
        gSerialClientInstance = CSKBurnProtocolClient(gSerialInstance, g_serial_interaction_dump_dbg, g_serial_print_funcname_dbg)
    else:
        logger.LOGE('not found serial device, exit!')
        return

def app_main(argv):
    # thread = threading.Thread(target=app_serial, args=[ argv.baudrate if argv.baudrate else 115200])
    # thread.start()
    if argv.detect:
        g_serial_detect()
    else:
        if argv.port:
            g_serial_detect(argv.port)
        else:
            choice = None
            choice = utils.user_choice("是否自动检测串口端口[y/n]: ", lambda c: c and c.lower() in ['y', 'yes', 'n', 'no'], choice)
            if choice in ['y', 'yes']:
                g_serial_detect()




def serial_burn_image(instance= gSerialClientInstance):
    global gSerialClientInstance 
    global g_burn_resource_dict
    if not instance:
        instance = gSerialClientInstance

    if g_serial_status == 'connect':
        if not serial_enter():
            return False
    elif g_serial_status == 'enter':
        pass
    else:
        if not serial_connect():
            return False
        if not serial_enter():
            return False

    file_exist_lambda = lambda f: f and os.path.isfile(f)
    burn_partition = []
    for partition in ['flashboot', 'master', 'respak', 'zero']:
        if partition and partition in g_burn_resource_dict.keys() and file_exist_lambda(g_burn_resource_dict.get(partition).get('file')):
            burn_partition.append(partition)
    for index_part, partition in enumerate(burn_partition):    
        g_serial_burn_partition(partition, index_part=index_part, total_part=len(burn_partition))
    
    return True

def command_action(argv):
    if not argv.interact:
        lambda_is_file_exist = lambda f: f and os.path.isfile(f)
        if lambda_is_file_exist(argv.l):
            g_serial_burn_lpk()
            g_serial_verify_lpk_partion()
            logger.LOGB("结束!")
            return True
        elif argv.f or argv.m or argv.r or argv.z:
            serial_burn_image()
        elif argv.verify:
            partition_info = argv.verify

            serial_verify_partition_info = [ partition_info[i:i+2] for i in range(0,len(partition_info),2) ]
            serial_verify_partition_info_format = []

            for partition_index, partition_info_item in enumerate(serial_verify_partition_info):
                partition_addr = utils.user_choice('分区地址: ', lambda addr: addr is not None and addr >= 0x0 , partition_info_item[0], isDigit = True)
                partition_size = utils.user_choice('分区大小: ', lambda addr: addr is not None and addr >= 0x0 , partition_info_item[1], isDigit = True)
                serial_verify_partition_info_format.append({'name': f'分区{partition_index}', 'addr': partition_addr, 'size': partition_size})
            #print(serial_verify_partition_info_format)
            g_serial_verify(serial_verify_partition_info_format)
        else:
            return False
        return True
    return False
    

def command_menu(argv):
    while True:
        print(command_prompt())
        choice = ''
        choice = utils.user_choice('请输入:', lambda f: f is not None and f != '', choice)
        if choice == 'c':
            logger.LOGB('正在等待设备接入…')
            serial_connect()
        elif choice == 'e':
            serial_enter()
        elif choice == 'r':
            logger.LOGB("正在读取芯片ID…")
            ret = g_serial_read_chipid()
            if not ret:
                logger.LOGE('读取失败')
        elif choice == 'v':
            logger.LOGB('正在进行校验分区操作')
            partition_addr = utils.user_choice('分区地址: ', lambda addr: addr is not None and addr >= 0x0 , choice, isDigit = True, reset=True)
            partition_size = utils.user_choice('分区大小: ', lambda addr: addr is not None and addr >= 0x0 , choice, isDigit = True, reset=True)
            g_serial_verify([{'addr': partition_addr, 'size': partition_size}])

        elif choice == 'l':
            logger.LOGB("正在进行烧录lpk资源操作…")
            g_serial_burn_lpk()  
            logger.LOGB("正在进行lpk资源分区校验…")
            g_serial_verify_lpk_partion()
        elif choice == 'bf':
            logger.LOGB('正在烧录Flashboot…')
            g_serial_burn_partition('flashboot')
        elif choice == 'bm':
            logger.LOGB('正在烧录master…')
            g_serial_burn_partition('master')
        elif choice == 'br':
            logger.LOGB('正在烧录respak…')
            g_serial_burn_partition('respak')
        elif choice == 'bz':
            logger.LOGB('正在烧录zero…')
            g_serial_burn_partition('zero')
        elif choice == 'rb':
            logger.LOGB('正在重启…')
            g_serial_reboot()
        elif choice == 'cb':
            logger.LOGB(f'current baudrate: {g_serial_baudrate}')
        elif choice == 'detect':
            g_serial_detect()
        elif choice == 'b' or choice == 'break':
            exit_app()
        else:
            print(f'[invaid]: {choice}')
        choice=''
        time.sleep(1)

    # thread.join()
    # for item in global_output_directory.keys():
    #     if 'dir' in global_output_directory.get(item).keys():
    #         utils.dirs(global_output_directory.get(item).get('dir'))

   

def version_print():
    description = '''
Version: v1.0\n 
Time: 2021/8/17\n  
Author: theirrycao\n
RELEASE:\n
支持CSK串口烧录，默认烧录固定分区地址的资源

'''
    description = logger.get_yellow_text(description)
    return description

def parse_user_choice():
    import argparse
    args = None
    try:
        parser = argparse.ArgumentParser(description='欢迎使用CSK串口固件烧录工具')
        # parser.add_argument("-c", type=int, choices=[1,2], help="芯片类型[1:300x 2:4002][已废弃，使用默认资源，不支持修改]")
        # parser.add_argument("-baudrate", type=int, choices=[9600, 115200, 921600, 1536000, 3000000, 460800], help="波特率")
        parser.add_argument("-baudrate", type=int, choices=[9600, 115200, 921600, 1536000, 3000000, 460800], help="波特率")
        parser.add_argument("--i", dest="interact", action='store_true', help="进入交互模式")
        parser.add_argument("--g", dest="graphviz", action='store_true', help="图形化绘制")
        parser.add_argument("--d", dest="debug", action='store_true', help="调试模式，打印更多交互日志")
        parser.add_argument("-v", "--verify", dest="verify", nargs='+', help="校验分区md5sum")
        parser.add_argument("--detect", dest = 'detect', action='store_true', help="监测串口")
        parser.add_argument("-p", dest="port", type=str, help="串口端口")
        parser.add_argument("-b", type=str, help="burner资源")
        parser.add_argument("-f", type=str, help="flashboot资源")
        parser.add_argument("-m", type=str, help="master资源")
        parser.add_argument("-r", type=str, help="respak资源")
        parser.add_argument("-z", type=str, help="zero资源")
        parser.add_argument("-l", type=str, help="lpk资源")
        parser.add_argument("-version", action="version", version=version_print())
        
        args = parser.parse_args()
        # print(args)
        # args = parser.parse_args(choice.split())
    except Exception as e:
        logger.LOGE(e)

    finally:
        return args if args else None

def unzip_file(zip_src, dst_dir):
    import zipfile
    r = zipfile.is_zipfile(zip_src)
    if r:
        fz = zipfile.ZipFile(zip_src, 'r')
        for file in fz.namelist():
            fz.extract(file, dst_dir)
    else:
        logger.LOGE('This is not zip')

def g_serial_verify_lpk_partion():
    global g_burn_resource_dict
    partition_info = []
    logger.LOGI('g_burn_resource_dict:', g_burn_resource_dict)
    for item in g_burn_resource_dict.keys():
        if 'size' in g_burn_resource_dict.get(item).keys() and 'addr' in g_burn_resource_dict.get(item).keys():
            if g_burn_resource_dict.get(item).get('size') > 0 and g_burn_resource_dict.get(item).get('addr') != '':
                partition_info.append({'size': g_burn_resource_dict.get(item).get('size'), 'addr': g_burn_resource_dict.get(item).get('addr')})
    if partition_info:
        g_serial_verify(partition_info)

def load_lpk_resource(lpk_file):
    global g_burn_resource_dict
    dst_dir = '.lpk'
    unzip_file(lpk_file, dst_dir)
    manifest_file = ''
    manifest_result = utils.find_file_by_fileName(dst_dir, 'manifest.json')
    if isinstance(manifest_result, list) and len(manifest_result) == 1:
        manifest_file = manifest_result[0]
    else:
        logger.LOGE('manifest.json 存在异常 {}'.format(manifest_result) )
        return False


    burn_resource_dict = utils.read_from_json_file_as_dict(manifest_file)
    if 'images' in burn_resource_dict.keys():
        burn_resource_dict = burn_resource_dict.get('images')
        for key in burn_resource_dict.keys():
            g_burn_resource_dict[key] = burn_resource_dict.get(key)
            g_burn_resource_dict[key]['file'] = os.path.join(os.path.dirname(manifest_file), g_burn_resource_dict[key]['file'])
            g_burn_resource_dict[key]['size'] = os.path.getsize(g_burn_resource_dict[key]['file'])
            if isinstance(g_burn_resource_dict[key]['addr'], str) and g_burn_resource_dict[key]['addr']:
                # print(g_burn_resource_dict[key])
                # print(g_burn_resource_dict[key]['addr'].strip('0x'))
                g_burn_resource_dict[key]['addr'] = int(g_burn_resource_dict[key]['addr'].replace('0x',''), 16)
    return True


def init_burn_resource():
    global g_burn_resource_dict
    g_burn_resource_dict = {'burner': {'addr': 0x0, 'file': '', 'size': 0},\
            'flashboot': {'addr': 0x0, 'file': '', 'size': 0},\
            'master': {'addr': 0x10000, 'file': '', 'size': 0},\
            'respak': {'addr': 0x100000, 'file': '', 'size': 0},\
            'zero': {'addr': 0x3ff000, 'file': '', 'size': 0}
                            }

    if getattr(sys, 'frozen', False): #是否Bundle Resource
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    g_burn_resource_dict['burner']['file'] = os.path.join(base_path, os.path.join('res','burner.img'))



def is_resource_exist(argv):
    global g_burn_resource_dict, default_baud_rate, g_serial_interaction_dump_dbg
    global g_resource_burn_lpk

    lambda_is_file_exist = lambda f: f and os.path.isfile(f)

    if not argv:
        return False

    if argv.baudrate:
        default_baud_rate = argv.baudrate
    if argv.debug:
        g_serial_raw_dump_dbg = True
        g_serial_interaction_dump_dbg = True

    if lambda_is_file_exist(argv.l):
        ret = load_lpk_resource(argv.l)
        if ret:
            g_resource_burn_lpk = argv.l
        return ret

    # if not (lambda_is_file_exist(argv.f) or \
    #         lambda_is_file_exist(argv.m) or \
    #         lambda_is_file_exist(argv.r) ):
    #     logger.LOGE('Partition resource is not exist!')
    #     return False

    if argv.b:
        g_burn_resource_dict['burner']['file'] = argv.b
    if argv.f:
        g_burn_resource_dict['flashboot']['file'] = argv.f
    if argv.m:
        g_burn_resource_dict['master']['file'] = argv.m
    if argv.r:
        g_burn_resource_dict['respak']['file'] = argv.r
    if argv.z:
        g_burn_resource_dict['zero']['file'] = argv.z

    return True

def entrance_main():

    argv = parse_user_choice()
    init()
    init_burn_resource()
    if not is_resource_exist(argv):
        return
    #logger.LOGI(argv)
    app_main(argv)
    if argv.graphviz:
        logger.LOGI('draw_graphviz begain...')
        draw_graphviz()
        return
    result = command_action(argv)
    if not result or argv.interact:
        command_menu(argv)

    exit_app()

def draw_entrance():
    '''
    init()
    init_burn_resource()
    argv = parse_user_choice()
    if not is_resource_exist(argv):
        return
    app_main(argv)
    '''
    argv = parse_user_choice()
    command_menu(argv)

def draw_graphviz():
#if __name__ == '__main__':
    config = Config()
    # 关系图中包括(include)哪些函数名。
    #如果是某一类的函数，例如类gobang，则可以直接写'gobang.*'，表示以gobang.开头的所有函数。（利用正则表达式）。
    '''
    config.trace_filter = GlobbingFilter(include=[
        'test',
        'init',
        'init_burn_resource',
        'entrance_main',
        'app_main',
        'is_resource_exist',
        'load_lpk_resource',
        'unzip_file',
        'parse_user_choice',
        'command_menu',
        'serial_burn_image',
        'command_prompt',
        'serial_burn_status_show',
        'g_serial_reboot',
        'serial_enter',
        'serial_connect',
        'g_serial_burn_lpk',
        'g_serial_burn_partition',
        'burn_image',
        'getmd5'
    ])
    '''
    # 该段作用是关系图中不包括(exclude)哪些函数。(正则表达式规则)
    config.trace_filter = GlobbingFilter(exclude=[
            '_*',
         'pycallgraph.*',
         '*.secret_function',
         'FileFinder.*',
         'ModuleLockManager.*',
         'SourceFilLoader.*'
     ])
    graphviz = GraphvizOutput()
    graphviz.output_file = 'graph.png'
    try:
        with PyCallGraph(output=graphviz, config=config):
            draw_entrance()
            logger.LOGI('draw_graphviz end')
    except Exception as err:
        logger.LOGE(f'{err}')
    finally:
        logger.LOGI('draw_graphviz finally ends')

if __name__ == '__main__':
    entrance_main()
    #draw_graphviz()
