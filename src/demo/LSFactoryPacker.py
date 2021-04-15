# -*- coding:utf-8 -*-
#*************************************************************************
#	> File Name: LSFactoryPacker.py
#	> Author: ThierryCao
#	> Mail: sycao@listenai.com
#	> Created Time: Thu 13 Mar 2021 12:54:08 PM CST
# ************************************************************************

import os, sys, hashlib, signal, shutil
from plugins import utils as utils
from plugins import logger as logger
from plugins import lsusb as lsusb
# from plugins import keyboard as keyboard 
from plugins import console as console

global global_step
global_step = 1

def md5sum(file, form='upper'):
    if not os.path.exists(file):
        print("md5sum: {}: No such file or directory".format(file))
    
    if os.path.isdir(file):
        print("md5sum: {}: Is a directory".format(file))
    
    try:
        with open(file, 'rb') as fd:
            data = fd.read()
            return "{}".format(str(hashlib.md5(data).hexdigest()).upper() if form == 'upper' else hashlib.md5(data).hexdigest())
    except Exception as err:
        print(err)

def print_align(*args, **kargs):
    file = kargs.pop('file', sys.stdout)
    first = True
    output = ''
    for arg in args:
        # print(arg)
        # output += '{0:{1}<20}\t'.format(arg, chr(12288))   # 左对齐
        output += str(arg)
        # file.write(output)
    # print('%-30s%-20s%-20s' %(argv[0], argv[1], argv[2]))
    print(output)

def menu_choice(menu_list, notice = '搜索结果包括:'):
    if isinstance(menu_list, list):
        if not menu_list:
            return
        elif len(menu_list) == 1:
            return menu_list[0]
        else:
            for index, item in enumerate(menu_list):
                notice += f'{index+1}: {item}\n'
            notice += '请选择: '
            choice = 0
            choice = user_choice(notice, lambda x: x and utils.is_number(x) and eval(x) in [ i for i in range(1, len(menu_list) + 1) ], choice )
            return menu_list(eval(choice) -1 )

def get_partition_resource(directory_path, resource):
    if directory_path and os.path.isdir(directory_path):
        for item in resource.keys():
            if not (resource.get(item) and os.path.isfile(resource.get(item)) ):
                search_result = utils.find_file_by_fileName(directory_path, item + '.bin')
                result = menu_choice(search_result)
                if result:
                    resource[item] = result
    return resource

                


def resource_prepare(args):
    global global_step 
    def parse_args(args):
        result = {'chip':'', 'burner':'', 'flashboot': '', 'master':'', 'script':'', 'respak':''}
        # print('-----------')
        # print(args.__dict__.keys())
        for key in args.__dict__.keys():
            if args.__dict__.get(key) is not None:
                for item in result.keys():
                    if key == item[0]:
                        result[item] = str(args.__dict__.get(key))
        return result
    def init_resource():
        resource = {'burner':{'version':1001, 'file_size': 0, 'addr': '0x0', 'md5': '', 'file_path': '' }, \
                        'flashboot':{'version':1001, 'file_size': 0, 'addr': '0x0', 'md5': '', 'file_path': '' }, \
                        'master':{'version':1001, 'file_size': 0, 'addr': '0x10000', 'md5': '', 'file_path': '' }, \
                        'script':{'version':1001, 'file_size': 0, 'addr': '0xf0000', 'md5': '', 'file_path': '' }, \
                        'respak':{'version':1001, 'file_size': 0, 'addr': '0x100000', 'md5': '', 'file_path': '' }}
        return resource
    def get_import_directory(choice=None):
        global global_step
        equation = lambda x:  x and x in ['n', 'no'] or ( x and os.path.isdir(x))
        clear_flag = False if equation(choice) else True
        choice = utils.user_choice(logger.get_yellow_text(f'[{global_step}]请输入固件文件夹的导入路径, 程序会自动搜索目录下的固件资源【若无需此步请输入 [n/no] 或 [回车] 跳过】: '), equation, choice)
        if choice not in ['', 'n', 'no']:
            if clear_flag:
                console.restore_last_position(row = 0, col = 0) 
            print_align(logger.get_blue_text(f'[{global_step}]固件导入路径', intent=True), logger.get_red_text('[√]', intent=True), f'固件文件夹路径: [{str(choice)}]')
            global_step += 1
        return None if choice in ['', 'n', 'no'] else choice

    # 初始化resource
    resource = init_resource()

    # 解析args 填充result
    result = parse_args(args)
    choice = ''

    # 导入目录
    # print(args)
    # print(r'%s'%args.__dict__['i'])
    args.__dict__['i'] = get_import_directory(args.__dict__['i'])

    # 使用导入的目录填充result
    result = get_partition_resource(args.__dict__['i'], result)

    for item in resource.keys():
        choice = None
        if item in result.keys():
            choice = result[item] if result[item] else choice
            # print(choice)
        # print_align(logger.get_yellow_text(f'1',intent=True), logger.get_red_text('[√]', intent=True), '3')
        if not (choice and os.path.isfile(choice)):
            if item == 'script':
                choice = utils.user_choice(logger.get_yellow_text(f'[{global_step}][可选]请输入{item}路径【若无此资源请输入 [n/no] 或 [回车] 跳过】: '), lambda x:  x in ['', 'n', 'no'] or ( x and os.path.isfile(x)), choice)
                if choice in ['', 'n', 'no']:
                    continue
            else:
                choice = utils.user_choice(logger.get_yellow_text(f'[{global_step}][必选]请输入{item}路径: '), lambda x: x and os.path.isfile(x), choice)

            console.restore_last_position(row = 0, col = 0)
            # print('\r',end='')
            print_align(logger.get_blue_text(f'[{global_step}]{item}资源', intent=True), logger.get_red_text('[√]', intent=True), f'{item}路径: [{str(choice)}]')
            global_step += 1
        if choice in ['', 'n', 'no']:
            continue
        resource[item]['file_path'] = choice
        resource[item]['file_size'] = os.path.getsize(choice)
        md5sum_value = md5sum(choice)
        if md5sum_value:
            resource[item]['md5'] = md5sum_value
    return args, resource

def print_factory_type(factory_type):
    global global_step
    factory_type_id = {'chip':'芯片','module':'模块','invalid':'非法'}.get(factory_type)
    if factory_type in ['chip', 'module']:
        print_align(logger.get_blue_text(f'[{global_step}]烧录的类型', intent=True), logger.get_red_text('[√]', intent=True), f'类型: [{str(factory_type_id)}]')
    else:
        print_align(logger.get_blue_text(f'[{global_step}]烧录的类型', intent=True), logger.get_red_text('[x]', intent=True), f'类型: [{str(factory_type_id)}]')
    global_step += 1

def get_factory_type(args):
    
    choice = ''
    if args.__dict__.get('t'):
        choice = args.__dict__.get('t')
   
    if choice not in ['chip', 'module']:
        factory_type = 'invalid'
       
    else:
        factory_type = choice
        factory_type_id = {'chip':'芯片','module':'模块','invalid':'非法'}.get(factory_type)
        
    
    return factory_type

def get_output_path(args):
    if args.__dict__.get('o'):
        choice = args.__dict__.get('o')
    choice = utils.user_choice(logger.get_yellow_text(f'[{global_step}]请输入芯片烧录器固件保存的目录[TF卡根目录的绝对路径]: '), lambda x: x != '', choice)
    return choice

def resouce_generate(args, resource):
    def resource_tf_struct_print(args):
        if args.__dict__.get('c') == '1':
            print(logger.get_purple_text('''完整的[CSK300X]SDCard目录应该如下:
SDCard根目录/
├── castor
│   ├── burn.cfg
│   └── files
│       ├── burner.img
│       ├── flashboot.bin
│       ├── master.bin
│       ├── respak.bin
└── .factorytest
    ├── burn.cfg
    └── files
        ├── burner.img
        ├── flashboot.bin
        └── master.bin
        '''))
       
        else:
            print(logger.get_purple_text('''\n完整的[CSK4002]SDCard目录应该如下:
SDCard根目录/
├── castor
│   ├── burn.cfg
│   └── files
│       ├── burner.img
│       ├── flashboot.bin
│       ├── master.bin
│       ├── respak.bin
│       └── script.bin
└── .factorytest
    ├── burn.cfg
    └── files
        ├── burner.img
        ├── flashboot.bin
        └── master.bin
        '''))
    def resource_factory_info_print(target):
        print("\n\n>>" + logger.get_yellow_text('尊敬的开发者:'))
        print(">>" + logger.get_yellow_text('恭喜你,LSFactoryPaker打包成功!'))
        print(">>" + logger.get_yellow_text('如下为固件生成信息:\n'))


        print('>>' + f'如果'+logger.get_red_text(f'[{target}]') + f'目录不在'+ logger.get_red_text(f'[SDCard根目录]') + f'，请将' + \
            logger.get_red_text(f'[{target}]')+f'文件夹完整拷贝至'+ \
            logger.get_red_text(f'[SDCard根目录],')+ "\n>>" + f'并且保证'+logger.get_red_text(f'[.factoryTest]')+ \
            f'也在' + logger.get_red_text(f'[SDCard根目录]') + f'，方可操作芯片烧录器进行烧录!')

    def resource_factory_test_copy(relative_path, output_path, override = False):
        if getattr(sys, 'frozen', False): #是否Bundle Resource
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        src_path = os.path.join(base_path, relative_path)

        if os.path.isdir(src_path) and os.path.isdir(output_path):
            # print('[resource_factory_test_copy],src_path:', src_path)
            utils.cp_rf(src_path, output_path, forced = override)

    def resource_copy(resource, path):
        for item in resource.keys():
            # logger.LOGB(f'[拷贝] {resource.get(item).get("file_path")} => [{path}]')
            if resource[item]['file_path'] and os.path.isfile(resource[item]['file_path']):
                utils.cp_rf(resource[item]['file_path'], path, target='dir')
            
            # shutil.copy(resource[item]['file_path'], path)

    def resource_cfg_generate(resource, path):
        data = {'version': 10020, 'castor': []}
        for item in resource.keys():
            if resource[item]['file_path'] and os.path.isfile(resource[item]['file_path']):
                # 需要相对路径, 路径转为芯片烧录器指定的路径格式
                resource[item]['file_path'] = 'files/' + os.path.basename(resource[item]['file_path'])

                data['castor'].append(resource[item])
        # print(data)
        utils.write_dict_in_json_file(data, path)
        utils.add_json(path, path)

    firmware_target = 'castor'
    factory_type = ''
    factory_target = '.factorytest'
    
    factory_type = get_factory_type(args)

    
    choice = get_output_path(args)
    root_dir = choice
    print(logger.get_yellow_text('\n开始生成固件..'))
    
    firmware_abs_dir = os.path.join(root_dir, firmware_target)

    # 清理 castor目录
    if firmware_abs_dir and os.path.isdir(firmware_abs_dir):
        utils.rm_rf(firmware_abs_dir, forced=True)
    # 准备 castor目录
    utils.dirs(os.path.join(firmware_abs_dir, 'files'))
    resource_copy(resource, os.path.join(firmware_abs_dir, 'files'))
    resource_cfg_generate(resource, os.path.join(firmware_abs_dir,'burn.cfg') )

    # 准备 .factorytest目录
    factory_type = os.path.join(factory_type, factory_target)
    resource_factory_test_copy(os.path.join('res', factory_type), root_dir, override = True)

    
    print(logger.get_red_text(f'\n生成成功，可以取走读卡器了!\n\n'))

    
       

def get_inline_file_path(file_name, factory_type):
    def find_inline_file_path(relative_path):
            if getattr(sys, 'frozen', False): #是否Bundle Resource
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            src_path = os.path.join(base_path, relative_path)

            if os.path.isfile(src_path):
                return src_path

    factory_target = os.path.join('.factorytest', os.path.join('files', file_name) )
    factory_type = os.path.join(factory_type, factory_target)
    target_path = os.path.join('res', factory_type)
    target_path = find_inline_file_path(target_path)


    return target_path

    
def get_default_burner_path(args):
    factory_type = get_factory_type(args)
    return get_inline_file_path('burner.img', factory_type)

def parse_user_choice():
    import argparse
    args = None
    try:
        parser = argparse.ArgumentParser(description='欢迎使用本打包工具')
        # parser.add_argument("-c", type=int, choices=[1,2], help="芯片类型[1:300x 2:4002][已废弃，使用默认资源，不支持修改]")
        parser.add_argument("-t", type=str, required = True, choices=['chip','module'], help="烧录类型[chip:芯片烧录 module:模组烧录]")
        parser.add_argument("-b", type=str, required = False, help="burner资源路径[已废弃，使用默认资源，不支持修改]")
        parser.add_argument("-i", type=str, action = utils.readable_dir, help="导入路径[原始固件文件夹]")

        parser.add_argument("-f", type=str, help="flashboot资源路径")
        parser.add_argument("-m", type=str, help="master资源路径")
        parser.add_argument("-s", type=str, help="script资源路径")
        parser.add_argument("-r", type=str, help="respak资源路径")

        parser.add_argument("-d", "--detect", action="store_true", default=False, help="是否自动检测TF卡路径")
        parser.add_argument("-l", "--loop", action="store_true", default=False, help="循环检测")
        parser.add_argument("-o", type=str, help="导出文件夹路径[tf卡生产固件的保存路径]")
        parser.add_argument("-v", action="version", version=version_print())
        
       
        args = parser.parse_args()
        print(args)
        # args = parser.parse_args(choice.split())
    # args = parser.parse_args(['-main', './main.bin', '-cmd', './cmd.bin', '-bias', './bias.bin', '-mlp', './mlp.bin'])
    except Exception as e:
        eprint(e)

    finally:
        return args if args else None



def programmer_welcome_info():
    welcome_info = '''\
###############################################################################
##                          LSFactoryPaker Script                            ##
##          The Best TFCard firmware Generator for LISTENAI Chip-Burner      ##
##                       POWERD BY LISTENAI CO., LTD.                        ##
##                    Presented by FAE GROUP with quality                    ##
##                      Support mail:sycao@listenai.com                      ##
###############################################################################\
'''
    print(logger.get_appoint_color_text(msg = welcome_info, fg='green', bg='black', bold=False))

def wait_for_udisk(timeout=False):
    global global_step
    dev = {'driver':'','opts':''}
    # if timeout:
        # print('\n你正在进行用于聆思芯片烧录器的TF卡固件制作\n请将TF卡插入读卡器，再将读卡器插入电脑')
    while timeout:
        dev = lsusb.get_udisk_partition()
        if dev['driver']:
            print_align('\r' + logger.get_blue_text(f'[{global_step}]检测读卡器 ', intent=True), logger.get_red_text('[√]', intent=True), '读卡器磁盘地址: [{}]'.format(dev['driver']))
            global_step += 1
            break
        else:
            if timeout:
                lsusb.wait_rotate(logger.get_yellow_text('[1]检测读卡器 ') )
            else:
                print_align('\r' + logger.get_blue_text(f'[{global_step}]检测读卡器 ', intent=True), logger.get_red_text('[x]', intent=True), '读卡器磁盘地址: [{}]'.format(dev['driver']))
    return dev

# def test():
#     c = keyboard.Control()
#     i = 0
#     while True:
#         i+=1
#         print(i,c.getdir())

def console_init():
    console.erase_screen(mode=2)

def add_args(args, key, value):
    args.__dict__[key] = value
    return args

def main():
    
    init()
    
    # programmer_welcome_info()

    args = parse_user_choice()
    if not args:
        return

    # 开启检测
    if args.detect:
        dev = wait_for_udisk(args.loop)
        if not (dev['driver'] and os.path.exists(dev['driver'])):
            print('TF卡导出路径为空')
            return
        else:
            args = add_args(args, 'o', dev['driver'])
    else:
        # 不包含导出路径
        if not args.o:
        # if not (args.o and os.path.exists(args.o)):
            print('TF卡导出路径为空')
            return
    
    # 类型非法
    print_factory_type(get_factory_type(args))
    if get_factory_type(args) not in ['chip', 'module']:
        return
    
    # args = add_args(args, 't', get_factory_type(args))
    args = add_args(args, 'b', get_default_burner_path(args))
    args, resurce = resource_prepare(args)
    if not resurce:
        return
    resouce_generate(args, resurce)

    # input('按任意键退出...')

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
    # console_init()

def version_print():
    description = '''
Version: v1.7\n 
Time: 2021/4/8\n  
Author: theirrycao\n
RELEASE:\n
1. 支持芯片烧录，模块烧录，两者区分不同的芯片检测固件
2. 内置检测固件基于(2020/3/30芯片检测固件)
Any Way Get This RC Package:
http://pan.iflytek.com:80/link/C68F68544BFF417F8FA9CC37894C4C7C 密码:47m1)
'''
    description = logger.get_yellow_text('v1.7 releases on 2021/4/8 by theirrycao, 支持芯片烧录，模块烧录，两者区分不同的芯片检测固件')
    return description

if __name__ == '__main__':
    main()