##########################################################################
# File Name: dot_generate.py
# Author: ThierryCao
# mail: iamthinker@163.com
# Created Time: 二  9/14 22:33:41 2021
#########################################################################

import os
import ast
import sys
from graphviz import Digraph
import _locale
_locale._getdefaultlocale = (lambda *args: ['zh_CN', 'utf8'])


def simplecfg(*args):
    visitor = CodeVisitor()
    for infile in args[0]:
        f = open(infile, "r")
        r_node = ast.parse(f.read())
        f.close()
        visitor.filename = os.path.basename(infile).split('.')[0]
        visitor.visit(r_node)

    fpos = {}#fpos存放函数basename所在的py文件
    for func in visitor.userfunc:
        fr = func.split('.')[0]
        bk = func.split('.')[-1]
        fpos[bk] = fr

    dest = {}#dest存放每个userfunc下调用了哪些userfunc
    for line in visitor.info:
        if line.startswith('User Function Name'):
            defnow = line.split(':')[1]
            dest[defnow] = []
            continue
        for func in visitor.userfunc:
            basename = func.split('.')[-1]
            line_tail = line.split(':')[-1]
            line_tail = line_tail.split('.')[-1]
            if basename == line_tail:
                dest[defnow].append(basename)
                break

    dot = Digraph(comment='The Round Table')

    ctr = 0
    alias = {}
    #在dot语法中，结点有自己的名字，这个名字跟结点在图片上显示的函数名字不同。alias存储两者的映射。

    for func in visitor.userfunc:
        ctr += 1
        alias[func] = 'A'+str(ctr)#跟dot语法的命名规则有关，也可以用其它命名，不必纠结
        dot.node(alias[func], func)
    for key in dest.keys():
        for dst in dest[key]:
            fullname = fpos[dst] + '.' + dst
            dot.edge(alias[key], alias[fullname])

    dot.render('test-output/round-table.gv')
    # print(ast.dump(r_node))


class CodeVisitor(ast.NodeVisitor):
    userfunc = []
    info = []
    filename = ''
    def generic_visit(self, node):
        # print(type(node).__name__)
        ast.NodeVisitor.generic_visit(self, node)
    def visit_FunctionDef(self, node):
        # print('User Function Name:%s' % node.name)
        self.info.append('User Function Name:'+self.filename+'.'+node.name)
        self.userfunc.append(self.filename+'.'+node.name)
        ast.NodeVisitor.generic_visit(self, node)
    def visit_Call(self, node):
        # print(node._fields)
        def recur_visit(node):
            if type(node) == ast.Name:
                return node.id
            elif type(node) == ast.Attribute:
                # Recursion on series of calls to attributes.
                # print(node.attr)
                func_name = recur_visit(node.value)
                if type(node.attr) == str and type(func_name) == str:
                    func_name += '.' + node.attr
                # else:
                    # print('attention!!!', type(node.attr), type(func_name))
                return func_name
            elif type(node) == ast.Str:
                return node.s
            elif type(node) == ast.Subscript:
                return node.value.id

        func = node.func
        # print(type(func), func._fields)
        func_name = recur_visit(func)
        if(type(func_name)==str):
            self.info.append('\tUser function Call:'+self.filename+'.'+func_name)
        ast.NodeVisitor.generic_visit(self, node)


simplecfg(sys.argv[1:])

