##########################################################################
# File Name: test.py
# Author: ThierryCao
# mail: iamthinker@163.com
# Created Time: 三  9/15 02:56:43 2021
#########################################################################
import csk_serial_burn_tool  
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
from pycallgraph import Config
from pycallgraph import GlobbingFilter

def test():
    print('hh')

def main():
	# 你的主函数代码。
    #entrance_main()
    test()
    csk_serial_burn_tool.entrance_main()
        
if __name__ == "__main__":
    config = Config()
    # 关系图中包括(include)哪些函数名。
    #如果是某一类的函数，例如类gobang，则可以直接写'gobang.*'，表示以gobang.开头的所有函数。（利用正则表达式）。
    config.trace_filter = GlobbingFilter(include=[
        'csk_serial_burn_tool.*',
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
    # 该段作用是关系图中不包括(exclude)哪些函数。(正则表达式规则)
    # config.trace_filter = GlobbingFilter(exclude=[
    #     'pycallgraph.*',
    #     '*.secret_function',
    #     'FileFinder.*',
    #     'ModuleLockManager.*',
    #     'SourceFilLoader.*'
    # ])
    graphviz = GraphvizOutput()
    graphviz.output_file = 'graph.png'
    with PyCallGraph(output=graphviz, config=config):
        main()
