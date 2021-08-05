import colorama
from colorama.winterm import win32 as win32
import ctypes
from ctypes import wintypes
import time
terminal = None
if terminal == None:
    terminal = colorama.winterm.WinTerm()

def print_local_position(handler, stream_id):
    position = handler.get_position(stream_id)
    if position:
        print('[pos: x:%d, y:%d]' %(position.X, position.Y), end='')

def get_current_before_cells(stream_id):
    csbi = win32.GetConsoleScreenBufferInfo(stream_id)
    # get the number of character cells in the current buffer
    cells_in_screen = csbi.dwSize.X * csbi.dwSize.Y
    # get number of character cells before current cursor position
    cells_before_cursor = csbi.dwSize.X * csbi.dwCursorPosition.Y + csbi.dwCursorPosition.X
    return cells_before_cursor
    # print(cells_before_cursor)
def SetConsoleCursorPosition(stream_id = win32.STDOUT, position = (1,1)):
    win32.SetConsoleCursorPosition(stream_id, position)

def erase_line(handler = terminal, stream_id = win32.STDOUT, row = 0, col=0):
    global terminal
    if handler == None:
        terminal = colorama.winterm.WinTerm()
        handler = terminal
    if stream_id == None:
        stream_id = win32.STDOUT

    csbi = win32.GetConsoleScreenBufferInfo(stream_id)
    # from_coord = get_current_before_cells(stream_id)
    from_coord = win32.COORD(row, csbi.dwCursorPosition.Y - col)
    cells_to_erase = csbi.dwSize.X * col + csbi.dwCursorPosition.X - row

    # fill the entire screen with blanks
    win32.FillConsoleOutputCharacter(stream_id, ' ', cells_to_erase, from_coord)
    # now set the buffer's attributes accordingly
    # win32.FillConsoleOutputAttribute(stream_id, handler.get_attrs(), cells_to_erase, from_coord)
    win32.SetConsoleCursorPosition(stream_id, position = (csbi.dwCursorPosition.Y - col ,1), adjust=False)

    # print('1', end='')
    # # win32.SetConsoleCursorPosition(stream_id, position = (csbi.dwCursorPosition.Y - col,1), adjust=False)
    # time.sleep(1)
    # print('2', end='')
    # # win32.SetConsoleCursorPosition(stream_id, position = (csbi.dwCursorPosition.Y - 1,1), adjust=False)
    # time.sleep(1)
    # print('3')
    # position = handler.get_position(stream_id)
    # time.sleep(1)
    # print(position.Y, position.X)
    # SetConsoleCursorPosition(position = (1,1))
    # print('1', end='')
    # time.sleep(1)
    # SetConsoleCursorPosition(position = (2,1))
    # print('2', end='')
    # time.sleep(1)

    # SetConsoleCursorPosition(position = (3,3))
    # print('3', end='')
    # time.sleep(1)

    # print(csbi.dwCursorPosition.Y)
    # print(csbi.dwCursorPosition.Y)
    # print(csbi.dwCursorPosition.X)
    # win32.SetConsoleCursorPosition(stream_id, (1, 1))


def restore_last_position(row = 0, col = 0):
    erase_line(terminal, win32.STDOUT, row, col)

def erase_screen(handler = terminal, mode = 0):
    if handler == None:
        terminal = colorama.winterm.WinTerm()
        handler = terminal
    handler.erase_screen(mode)

def main():
    terminal = colorama.winterm.WinTerm()
    print('123')
    erase_line(terminal, win32.STDOUT, row = 1, col = 1)
    terminal.set_cursor_position(position=(1,0))
    print('456',end='')
    # terminal.erase_screen(mode=1)
    

# if __name__ == '__main__':
#     main()

def process_posix():
    #原文链接：https://blog.csdn.net/weixin_39793553/article/details/111293598
    import time
    import sys

    CSI = '\033['

    def cursor_prev_line():
        return CSI + '1F'

    for i in range(101):
        sys.stdout.write(cursor_prev_line())
        sys.stdout.flush()
        print("process ... " + str(i) + "%")
        time.sleep(0.1)
    print("Done!")
