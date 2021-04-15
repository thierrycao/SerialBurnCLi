from pynput.keyboard import Key,Listener
# from direction import Direction

import enum
class Direction(enum.Enum):
    UP      = 1
    DOWN    = 2
    LEFT    = 3
    RIGHT   = 4

class Control():
    def __init__(self):
        self.dir_ = None # dir一定要用成员变量，不然没办法在on_press中修改

    def getdir(self):
        self.dir_ = None    # 如果是不是上下左右则返回None
        def on_press(key):
            if key == Key.up:self.dir_ = Direction.UP
            elif key == Key.down:self.dir_ = Direction.DOWN
            elif key == Key.left:self.dir_ = Direction.LEFT
            elif key == Key.right:self.dir_ = Direction.RIGHT
            return False
        listener = Listener(on_press=on_press) # 创建监听器
        listener.start()    # 开始监听，每次获取一个键
        listener.join()     # 加入线程
        listener.stop()     # 结束监听，没有这句也行，直接随函数终止
        return self.dir_