# -*- coding:utf-8 -*-
# *************************************************************************
#	> File Name: utils.py
#	> Author: ThierryCao
#	> Mail: sycao@listenai.com
#	> Created Time: Thu 28 May 2020 12:54:08 PM CST
# ************************************************************************
import os, sys, platform
import csv, shutil, json
from plugins import logger 
import time
import argparse

class readable_dir(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            print("readable_dir:{0} is not a valid path".format(prospective_dir))
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))

# import binascii
def is_python2():
    return sys.version_info < (3,0)

# def bytes2int(data):
#     if data and isinstance(data, bytes):
#         return int(data.hex(), 16)
#     return None
def get_platform_system():
    return platform.system().lower()

def isPlatformWin():
    return True if get_platform_system() == 'Windows' else False

def run_shell(cmd):
    import subprocess
    def runcmd(command):
        ret = subprocess.run(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,encoding="utf-8",timeout=1)
        if ret.returncode == 0:
            print("success:",ret)
        else:
            print("error:",ret)
    runcmd(cmd)


def bytes2Int(bytes_t, signed=True):
    return int.from_bytes(bytes_t, 'little', signed=signed)
def dirs(dirs):
    try:
        if dirs and (not os.path.isdir(dirs)):
            os.makedirs(dirs)
    except Exception as e:
        print(e)
    # return dirs

def rm_rf(dirs, forced=False):
    try:
        if dirs and os.path.isdir(dirs):
            # print('rm_rf')
            if not forced:
                choice = ''
                choice = user_choice(f"发现已存在的目录[{dirs}],确定删除[y/n]: ", lambda x: x and x in ['y', 'n'], choice)
                if choice == 'n':
                    return
            shutil.rmtree(dirs, True)
            time.sleep(0.1)
            if not os.path.isdir(dirs):
                print(f'>>>[{dirs}]已删除!')
    except Exception as e:
        print(e)

def is_windows():
    if platform.system() == "Windows":
        return True
    else:
        return False

def is_number(s):
    if not s:
        return False
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
 
    return False

def is_csv_file(src_file):
    if not (src_file and os.path.isfile(src_file)):
        return False
    try:     
        with open(src_file, 'r') as cf:
            lines = csv.reader(cf)
            if lines:
                # print(lines)
                return True
    except Exception as e:
        print(type(e), e)
        return False
def is_txt_file(src_file):
    if not (src_file and os.path.isfile(src_file) and src_file.split('.')[-1] == 'txt'):
        return False
    return True

def is_spec_type(path, type=''):
    if path and type:
        return os.path.splitext(os.path.basename(path))[-1] == f'.{type}'
    else:
        print(f'path:{path}, type:{type} either is wrong!')
        return False
def get_file_suffix(path):
    return os.path.splitext(os.path.basename(path))[-1].strip('.')
def get_file_prefix(path):
    return os.path.splitext(os.path.basename(path))[0]

def read_hex_from_bin(src_file):
    """[read_list_from_txt]

    Args:
        src_file ([type]): [description]

    Returns:
        [type]: [description]
    """
    if not os.path.isfile(src_file):
        return []
    line = []
    try:
        with open(src_file, 'rb') as rf:
            line = list(bytearray.fromhex(rf.read().hex()))
            return line
    except Exception as err:
        print(err)

def read_list_from_txt(src_file):
    """[read_list_from_txt]

    Args:
        src_file ([type]): [description]

    Returns:
        [type]: [description]
    """
    if not os.path.isfile(src_file):
        return []
    line = []
    try:
        with open(src_file, 'r', encoding='utf-8') as rf:
            line = rf.readlines()
            line = [ i.strip().strip('\r').strip('\n') for i in line ]
            return line
    except Exception as err:
        print(err)
    # finally:
        # print('{} len:{}'.format(src_file, len(line)))

def read_from_json_file_as_dict(src_file):
    """[read_from_json_file_as_dict]

    Args:
        src_file ([type]): [description]

    Returns:
        [dict]: [description]
    """
    result = {}
    if not os.path.isfile(src_file):
        return result
    try:
        if is_python2():
            with open(src_file, 'rb') as i:
                result = json.loads(i.read())
        else:
            with open(src_file, 'r', encoding='utf-8') as i:
                result = json.load(i)
    except Exception as err:
        print(err)
    finally:
        # print('{} len:{}'.format(src_file, len(result)))
        # print(result)
        return result
def write_dict_in_json_file(dict_data, output_file):
    """[write_data_to_json]

    Args:
        dict_data ([type]): [description]
        output_file ([type]): [description]

    Returns:
        [type]: [description]
    """
    if not (dict_data and output_file):
        return False
    try:
        if is_python2():
            with open(output_file, 'w') as o:
            # with open(src_file, 'rb') as i, open(output_file, 'w') as o:
                o.write(json.dumps(dict_data))
        else:
            with open(output_file, 'w') as o:
            # with open(src_file, 'r', encoding='utf-8') as i, open(output_file, 'w') as o:
                o.write(json.dumps(dict_data))
    except Exception as err:
        print(err)

def write_bin_list_to_file(src_list, output='output.bin'):
    # print('----------write_bin_list_to_file----------')
    # print(f'[write_bin_list_to_file], src_list:{len(src_list)}, output={output}')
  
    try:
        with open(output, 'wb') as wf:
            if isinstance(src_list, list):
                for i in src_list:
                    # wf.write(bytes(i))
                    wf.write(i.to_bytes(1, byteorder='little', signed=True))
            else:
                wf.write(bytes(src_list))
    except Exception as err:
        print(err)

def write_bin_list_to_bmp(src_list, width, height, save_path=''):
    from PIL import Image
    import numpy as np
    # import matplotlib.pyplot as plt
    # width = 46
    # height = 180
    # img_ori = open('1_46_180.bin', 'rb')
    # img_ori_data = img_ori.read()
    # print('len:', len(img_ori_data))

    img_gray_8 = Image.new('L', (width, height), 128)

    img = np.array(img_gray_8)

    print(img.shape)
    #rows,cols,dims = img.shape

    for i in range(height):
        for j in range(width):
            img[i, j] = src_list[i*width + j]
        
    # print('end')
    # save_path = '1.bmp'
    im = Image.fromarray(img)
    im.convert('L').save(save_path) # 保存为灰度图(8-bit)

def connect_bmp(info_list, save_path=''):
    from PIL import Image

    # width = 500
    width = 0
    width_index = 0
    height = 220

    for i in info_list:
        width += i.get('width')
    # 创建空白图片
    img_gray_8 = Image.new('L', (width, height), 128)
    for index,value in enumerate(info_list):
        img = Image.open(value.get('file_path')).convert("L")
        img_gray_8.paste(img, (width_index , 20 ))
        # img_gray_8.paste(img, (width_index , 20 + value.get('yset')))
        width_index += value.get('width') 
        # img_gray_8.paste(img, (width_index + value.get('xset'), 20 + value.get('yset')))
        # width_index += value.get('width') + value.get('xset')

    img_gray_8.save(save_path)

def write_str_list_to_file(src_list, output='output.txt', split_char='\n'):
    """[write_str_list_to_file]

    Args:
        src_list ([type]): [description]
        output (str, optional): [description]. Defaults to 'output.txt'.
        split_char (str, optional): [description]. Defaults to '\n'.
    """

    # print(f'[write_str_list_to_file], src_list:{len(src_list)}, output={output}')

    if not (src_list and split_char):
        return
    # print('output to txt:{}'.format(src_list))
    src_list = [ str(i) for i in src_list ]
    try:
        with open(output, 'w', encoding='utf-8') as wf:
            wf.write(split_char.join(src_list))
    except Exception as err:
        print(err)

def get_spec_type_file_from_dir(dir_path, index = 1, type='ini'):
        target_file = ''
        listDir = os.listdir(dir_path)
        target_files = [i for i in listDir if i.split('.')[-1] == type]
        if len(target_files) < index:
            return None
        elif len(target_files) >= index:
            target_file = target_files[index - 1]
            return os.path.join(dir_path, target_file)

def strip_json(src_file='', output_file=''):
    """[strip_json]

    Args:
        src_file (str, optional): [description]. Defaults to ''.
        output_file (str, optional): [description]. Defaults to ''.
    """

    src_file = user_choice(u"请输入文件: ", lambda a: os.path.isfile(a), src_file)
    output_file = user_choice(u"请输入保存的文件: ", lambda a: a is not '', output_file)
    if is_python2():
        with open(src_file, 'rb') as i, open(output_file, 'w') as o:
            o.write(json.dumps(json.loads(i.read()), ensure_ascii=False))
    else:
        with open(src_file, 'r', encoding='utf-8') as i, open(output_file, 'w') as o:
            o.write(json.dumps(json.load(i), ensure_ascii=False))
def is_json_file(src_file):
    data = dict()
    try:
        if is_python2():
            with open(src_file, 'rb') as i:
                data = json.loads(i.read())
        else:
            with open(src_file, 'r', encoding='utf-8') as i:
                data = json.load(i)
    except Exception as e:
        # print(e)
        return False
    # print('is_json_file:', data)
    return True

def add_json(src_file='', output_file=''):
    src_file = user_choice(u"请输入文件: ", lambda a: os.path.isfile(a), src_file)
    output_file = user_choice(u"请输入保存的文件: ", lambda a: a is not '', output_file)
    try:
        if is_python2():
            with open(src_file, 'rb') as i:
                data = json.loads(i.read())
            with open(output_file, 'w') as o:
                data = json.dump(data, ensure_ascii=False, indent=1)
                o.write(data)
        else:   
            with open(src_file, 'r', encoding='utf-8') as i:
                data = json.load(i)
                # print('+++++', data)
            #中文编码
            with open(output_file, 'w', encoding='utf-8') as o:
                data = json.dumps(data, ensure_ascii=False, indent=1)
                o.write(data)
    except Exception as err:
        print(err)


def load_json_file_dump_bytes(src_file=''):
    data = bytes()
    src_file = user_choice(u"请输入文件: ", lambda a: os.path.isfile(a), src_file)
    if is_python2():
        with open(src_file, 'rb') as i:
            # if indent:
            #     data = json.dumps(json.loads(i.read()), ensure_ascii=False, indent=1)
            # else:
            # data = json.dumps(json.loads(i.read()), ensure_ascii=False)
            data = json.loads(i.read())
            data = bytes('{}'.format(data), 'utf-8')
            return data
    else:
        with open(src_file, 'r', encoding='utf-8') as i:
            # if indent:
            #     # data = json.dumps(json.load(i), ensure_ascii=False, indent=1)
            #     data = json.load(i)
            #     data = bytes('{}'.format(data), 'utf-8')
            # else:
            # data = json.dumps(json.load(i), ensure_ascii=False)
            # data = bytes('{}'.format(data), 'utf-8')
            # print('[load_json_file_dump_bytes]:', data)
            data = json.load(i)
            data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
            return data.encode('utf-8')
            
    # return data.encode('utf-8')

def load_file_dump_bytes(src_file=''):
    if not os.path.isfile(src_file):
        print(f'{src_file} not found')
        return bytes()
    try:
        with open(src_file, 'rb') as f:
            return f.read()
    except Exception as err:
        print(err)

def read_list_from_csv(src_file, column_num=0):
    lines = []
    if not (src_file and os.path.isfile(src_file)):
        return lines
    try:     
        with open(src_file, 'r') as cf:
            obj = csv.reader(cf)
            for i in obj:
                # print(type(i), i)
                if column_num == -1:
                    lines.append(i)
                else:
                    lines.append(i[column_num])
            
    except Exception as e:
        print(type(e), e)
    finally:
        return lines

# def get_abs_path(dir_path, file_path):
#     return os.path.join(dir_path, file_path)
def get_abs_path(*param):
    return os.path.join(*param)

def read_data_from_file(src_file):
    data = ''
    if not os.path.isfile(src_file):
        return data
    try:
        with open(src_file, "r") as rf:
            data = rf.read()
    except Exception as e:
        print(type(e), e)
    finally:
        return data

def is_keyword_in_text(keyword, text):
    if isinstance(keyword, str):
        return (keyword in text, [keyword])
    elif isinstance(keyword, list):
        for i in keyword:
            if i in text:
                return (True, [i])
        return (False, keyword)

    return (False, [keyword])


def find_file_by_content(path, keyword):
    """[find_content]

    Args:
        path ([type]): [description]
        key_word ([type]): [description]

    Returns:
        [type]: [description]
    """
    filename = []
    key_word = []

    #遍历目录文件名
    for cur_dir, dirs, files in os.walk(path):  
        for target in files:
            #切换到当前路径
            # os.chdir(cur_dir)  
            name = get_abs_path(cur_dir, target)
            #读文件内容
            r = read_data_from_file(name)  
            #文件内容是否包含关键字
            result, key_word = is_keyword_in_text(keyword, r)  
            if result:
                #文件名及路径添加到数组
                filename.append(os.path.abspath(name))  
    return filename  #返回数组

def find_file_by_fileName(path, keyword):
    filename = []
    key_word = []

    #遍历目录文件名
    for cur_dir, dirs, files in os.walk(path):  
        for target in files:
            #切换到当前路径
            # os.chdir(cur_dir)  
            name = get_abs_path(cur_dir, target)
            # print(name)
            if os.path.isfile(name):
                result, key_word = is_keyword_in_text(keyword, str(name))
                if result:
                    #文件名及路径添加到数组
                    filename.append(os.path.abspath(name))  
    #返回数组
    return filename

def search(root, target):
    items = os.listdir(root)
    for item in items:
        path = os.path.join(root, item)
        if os.path.isdir(path):
            print('[-]', path)
            search(path, target)
        elif path.split('/')[-1] == target:
            print('[+]', path)
        else:
            print('[!]', path)
def search_dir(root, target):
    result = []
    items = os.listdir(root)
    for item in items:
        path = os.path.join(root, item)
        if os.path.isdir(path) and path.split(os.sep)[-1] == target and path not in result:
            print('[=]', path)
            result.append(path)
            ret = search_dir(path, target)
            if ret:
                result.extend(ret)
        elif os.path.isdir(path) and path.split(os.sep)[-1] != target:
            # print('[+]', path)
            ret = search_dir(path, target)
            if ret:
                result.extend(ret)
        # else:
            # print('[!]', path)

    return result

def copy_files_to_target_dir(src_files, target_dir):
    if not (src_files and target_dir):
        return
    dirs(target_dir)
    for i in src_files:
        if os.path.isfile(i):
            shutil.copy(i, target_dir)

def get_realpath_file_base_dir(src_file):
    if src_file and os.path.isfile(src_file):
        return os.path.dirname(os.path.abspath(src_file))
    return None

def get_text_file_base_dir(text):
    return os.path.split(text)[0] if text else None

def get_text_file_base_name(text):
    return os.path.split(text)[-1] if text else None


def read_section_data_from_json(src_file, section):
    data = read_from_json_file_as_dict(src_file)
    section_list = []
    if data and section in data.keys():
        section_list = data.get(section)
    else:
        print(f'[read_section_data_from_json], cannot find {section} in {src_file}')
    print(f'read_section_data_from_json, src_file:{src_file}, section:{section}')
    print(section_list)

    return section_list

def merge_section_appoint(appoint_id, appoint_id_2, list1, list2):
    result_list = []
    if appoint_id and appoint_id_2:
        for i in list1:
            for j in list2:
                if appoint_id in i.keys():
                    kuid = i.get(appoint_id)
                    if appoint_id_2 in j.keys():
                        if kuid == j.get(appoint_id_2):
                            result = dict(i, **j)
                            result_list.append(result)
        return result_list

def pop_section_appoint(appoint_id, lt):
    """[pop_section_appoint]

    Args:
        appoint_id ([str]): [appoint section]
        lt ([list/dict]): [target]

    Returns:
        [list/dict]: [result after disposed]
    """
    if lt and isinstance(lt, list):
        for i in lt:
            if isinstance(i, dict) and appoint_id in i.keys():
                i.pop(appoint_id, None)
    elif lt and isinstance(lt, dict) and appoint_id in lt.keys():
        lt.pop(appoint_id, None)
    return lt

def pop_section_appoint_from_json(src_file, section):
    data = read_from_json_file_as_dict(src_file)
    if data and section in data.keys():
        data.pop(section, None)
    else:
        print(f'[pop_section_appoint_from_json], cannot find {section} in {src_file}')
    print(f'pop_section_appoint_from_json, src_file:{src_file}, section:{section}')
    print(data)

    return data

def cp_rf(from_dir, to_dir, target='dir', forced = False):
    if os.path.isdir(from_dir) and to_dir:
        from_list = []
        to_list = []
        if not os.path.isdir(to_dir):
            shutil.copytree(from_dir, to_dir)
        else:
            from_f = os.path.basename(from_dir)
            to_tree = os.path.join(to_dir, from_f)
            if to_tree and os.path.isdir(to_tree):
                rm_rf(to_tree, forced=forced)
            shutil.copytree(from_dir, to_tree)
            # from_list = os.listdir(from_dir)
            # if from_list:
            #     to_list = os.listdir(to_dir)
            #     for from_f in from_list:
            #         abs_from = os.path.join(from_dir, from_f)
            #         if os.path.isfile(abs_from):
            #             if from_f in to_list:
            #                 abs_to = os.path.join(to_dir, from_f)
            #                 if os.path.isfile(abs_to):
            #                     os.remove(abs_to)
            #             shutil.copy(os.path.join(from_dir, from_f),
            #                         os.path.join(to_dir, from_f))
        return
    elif os.path.isfile(from_dir) and to_dir:
        if (not os.path.isdir(to_dir)) and target == 'dir':
            dirs(to_dir)
            shutil.copy(from_dir, to_dir)
        elif os.path.isdir(to_dir) and target == 'dir':
            from_f = os.path.basename(from_dir)
            to_list = os.listdir(to_dir)
            if from_f in to_list:
                abs_to = os.path.join(to_dir, from_f)
                if os.path.isfile(abs_to):
                    os.remove(abs_to)
            shutil.copy(from_dir,
                        os.path.join(to_dir, from_f))
        elif (not os.path.isfile(to_dir)) and target == 'file':
            target_dir = get_text_file_base_dir(to_dir)
            target_name = get_text_file_base_name(to_dir)
            dirs(target_dir)
            shutil.copy(from_dir, to_dir)
        elif os.path.isfile(to_dir):
            os.remove(to_dir)
            shutil.copy(from_dir, to_dir)
            

def input_text(notice, color = False):
    if is_python2():
        # print('---')
        if color:
            param = raw_input(logger.get_blue_text(notice.encode('gbk')))
        else:
            param = raw_input(notice.encode('gbk'))
    else:
        if color:
            param = input(logger.get_blue_text(notice))
        else:
            print(f'{notice}', end='')
            param = input()
            # param = input(u'{}'.format(notice))
    return param

def user_choice(notice, cond, param, reset = False, color = False, debug=False):
    if reset:
        param = ''
    while not cond(param):
        param = input_text(notice, color = color)
        if debug:
            print(f'>>>你的输入为:{param}')
    return param

def search_files_by_keyword(path='', keyword=''):
    target_file = ''
    target_dir = ''
    choice = ''
    path = user_choice(u"请输入需要搜索的文件夹路径: ", lambda a: os.path.isdir(a), path)
    keyword = user_choice(u"请输入关键字[文件请输入*.txt]: ", lambda a: a is not '', keyword)
    # keyword = user_choice(u"请输入关键字: ", lambda a: a is not '', keyword)
    if keyword and os.path.isfile(keyword):
        if is_csv_file(keyword):
            print(f'--------{keyword} is csv file-------')
            keyword = read_list_from_csv(keyword)     
            # print(keyword)
        elif is_txt_file(keyword):
            keyword = read_list_from_txt(keyword)
    result = find_file_by_fileName(path, keyword)
    if result:
        print(f'已找到{len(result)}条搜索结果>>>>')
        choice = user_choice(u'是否需要将结果写入文件中[y/n]: ', lambda a: a in ['y', 'n'], choice, reset = True)
        if choice == 'y':
            target_file = user_choice(u"请输入需要写入的文件名: ", lambda a: a is not '', target_file)
            print(f'即将写入{target_file}>>>>')
            write_str_list_to_file(result, output=target_file, split_char='\n')
            print(f'写入成功>>>>')
        else:
            choice = user_choice(u'是否需要将结果打印[y/n]: ', lambda a: a in ['y', 'n'], choice, reset = True)
            if choice == 'y':
                print('>>>搜索结果:', result)
        choice = ''
        choice = user_choice(u'是否需要拷贝文件到对应目标文件夹[y/n]: ', lambda a: a in ['y', 'n'], choice)
        if choice == 'y':
            target_dir = user_choice(u"请输入需要拷贝到的文件夹路径: ", lambda a: os.path.isdir(a), target_dir)
            print(f'即将拷贝到{target_dir}>>>>')
            copy_files_to_target_dir(result, target_dir)
            print(f'拷贝成功>>>>')


global_commands = []

def register_command(description, callback):
    global global_commands
    if isinstance(global_commands, list):
        global_commands.append({'id': len(global_commands) + 1, 'des': description, 'cb': callback})

def print_function():
    # 1.search_files_by_keyword[path, keyword], 通过关键字搜索文件夹下匹配的对应文件'
    #     description = '''\
    # 1.通过关键字搜索文件夹下匹配的对应文件
    # 2.
    # 3...\
    # '''
    # print(description)
    # logger.get_appoint_color_text(msg = welcome_info, fg='green', bg='black', bold=False)
    description = ['{}.{}'.format(logger.get_appoint_color_text(i.get('id'), fg='yellow', bg='black', bold=False), i.get('des')) for i in global_commands]
    description = f'\n'.join(description)
    return description

def get_commands_len():
    return len(global_commands)
def get_commands_list():
    return global_commands
def functions():
    choice = 0
    # choice = user_choice(u"你好:", lambda a: a is not '', choice, reset = True)
    register_command('通过关键字搜索文件夹下匹配的对应文件', search_files_by_keyword)
    if get_commands_len() < 1:
        return

    choice = user_choice(u"{}\n请输入需要的功能{}: ".format(print_function(), f'[1-{get_commands_len()}]' if get_commands_len() > 1 else f'[{get_commands_len()}]'),\
                         lambda a: is_number(a) and int(a) in [ i+1 for i in range(0, get_commands_len()) ], choice)
    get_commands_list()[int(choice)-1].get('cb')()



def main():
    functions()

if __name__ == '__main__':
    main()
