# -*- coding:utf-8 -*-
#*************************************************************************
#	> File Name: LSFactoryPacker.py
#	> Author: ThierryCao
#	> Mail: sycao@listenai.com
#	> Created Time: Thu 13 Mar 2021 12:54:08 PM CST
# ************************************************************************

import os, sys, hashlib, signal, shutil, time
sys.path.append("..") 
from plugins import utils as utils
from plugins import logger as logger
from serial import Serial
import serial
import serial.tools.list_ports
import thread_pool
import threading
from tqdm import tqdm

g_serial_raw_dump_dbg = False
g_serial_interaction_dump_dbg = False
g_serial_baudrate = 115200

g_serial_print_funcname_dbg = False

g_serial_status = 'uninit'



serial_instances=[]
preset_output_dir='output'
output_dir='output'
default_baud_rate=115200

global_big_end = 'little'

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

def exit_app(_signum = 0, _frame = 0):
    import traceback
    try:
        # 等一等子线程销毁
        # time.sleep(0.5)
        global end_read,gSerialInstance

        if gSerialInstance:
            gSerialInstance.deinit_serial()
        end_read=True
        sys.exit(1)
    except:
        # traceback.print_exc()
        os._exit(0)

def init():
    signal.signal(signal.SIGINT, exit_app)
    signal.signal(signal.SIGTERM, exit_app)


def is_little_endian():
    global global_big_end
    return True if global_big_end == 'little' else False




def init_serial():
    """初始化串口
    """
    serial_instance = None
    # logger.LOGI(f"初化串口成功：{port}")
    try:
        serial_instance = ReadSerialThread()
        serial_instance.start()
        serial_instance.mark_start()
        # serial_instances.append(serial_instance)
        thread_pool.put_thread(serial_instance)
    except Exception as err:
        logger.LOGE("初始化串口失败 {}".format(err))
        exit_app(1, 0)
    finally:
        return serial_instance


end_read=False

class ReadSerialThread(threading.Thread):
    def __init__(self, thread_id = 0, name = 'usbserial', serial_instance = None):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.serial = None
        self.serial_is_open = False
        self.lock = threading.RLock()

        if serial_instance == None:
            self.init_serial()
        else:
            self.serial = serial_instance

        self.is_running = False

        self.com_msg = []
        
        

    def init_serial(self, com = None, baud=115200):
        global g_serial_baudrate
        if com == None:
            com = self.get_serial_ports()[0]
        self.lock.acquire()
        if self.serial and isinstance(self.serial, serial.serialposix.Serial) and ( not self.serial_is_open ):
            self.deinit_serial()
            
        logger.LOGB(f'init_serial>> com:{com}, baud:{baud}')
        self.serial = Serial(com, baud, timeout=0.1)
        self.serial_is_open = True
        self.lock.release()

        g_serial_baudrate = baud


    def deinit_serial(self):
        if self.serial and isinstance(self.serial, serial.serialposix.Serial) and self.serial_is_open:
            logger.LOGB('deinit_serial>>')
            self.serial_is_open = False
            self.lock.acquire()
            self.serial.close()
            self.lock.release()
            
        
    def get_serial_ports(self):
        plist = list(serial.tools.list_ports.comports())
        portList = list()
        # print([ i[0] for i in plist])
        for port in plist:
            if utils.get_platform_system() == 'darwin':
                if '/dev/cu.usbserial' in port[0]:
                    portList.append(port[0])
            else:
                portList.append(port[0])
        return portList

    def reload(self, baud = 115200):
        logger.LOGB(f'reload>>  baud:{baud}')

        self.deinit_serial()
        self.init_serial(None, baud)
        if self.serial and isinstance(self.serial, serial.serialposix.Serial):
            return True
        else:
            return False

    def mark_start(self):
        self.is_running = True

    def mark_stop(self):
        self.is_running = False

    def run(self):
        global end_read, start_time, preset_output_dir, output_dir
        # com = self.com
        tmp_msg = ''

        name = self.name
        if not output_dir:
            output_dir = preset_output_dir
        log_file = os.path.join(output_dir, 'log', 'device_log', f'serial_1.log')
        utils.dirs(os.path.dirname(log_file))
        # log_file = os.path.join(output_dir, 'log', 'device_log', f'serial_{com}_{name}.log')
        with open(log_file, 'wb+') as file:
            while not end_read and self.is_running:
                try:
                    if self.serial and isinstance(self.serial, serial.serialposix.Serial) and self.serial.isOpen() and self.serial_is_open:
                        self.lock.acquire()
                        if self.serial_is_open:
                            tmp_msg = self.serial.readline()
                        else:
                            tmp_msg = ''
                        self.lock.release()
                        # self.com_msg += str(tmp_msg, 'utf8')
                        
                        if tmp_msg:
                            tmp_msg_hex = list(bytearray.fromhex( tmp_msg.hex() ))
                            # print('111', tmp_msg_hex, type(tmp_msg_hex))

                            if g_serial_raw_dump_dbg:
                                logger.LOGI('ReadSerialThread:')
                                logger.print_hex(tmp_msg_hex)

                            if isinstance(tmp_msg_hex, list):
                                self.com_msg.extend(tmp_msg_hex)
                        else:
                            time.sleep(0.01)
                    else:
                        time.sleep(0.01)
                    # file.write(tmp_msg)
                    # file.flush()
                    # os.fsync(file.fileno())

                except Exception as err:
                    logger.LOGW(err, self.serial_is_open)
                    end_read = True
                    # time.sleep(0.01)

                

    def write(self, msg):
        if self.serial and msg:
            if isinstance(msg, str):
                self.serial.write(f'{msg}\n'.encode('utf-8'))
            elif isinstance(msg, list):
                self.serial.write(bytes(msg))
            self.serial.flush()

    def read(self):
        temp_com_msg = list(self.com_msg)
        return temp_com_msg

    def swap(self):
        self.com_msg = []


class CSKBurnProtolClient():
    def __init__(self, serialInstance):
        self.serialInstance = serialInstance
        self.attach()

    def attach(self):

        self.DIR_REQ = 0x00
        self.DIR_RES = 0x01

        self.CMD_FLASH_BEGIN = 0x02                                                                                                                               
        self.CMD_FLASH_DATA =  0x03                                                                                                                                
        self.CMD_FLASH_END = 0x04                                                                                                                                 
        self.CMD_MEM_BEGIN = 0x05                                                                                                                                 
        self.CMD_MEM_END = 0x06                                                                                                                                
        self.CMD_MEM_DATA = 0x07                                                                                                                                 
        self.CMD_SYNC = 0x08                                                                                                                                    
        self.CMD_READ_REG = 0x0a                                                                                                                               
        self.CMD_CHANGE_BAUDRATE = 0x0f                                                                                                             
        self.CMD_SPI_FLASH_MD5 = 0x13                                                                                                                       
        self.CMD_FLASH_MD5_CHALLENGE = 0xF2

        self.TIMEOUT_DEFAULT = 200
        self.TIMEOUT_MEM_DATA = 500
        self.TIMEOUT_FLASH_DATA = 1000
        self.TIMEOUT_FLASH_MD5SUM = 5000                                                                                             
                                                                                                                                                                
        self.CHECKSUM_MAGIC = 0xef                                                                                                                           
        self.CHECKSUM_NONE = 0

        self.csk_command_t = {'direction':'', 'command': 0, 'size':0, 'checksum':0 }
        self.csk_response_t = {'direction':'', 'command': 0, 'size':0, 'value':0 }

        self.RAM_BLOCK_SIZE = 0x800
        self.FLASH_BLOCK_SIZE = 0x1000
        self.STATUS_BYTES_LEN = 2
        self.CSK_CMD_LEN = 1 + 1 + 2 + 4
        self.CSK_CMD_DATA_HEAD_LEN = 4
        self.MAX_REQ_COMMAND_LEN = self.CSK_CMD_LEN + self.CSK_CMD_DATA_HEAD_LEN
        self.MAX_REQ_PAYLOAD_LEN = self.FLASH_BLOCK_SIZE
        self.MAX_REQ_RAW_LEN = self.MAX_REQ_COMMAND_LEN + self.MAX_REQ_PAYLOAD_LEN
        self.MAX_REQ_SLIP_LEN = self.MAX_REQ_RAW_LEN * 2

        self.MAX_RES_READ_LEN = 512
        self.MAX_RES_SLIP_LEN = self.MAX_RES_READ_LEN * 2

        self.MD5_LEN = 16

    def serial_read(self):
        return self.serialInstance.read()
    def serial_swap(self):
        return self.serialInstance.swap()

    def serial_write(self, data):
        # write_data = bytes(data)
        self.serialInstance.write(data)
    
    def BLOCKS(self, size, block_size):
        return int((size + block_size - 1) / block_size)

    def set_request_hdr(self, data, option, in_chk):
        req_hdr = dict(self.csk_command_t)
        req_hdr['direction'] = self.DIR_REQ
        req_hdr['command'] = option
        req_hdr['size'] = len(data)
        req_hdr['checksum'] = in_chk
        return req_hdr

    def get_bytes_hex_list(self, data, len):
        out = []
        for i in range(len):
            out.append( (data >> (8 * i) ) & 0xFF )
        return out

    def get_hex_from_list(self, data):
        lens = len(data)
        out_data = 0
        for i in range(lens):
            out_data += data[i] << (8 * i) 
        return out_data

    def get_req_raw_data(self, req_hdr, req_data):
        
        req_raw_buf = []
        req_raw_buf.append(req_hdr.get('direction'))
        req_raw_buf.append(req_hdr.get('command'))
        req_raw_buf.extend(self.get_bytes_hex_list(req_hdr.get('size'), 2))
        req_raw_buf.extend(self.get_bytes_hex_list(req_hdr.get('checksum'), 4))

        if isinstance(req_data, list):
            req_raw_buf.extend(req_data)
        elif isinstance(req_data, int):
            req_raw_buf.append(req_data)
        else:
            logger.LOGE('get_req_raw_data: err, not support {}'.format(type(req_data)))
            
        return req_raw_buf
    
    def parse_response(self, data, key):
        response_map = {'direction': {'pos':0, 'lens': 1}, \
                        'command': {'pos':1, 'lens':1}, \
                        'size': {'pos':2, 'lens':2}, \
                        'value': {'pos':4, 'lens': 4}, \
                        'error': {'pos': 8, 'lens': 1}, \
                        'status': {'pos': 9, 'lens': 1}, \
                        'md5': {'pos': 10, 'lens': 16}
                        }
        ret_data = 0
        if key and key in response_map.keys():
            if ( response_map.get(key).get('pos') > len(data) -1 ) or ( response_map.get(key).get('pos') + response_map.get(key).get('lens') -1  > len(data) -1 ):
                logger.LOGE(f'parse_response: [{key}], pos or lens is over')
            else:
                spec_data_list = data[response_map.get(key).get('pos'): response_map.get(key).get('pos') + response_map.get(key).get('lens')]
                ret_data = self.get_hex_from_list(spec_data_list)

        return ret_data

    def get_req_command(self, option):
        request_map = {'FLASH_BEGIN': 0x02,\
                        'FLASH_DATA': 0x03, \
                        'FLASH_END': 0x04, \
                        'MEM_BEGIN': 0x05, \
                        'MEM_END': 0x06, \
                        'MEM_DATA': 0x07, \
                        'SYNC': 0x08, \
                        'READ_REG': 0x0a, \
                        'CHANGE_BAUDRATE': 0x0f, \
                        'SPI_FLASH_MD5': 0x13, \
                        'ERASE_FLASH': 0xd0,\
                        'FLASH_MD5_CHALLENGE': 0xF2
                        }
        if isinstance(option, int):
            for item in request_map.keys():
                if option == request_map.get(item):
                    return item
        elif isinstance(option, str):
            if option in request_map.keys():
                return request_map.get(option)
            else:
                logger.LOGE(f'get_req_command error, {option}')
                return 0
        else:
            logger.LOGE('get_req_command not support this style {}'.format(type(option)))

    def generate_response_head(self):
        header = []
        response_map = {'direction': {'pos':0, 'lens': 1}, \
                        'command': {'pos':1, 'lens':1}, \
                        'size': {'pos':2, 'lens':2}, \
                        'value': {'pos':4, 'lens': 4}, \
                        'error': {'pos': 8, 'lens': 1}, \
                        'status': {'pos': 9, 'lens': 1}, \
                        'md5': {'pos': 10, 'lens': 16}
                        }
        for key in response_map.keys():
            if response_map.get(key).get('lens') == 1:
                header.append(key[0:3])
            elif response_map.get(key).get('lens') > 1:
                header.append(key[0:3])
                header.extend(['---']* (response_map.get(key).get('lens') -1) )
        
        return header

    def interact_data_dump(self, interact_type, data):
        if g_serial_interaction_dump_dbg:
            if interact_type == 'req':
                logger.LOGI('write req_slip_buf: ')
                logger.print_hex(data)
            elif interact_type == 'res':
                logger.LOGI('read res_raw_buf: ', )
                logger.print_hex(data, head= self.generate_response_head() )

    def command(self, command, data, in_chk, timeout = 0.2):

        res_ret = { 'ret': False,
                    'res_ret': {'error': [], 'code': 0, 'value': [], 'size': 0, 'md5': []}
                   }
        req_hdr = self.set_request_hdr(data, command, in_chk)

        #req_hdr
        #req_cmd
        req_raw_buf = self.get_req_raw_data(req_hdr, data)
        req_slip_buf = self.slip_encode(req_raw_buf)

        self.interact_data_dump('req', req_slip_buf)
        
        self.serial_write(req_slip_buf)

        # 10毫秒之后读取结果
        time.sleep(0.01)

        while True:
            res_slip_buf = self.serial_read()
            if res_slip_buf and len(res_slip_buf) >= 10 + 2:
                self.serial_swap()
                # print('time wasting:', timeout)
                break
            elif (not res_slip_buf) and timeout <= 0:
                # print('timeout:', timeout)
                return res_ret

            timeout -= 0.01
            time.sleep(0.01)

        res_raw_buf = self.slip_decode(res_slip_buf)

        
        # print(self.generate_response_head())
        self.interact_data_dump('res', res_raw_buf)
        

        ret_direction = self.parse_response(res_raw_buf, 'direction')
        ret_command = self.parse_response(res_raw_buf, 'command')
        ret_value = self.parse_response(res_raw_buf, 'value')
        ret_size = self.parse_response(res_raw_buf, 'size')

        res_ret['res_ret']['error'] = self.parse_response(res_raw_buf, 'error')
        res_ret['res_ret']['code'] = self.parse_response(res_raw_buf, 'status')
        res_ret['res_ret']['value'] = ret_value
        res_ret['res_ret']['size'] = ret_size

        if (ret_size == 2 + 16) and command == self.get_req_command('FLASH_MD5SUM'):
            res_ret['res_ret']['md5'] = self.parse_response(res_raw_buf, 'md5')
        
        if ret_command == command and ret_direction == self.DIR_RES:
            res_ret['ret'] = True

        return res_ret

    def check_command(self, command, data, in_chk, timeout=0.2):

        ret = self.command(command, data, in_chk, timeout)
        if not ret.get('ret'):
            # return False
            return 0xFE
        if len(ret.get('res_ret')) < 2:
            logger.LOGE('错误: 指令 %02X 串口读取异常' %command)
            # return False
            return 0xFF
        if ret.get('res_ret').get('error'):
            logger.LOGE('错误: 指令 %02X 设备返回异常 0x%02X' %(command, ret.get('res_ret').get('code')))
        elif command == self.get_req_command('READ_REG'):
            return ret.get('res_ret').get('value')

        elif command == self.get_req_command('FLASH_DATA'):
            return ret

        else:
            # return True
            return 0x00
    def print_funcname(fn):
        def wrapper(*arg, **kw):
            if g_serial_print_funcname_dbg:
                logger.LOGB('%s' % fn.__name__)
            return fn(*arg, **kw)
        return wrapper

    @print_funcname
    def cmd_sync(self, timeout = 0.01):
        # logger.LOGB('cmd_sync')
        cmd = [0x07, 0x07, 0x12, 0x20]
        cmd.extend([ 0x55 ] * 32)
        return self.command(self.get_req_command('SYNC'),  cmd, 0, 0.5).get('ret')

    @print_funcname
    def cmd_read_reg(self, reg):
        cmd = self.get_bytes_hex_list(reg, 4)
        return self.check_command(self.get_req_command('READ_REG'),cmd, 0) 

    @print_funcname
    def cmd_mem_begin(self, size, blocks, block_size = 0, offset = 0):

        size = self.get_bytes_hex_list(size, 4)
        blocks = self.get_bytes_hex_list(blocks, 4)
        block_size = self.get_bytes_hex_list(block_size, 4)
        offset = self.get_bytes_hex_list(offset, 4)

        cmd = size + blocks + block_size + offset

        return True if self.check_command(self.get_req_command('MEM_BEGIN'),cmd, 0) == 0x00 else False

    @print_funcname
    def cmd_mem_block(self, data, data_len, seq):
        size = self.get_bytes_hex_list(data_len, 4)
        seq = self.get_bytes_hex_list(seq, 4)
        rev1 = self.get_bytes_hex_list(0, 4)
        rev2 = self.get_bytes_hex_list(0, 4)
        cmd = size + seq + rev1 + rev2 + data

        return True if self.check_command(self.get_req_command('MEM_DATA'), cmd, self.checksum(data), 0.5) == 0x00 else False

    @print_funcname
    def cmd_mem_end(self):

        OPTION_REBOOT = 0
        option = self.get_bytes_hex_list(OPTION_REBOOT, 4)
        address = self.get_bytes_hex_list(0, 4)
        cmd = option + address

        return True if self.check_command(self.get_req_command('MEM_END'), cmd, 0) == 0x00 else False

    @print_funcname
    def cmd_flash_begin(self, size, blocks, block_size, offset, md5):

        MD5_LEN = 16

        size = self.get_bytes_hex_list(size, 4)
        blocks = self.get_bytes_hex_list(blocks, 4)
        block_size = self.get_bytes_hex_list(block_size, 4)
        offset = self.get_bytes_hex_list(offset, 4)
        md5 = self.get_bytes_hex_list(md5, MD5_LEN)

        cmd = size + blocks + block_size + offset + md5

        return True if self.check_command(self.get_req_command('FLASH_BEGIN'), cmd, self.checksum(md5)) == 0x00 else False 

    @print_funcname
    def cmd_flash_block(self, data, data_len, seq):
        seq_rel = int(seq)

        size = self.get_bytes_hex_list(data_len, 4)
        seq = self.get_bytes_hex_list(seq, 4)
        rev1 = self.get_bytes_hex_list(0, 4)
        rev2 = self.get_bytes_hex_list(0, 4)
        cmd = size + seq + rev1 + rev2 + data

        ret = self.check_command(self.get_req_command('FLASH_DATA'), cmd, self.checksum(data), 1)
        if ret.get('res_ret').get('error') != 0x00:
            logger.LOGE('错误: 数据块 %d 写失败: %02X' %(seq_rel, ret.get('res_ret').get('error')))
        if ret.get('res_ret').get('error') == 0x0A:
            time.sleep(0.5)
        return ret
        # return True if ret == 0x00 else False
    @print_funcname
    def cmd_flash_finish(self):

        OPTION_REBOOT = 0
        option = self.get_bytes_hex_list(OPTION_REBOOT, 4)
        address = self.get_bytes_hex_list(0, 4)
        cmd = option + address

        return True if self.check_command(self.get_req_command('FLASH_END'), cmd, 0) == 0x00 else False

    @print_funcname
    def cmd_flash_md5sum(self, address, size):

        
        address = self.get_bytes_hex_list(address, 4)
        size = self.get_bytes_hex_list(size, 4)
        rev1 = self.get_bytes_hex_list(0, 4)
        rev2 = self.get_bytes_hex_list(0, 4)
        cmd = address + size + rev1 + rev2 
        ret = self.command(self.get_req_command('SPI_FLASH_MD5'),  cmd, 0, 5)
        if not ret.get('ret'):
            return ''
        if ret.get('res_ret').get('size') < 2:
            logger.LOGE('错误: 串口读取异常')
            return ''
        if ret.get('res_ret').get('error') != 0:
            logger.LOGE('错误: 设备返回异常 %02X%02X' %(ret.get('res_ret').get('error'), ret.get('res_ret').get('status')) )
        return self.intList2hexString(ret.get('res_ret').get('md5'))

    @print_funcname
    def cmd_flash_md5_challenge(self):

        return True if self.check_command(self.get_req_command('FLASH_MD5_CHALLENGE'), [], 0, 5) == 0x00 else False 

    @print_funcname
    def cmd_change_baud(self, baud):

        cmd = self.get_bytes_hex_list(baud, 4)
        ret = self.command(self.get_req_command('CHANGE_BAUDRATE'),  cmd, 0, 1)
        if not ret.get('ret'):
            return False

        return self.serialInstance.reload(baud)

    def checksum(self, data):
        CHECKSUM_MAGIC = 0xef
        state = CHECKSUM_MAGIC

        for item in data:
            state = state ^ item

        return state
    def intList2hexString(self, int_list):
        import binascii
        if not int_list:
            return ''

        return binascii.b2a_hex(str(bytearray(int_list)))

    def str2hex(self, input_s):
        input_s = input_s.strip()
        send_list = []
        while input_s != '':
            try:
                num = int(input_s[0:2], 16)
            except ValueError as err:
                # QMessageBox.critical(self, 'wrong data', '请输入十六进制数据，以空格分开!')
                logger.LOGE(err)
                return None
            input_s = input_s[2:].strip()
            send_list.append(num)
        return send_list

    def slip_encode(self, req_raw_buf):
        END = 0xC0
        ESC = 0xDB
        ESC_END = 0xDC
        ESC_ESC = 0xDD

        req_slip_buf = [END]

        for item, value in enumerate(req_raw_buf):
            if value == END:
                req_slip_buf.append(ESC)
                req_slip_buf.append(ESC_END)
            elif value == ESC:
                req_slip_buf.append(ESC)
                req_slip_buf.append(ESC_ESC)
            else:
                req_slip_buf.append(value)

        req_slip_buf.append(END)

        return req_slip_buf

    def slip_decode(self, req_slip_buf):
        END = 0xC0
        ESC = 0xDB
        ESC_END = 0xDC
        ESC_ESC = 0xDD

        req_raw_buf = []

        for item, value in enumerate(req_slip_buf):
            if value == END and item == 0:
                continue
            if item == (len(req_slip_buf) -1) and value == END:
                # req_raw_buf.append(value)
                break
            
            if value == ESC and req_slip_buf[item+1] == ESC_END:
                req_raw_buf.append(END)
            elif value == ESC and req_slip_buf[item+1] == ESC_ESC:
                req_raw_buf.append(ESC)
            else:
                req_raw_buf.append(value)
        return req_raw_buf



def clean_com_msg(com):
    
    if com and isinstance(com, ReadSerialThread):
        com.swap()
    else:
        logger.LOGE(f'[clean_com_msg] Not Done')


def swap_serial_msg():
    if serial_instance:
        serial_instance.swap()

def read_serial_msg():
    if serial_instance:
        data = serial_instance.read()
        if data and data.strip():
            print('REC:' + data.strip().strip('\n'))
            return data.strip().strip('\n')

def write_serial_msg(msg):
    serial_instance.write(msg)

gSerialInstance = None
serial_instance = None
g_burn_resource_dict = {}

g_serial_enter = None
g_serial_connect = None
args_dict = {'loggers': []}


def task_retry(func, count, notice = '完成了', param = None, time_sep = 0.5):
    while count > 0:
        count -= 1
        if param:
            ret = func(param)
        else:
            ret = func()
        if ret == True:
            logger.LOGB('%s '%notice)
            return True
        time.sleep(time_sep)
    return False
        
def _serial_enter(instance = gSerialInstance, change_baud=True):

    global g_burn_resource_dict, gSerialInstance, g_serial_status
    if not instance:
        instance = gSerialInstance

    RAM_BLOCK_SIZE = 0x800
    burner_len = os.path.getsize(g_burn_resource_dict.get('burner').get('file'))
    blocks = instance.BLOCKS(burner_len, RAM_BLOCK_SIZE)
    if not instance.cmd_mem_begin(burner_len, blocks, RAM_BLOCK_SIZE, 0):
        logger.LOGE('cmd_mem_begin fails')
        return False

    data = utils.read_hex_from_bin(g_burn_resource_dict.get('burner').get('file'))
    offset = 0

    with tqdm(total = blocks + 1, desc= 'burner', leave = True, ncols = 100, unit='Blocks', unit_scale = True) as pbar:
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
    if change_baud:
        if not instance.cmd_change_baud(3000000):
            logger.LOGE('错误: 无法设置串口速率')
            return False
    g_serial_status = 'enter'

    return True

def _serial_enter_no_change_baud(instance = gSerialInstance, change_baud=False):
    global gSerialInstance
    if not instance:
        instance = gSerialInstance
    def _serial_enter_no_change_baud_():
        return _serial_enter(instance, change_baud)
    
    if not task_retry(_serial_enter_no_change_baud_, 4, '连接成功'):
        logger.LOGE('设备连接失败')
        return False
    else:
        return True
    
    

def g_serial_read_chipid(instance = gSerialInstance):
    global gSerialInstance, g_serial_status

    EFUSE_BASE = 0xF1800000

    if not instance:
        instance = gSerialInstance

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

    id1 = instance.cmd_read_reg(EFUSE_BASE + 0x80 + 0x0A)
    if id1 == 0x00:
        return False

    time.sleep(0.1)
    id0 = instance.cmd_read_reg(EFUSE_BASE + 0x80 + 0x0E)
    if id0 == 0x00:
        return False

    chipid = hex( (id0 << 32) | id1 ).strip('0x')

    logger.LOGB(f'chipid: {chipid}')

    return True

def getmd5(file):
    import hashlib
    m = hashlib.md5()
    with open(file,'rb') as f:
        for line in f:
            m.update(line)
    md5code = m.hexdigest()
    # return bytes.fromhex(md5code).hex()
    return int(md5code, 16)


def burn_image(addr, data, lens, md5sum, instance = gSerialInstance):
    
    global gSerialInstance
    if not instance:
        instance = gSerialInstance

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

            # 更新进度条
            pbar.update(next - index)

            index = next


    # FLASH_BLOCK_TRIES = 5
    # for i in range(FLASH_BLOCK_TRIES):
    #     if (not instance.cmd_flash_md5_challenge()) and (i == FLASH_BLOCK_TRIES -1):
    #         logger.LOGE("错误: MD5 校验失败")
    #         return False

    logger.LOGB('烧录完成')
    return True
        

    

def g_serial_burn_partition(partition):
    global g_burn_resource_dict, gSerialInstance

    if partition and partition in g_burn_resource_dict.keys():
        md5sum = getmd5(g_burn_resource_dict.get(partition).get('file'))
        addr = g_burn_resource_dict.get(partition).get('addr')
        data = utils.read_hex_from_bin(g_burn_resource_dict.get(partition).get('file'))
        lens = len(data)
        logger.LOGB('正在烧录分区 %d/%d… (0x%08X, %.2f KB)' %(0, 1, addr, lens/1024))
        burn_image(addr, data, lens, md5sum)

def g_serial_burn_lpk():
    global g_burn_resource_dict

    logger.LOGB('1.正在等待设备接入…')
    serial_connect()

    logger.LOGB("2.正在进入烧录模式…")
    serial_enter()

    logger.LOGB("3.正在读取芯片ID…")
    g_serial_read_chipid()

    for key in g_burn_resource_dict.keys():
        if key == 'burner':
            continue
        g_serial_burn_partition(key)


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
    def _serial_connect(instance = gSerialInstance):
        if not instance:
            instance = gSerialInstance
        return instance.cmd_sync()

    if not task_retry(_serial_connect, 4, '连接成功'):
        logger.LOGE('设备连接失败')
        return False
    else:
        return True

@serial_status_set
def serial_enter(instance = gSerialInstance):
    if not instance:
        instance = gSerialInstance

    if not task_retry(_serial_enter, 4, '进入烧录模式'):
        logger.LOGE('进入烧录模式失败')
        return False
    else:
        return True
            
def g_serial_reboot(instance = gSerialInstance):
    global g_serial_status
    if not instance:
        instance = gSerialInstance

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

    return True

def command_prompt():
    import prettytable as pt
    tb = pt.PrettyTable()
    tb.field_names = ["item", "名称", "快捷指令"]
    tb.add_row(["1","设备连接", "c"])
    tb.add_row(["2","进入烧录", "e"])
    tb.add_row(["3","读取chipid", "r"])
    tb.add_row(["4","烧录lpk资源", "l"])
    tb.add_row(["5","烧录flashboot", "bf"])
    tb.add_row(["6","烧录master", "bm"])
    tb.add_row(["7","烧录respak", "br"])
    tb.add_row(["8","烧录zero", "bz"])
    tb.add_row(["9","重启", "rb"])
    tb.add_row(["0","退出", "b"])
    tb.add_row(["*","查看当前波特率", "cb"])
    return tb

def app_main(argv):
    global gSerialInstance, serial_instance,  args_dict
    serial_instance = init_serial()
    # thread = threading.Thread(target=app_serial, args=[ argv.baudrate if argv.baudrate else 115200])
    # thread.start()

    choice = ''

    if serial_instance:
        gSerialInstance = CSKBurnProtolClient(serial_instance)
    else:
        logger.LOGE('not found serial device, exit!')
        return

def command_menu(argv):
    if not argv.c:
        lambda_is_file_exist = lambda f: f and os.path.isfile(f)
        if lambda_is_file_exist(argv.l):
            g_serial_burn_lpk()
        exit_app()

    while True:
        print(command_prompt())
        choice = ''
        choice = utils.user_choice('请输入:', lambda f: f is not '' and f is not None, choice)
        if choice == 'c':
            logger.LOGB('正在等待设备接入…')
            serial_connect()
        elif choice == 'e':
            serial_enter()
        elif choice == 'r':
            logger.LOGB("正在读取芯片ID…")
            g_serial_read_chipid()
        elif choice == 'l':
            logger.LOGB("即将烧录lpk资源…")
            g_serial_burn_lpk()  
        elif choice == 'bf':
            logger.LOGB('正在烧录Flashboot…')
            g_serial_burn_partition('flashboot')
        elif choice == 'bm':
            logger.LOGB('正在烧录master…')
            g_serial_burn_partition('master')
        elif choice == 'br':
            logger.LOGB('正在烧录respak…')
            g_serial_burn_partition('respak')
        elif choice == 'rb':
            logger.LOGB('正在重启…')
            g_serial_reboot()
        elif choice == 'cb':
            logger.LOGB(f'current baudrate: {g_serial_baudrate}')
            
        elif choice == 'b' or choice == 'break':
            exit_app()
        else:
            write_serial_msg(choice)
        choice=''
        time.sleep(1)

    thread.join()
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
        parser.add_argument("-baudrate", type=int, choices=[9600, 115200, 1536000, 3000000], help="波特率")
        parser.add_argument("--c", action='store_true', help="进入交互模式")
        parser.add_argument("-b", type=str, help="burner资源")
        parser.add_argument("-f", type=str, help="flashboot资源")
        parser.add_argument("-m", type=str, help="master资源")
        parser.add_argument("-r", type=str, help="respak资源")
        parser.add_argument("-z", type=str, help="zero资源")
        parser.add_argument("-l", type=str, help="lpk资源")
        parser.add_argument("-v", action="version", version=version_print())
        
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
            if isinstance(g_burn_resource_dict[key]['addr'], str) and g_burn_resource_dict[key]['addr']:
                # print(g_burn_resource_dict[key])
                # print(g_burn_resource_dict[key]['addr'].strip('0x'))
                g_burn_resource_dict[key]['addr'] = int(g_burn_resource_dict[key]['addr'].replace('0x',''), 16)


def init_burn_resource():
    global g_burn_resource_dict
    g_burn_resource_dict = {'burner': {'addr': 0x0, 'file': ''},\
                            'flashboot': {'addr': 0x0, 'file': ''},\
                            'master': {'addr': 0x10000, 'file': ''},\
                            'respak': {'addr': 0x100000, 'file': ''},\
                            'zero': {'addr': 0x3ff000, 'file': ''}
                            }

    if getattr(sys, 'frozen', False): #是否Bundle Resource
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    g_burn_resource_dict['burner']['file'] = os.path.join(base_path, os.path.join('res','burner.img'))



def is_resource_exist(argv):
    global g_burn_resource_dict

    lambda_is_file_exist = lambda f: f and os.path.isfile(f)

    # if not lambda_is_file_exist(argv.b):
    #     logger.LOGE('burner resource is not exist!')
    #     return False

    if lambda_is_file_exist(argv.l):
        load_lpk_resource(argv.l)
        return True


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

def main():
    init()
    init_burn_resource()

    argv = parse_user_choice()
    if not is_resource_exist(argv):
        return
    logger.LOGI(argv)
    app_main(argv)
    command_menu(argv)

    exit_app()


if __name__ == '__main__':
    main()