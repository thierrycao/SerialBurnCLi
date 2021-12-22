# -*- coding:utf-8 -*-
##########################################################################
# File Name: csk_burn_protocol_client.py
# Author: ThierryCao
# mail: iamthinker@163.com
# Created Time: 日 11/ 7 21:57:46 2021
#########################################################################
from plugins import logger as logger
import time
g_serial_print_funcname_dbg = False
class CSKBurnProtocolClient():
    def __init__(self, serialInstance, serial_interaction_dump_dbg, serial_print_funcname_dbg):
        self.serialInstance = serialInstance
        self.serial_interaction_dump_dbg = serial_interaction_dump_dbg
        self.serial_print_funcname_dbg = serial_print_funcname_dbg
        g_serial_print_funcname_dbg = self.serial_print_funcname_dbg
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
                if 'md5' == key:
                    spec_data_list.reverse()
                    ret_data = self.get_hex_from_list(spec_data_list)
                else:
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
    def generate_request_head(self):
        header = []
        request_map = {'direction': {'pos':0, 'lens': 1}, \
                        'command': {'pos':1, 'lens':1}, \
                        'size': {'pos':2, 'lens':2}, \
                        'value': {'pos':4, 'lens': 4}, \
                        'error': {'pos': 8, 'lens': 1}, \
                        'status': {'pos': 9, 'lens': 1}, \
                        'md5': {'pos': 10, 'lens': 16}
                        }
        for key in request_map.keys():
            if request_map.get(key).get('lens') == 1:
                header.append(key[0:3])
            elif request_map.get(key).get('lens') > 1:
                header.append(key[0:3])
                header.extend(['---']* (request_map.get(key).get('lens') -1) )
        
        return header


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

    def interact_data_dump(self, interact_type, data, notice=''):
        if self.serial_interaction_dump_dbg:
            if 'req' in interact_type:
                if  notice:
                    logger.LOGI(str(notice))
                else:
                    logger.LOGI(f'write {interact_type}: ')
                if  'slip_decode' in  interact_type:
                    logger.print_hex(data, head= self.generate_request_head())
                else:
                    logger.print_hex(data)
            elif 'res' in interact_type:
                if  notice:
                    logger.LOGI(str(notice))
                else:
                    logger.LOGI(f'read {interact_type}: ', )
                if 'slip_decode' in interact_type:
                    logger.print_hex(data, head= self.generate_response_head() )
                else:
                    logger.print_hex(data)

    def command(self, command, data, in_chk, timeout = 0.2):

        res_ret = { 'ret': False,
                    'res_ret': {'error': [], 'code': 0, 'value': [], 'size': 0, 'md5': []}
                   }
        req_hdr = self.set_request_hdr(data, command, in_chk)

        #req_hdr
        #req_cmd
        req_raw_buf = self.get_req_raw_data(req_hdr, data)
        req_slip_buf = self.slip_encode(req_raw_buf)

        self.interact_data_dump('req_slip_encode', req_raw_buf)
        self.interact_data_dump('req_slip_decode', req_slip_buf)
        
        self.serial_write(req_slip_buf)

        # 10毫秒之后读取结果
        time.sleep(0.01)
        buf = []
        while True:
            res_slip_buf = self.serial_read()
            if timeout <= 0:
                if res_slip_buf and len(res_slip_buf) >= 10 + 2:
                    self.serial_swap()
                    break
                else:
                    self.serial_swap()
                    #print('buf: ', buf)
                    return res_ret
            elif res_slip_buf and len(res_slip_buf) >= 10 + 2:
                self.serial_swap()
                break
            elif res_slip_buf and len(res_slip_buf) < 10 + 2:
                buf.extend(res_slip_buf)

            timeout -= 0.02
            time.sleep(0.02)
            #print('read:', timeout)

        self.interact_data_dump('res_slip_encode', res_slip_buf)

        res_raw_buf = self.slip_decode(res_slip_buf)

        
        # print(self.generate_response_head())
        self.interact_data_dump('res_slip_decode', res_raw_buf)
        

        ret_direction = self.parse_response(res_raw_buf, 'direction')
        ret_command = self.parse_response(res_raw_buf, 'command')
        ret_value = self.parse_response(res_raw_buf, 'value')
        ret_size = self.parse_response(res_raw_buf, 'size')

        res_ret['res_ret']['error'] = self.parse_response(res_raw_buf, 'error')
        res_ret['res_ret']['code'] = self.parse_response(res_raw_buf, 'status')
        res_ret['res_ret']['value'] = ret_value
        res_ret['res_ret']['size'] = ret_size

        if (ret_size == 2 + 16) and command == self.get_req_command('SPI_FLASH_MD5'):
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
        '''
        if ret.get('res_ret').get('error'):
            logger.LOGE('错误: 指令 %02X 设备返回异常 0x%02X' %(command, ret.get('res_ret').get('code')))
            logger.LOGE('错误: 指令 %02X 设备返回异常 ' %(command), ret)
        '''
        # 忽略res的error 
        '''
        if command == self.get_req_command('READ_REG'):
            return ret.get('res_ret').get('value')
        '''
        if ret.get('res_ret').get('error'):
            logger.LOGE('错误: 指令 %02X 设备返回异常 0x%02X' %(command, ret.get('res_ret').get('code')))
            logger.LOGE('错误: 指令 %02X 设备返回异常 ' %(command), ret)
            if command == self.get_req_command('READ_REG'):
                return ret.get('res_ret').get('value')
        elif command == self.get_req_command('READ_REG'):
            return ret.get('res_ret').get('value')

        elif command == self.get_req_command('FLASH_DATA'):
            return ret

        else:
            return (True, 0x00)
    def print_funcname(fn):
        def wrapper(*arg, **kw):
            if g_serial_print_funcname_dbg:
                logger.LOGB('%s' % fn.__name__)
            return fn(*arg, **kw)
        return wrapper

    @print_funcname
    def cmd_sync(self, timeout = 0.3):
        # logger.LOGB('cmd_sync')
        cmd = [0x07, 0x07, 0x12, 0x20]
        cmd.extend([ 0x55 ] * 32)
        return self.command(self.get_req_command('SYNC'),  cmd, 0, timeout).get('ret')

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

        return True if self.check_command(self.get_req_command('MEM_BEGIN'),cmd, 0) == (True,0x00) else False

    @print_funcname
    def cmd_mem_block(self, data, data_len, seq):
        size = self.get_bytes_hex_list(data_len, 4)
        seq = self.get_bytes_hex_list(seq, 4)
        rev1 = self.get_bytes_hex_list(0, 4)
        rev2 = self.get_bytes_hex_list(0, 4)
        cmd = size + seq + rev1 + rev2 + data

        return True if self.check_command(self.get_req_command('MEM_DATA'), cmd, self.checksum(data), 0.5) == (True,0x00) else False

    @print_funcname
    def cmd_mem_end(self):

        OPTION_REBOOT = 0
        option = self.get_bytes_hex_list(OPTION_REBOOT, 4)
        address = self.get_bytes_hex_list(0, 4)
        cmd = option + address

        return True if self.check_command(self.get_req_command('MEM_END'), cmd, 0) == (True,0x00) else False

    @print_funcname
    def cmd_flash_begin(self, size, blocks, block_size, offset, md5):

        MD5_LEN = 16

        size = self.get_bytes_hex_list(size, 4)
        blocks = self.get_bytes_hex_list(blocks, 4)
        block_size = self.get_bytes_hex_list(block_size, 4)
        offset = self.get_bytes_hex_list(offset, 4)
        md5 = self.get_bytes_hex_list(md5, MD5_LEN)

        cmd = size + blocks + block_size + offset + md5

        return True if self.check_command(self.get_req_command('FLASH_BEGIN'), cmd, self.checksum(md5)) == (True,0x00) else False 

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

        return True if self.check_command(self.get_req_command('FLASH_END'), cmd, 0) == (True,0x00) else False

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

        #return self.intList2hexString(ret.get('res_ret').get('md5'))
        return hex(ret.get('res_ret').get('md5'))

    @print_funcname
    def cmd_flash_md5_challenge(self):

        return True if self.check_command(self.get_req_command('FLASH_MD5_CHALLENGE'), [], 0, 5) == (True,0x00) else False 

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
