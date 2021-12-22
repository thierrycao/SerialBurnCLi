# -*- coding:utf-8 -*-
##########################################################################
# File Name: csk_read_thread.py
# Author: ThierryCao
# mail: iamthinker@163.com
# Created Time: 日 11/ 7 21:56:55 2021
#########################################################################
from serial import Serial
import serial
import threading
from plugins import logger as logger
from plugins import utils as utils
import os
import time



class ReadSerialThread(threading.Thread):
    def __init__(self, serial_raw_dump_dbg, com = None, thread_id = 0, name = 'usbserial', serial_instance = None):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.serial = None
        self.serial_is_open = False
        self.serial_com = com
        self.serial_raw_dump_dbg = serial_raw_dump_dbg
        self.preset_output_dir='output'
        self.output_dir='output'
        self.end_read = False
        self.lock = threading.RLock()

        if serial_instance == None:
            self.init_serial(com = self.serial_com)
        else:
            self.serial = serial_instance

        self.is_running = False

        self.com_msg = []
        
        

    def init_serial(self, com = None, baud=115200):
        global g_serial_baudrate

        while com == None:
            com_list = self.get_serial_ports()
            #logger.LOGI('串口监测结果:{}'.format(com_list))
            if com_list:
                if len(com_list) > 1:
                    com_is_only = lambda f: f is not None and f >=0 and f < len(com_list)
                    choice = None
                    com = utils.user_choice('{} {}'.format(utils.table_prompt(com_list) , '\n选择需要的串口号: '), com_is_only, choice, isDigit = True) 
                    com = int(com)
                    com = com_list[com]
                    #print('com:', com)
                else:
                    com = com_list[0]
                self.serial_com = com
                break
            else:
                utils.wait_rotate(header = '请插入串口设备', wait = True, cond_lambda = self.get_serial_ports ) 
        self.lock.acquire()
        if self.serial and ( not self.serial_is_open ):
            self.deinit_serial()
            
        logger.LOGB(f'初始化串口>> 端口:{com}, 波特率:{baud}')
        self.serial = Serial(com, baud, timeout=0.1)
        self.serial_is_open = True
        self.lock.release()

        g_serial_baudrate = baud


    def deinit_serial(self):
        if self.serial and self.serial_is_open:
            logger.LOGB('deinit_serial>>')
            self.serial_is_open = False
            self.com = None
            self.lock.acquire()
            self.serial.close()
            self.lock.release()
            
        
    def get_serial_ports(self):
        import serial.tools.list_ports as list_ports
        plist = list(list_ports.comports())
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
        if self.serial:
            return True
        else:
            return False

    def mark_start(self):
        self.is_running = True

    def mark_stop(self):
        self.is_running = False
    
    def notice_end_read(self):
        self.end_read = True

    def run(self):
        # com = self.com
        tmp_msg = ''

        name = self.name
        if not self.output_dir:
            self.output_dir = self.preset_output_dir
        log_file = os.path.join(self.output_dir, 'log', 'device_log', f'serial_1.log')
        utils.dirs(os.path.dirname(log_file))
        # log_file = os.path.join(output_dir, 'log', 'device_log', f'serial_{com}_{name}.log')
        index = 0
        time_stamp = 0
        with open(log_file, 'wb+') as file:
            while not self.end_read and self.is_running:
                try:
                    if self.serial and self.serial.isOpen() and self.serial_is_open:
                        self.lock.acquire()
                        if self.serial_is_open:
                            tmp_msg = self.serial.read_all()
                            #tmp_msg = self.serial.readline()
                        else:
                            tmp_msg = ''
                        self.lock.release()
                        # self.com_msg += str(tmp_msg, 'utf8')
                        
                        if tmp_msg:
                            tmp_msg_hex = list(bytearray.fromhex( tmp_msg.hex() ))
                            # print('111', tmp_msg_hex, type(tmp_msg_hex))

                            if self.serial_raw_dump_dbg:
                                logger.LOGI('ReadSerialThread:')
                                logger.print_hex(tmp_msg_hex)

                            if isinstance(tmp_msg_hex, list):
                                self.com_msg.extend(tmp_msg_hex)
                        else:
                            time.sleep(0.01)
                            '''
                            time_stamp += 1
                            if time_stamp >= 500:
                                time_stamp = 0
                                index = 0
                            elif int(time_stamp%50) == 0:
                                index += 1
                                #print('time_stamp:', index)
                            '''
                    else:
                        time.sleep(0.01)
                        time_stamp += 1
                        if time_stamp >= 500:
                            time_stamp = 0
                            index = 0
                        elif int(time_stamp%50) == 0:
                            index += 1
                            logger.LOGW('\rserial is not open', end='')
                    # file.write(tmp_msg)
                    # file.flush()
                    # os.fsync(file.fileno())

                except Exception as err:
                    logger.LOGW(err, self.serial_is_open)
                    self.notice_end_read()
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
