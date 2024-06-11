def NullFunc():
    pass


# RGB565 颜色定义(大端序BE)
BLACK = const(0x0000)
BLUE = const(0x1F00)
RED = const(0x00F8)
GREEN = const(0xE007)
CYAN = const(0x0FF7)
MAGENTA = const(0x1FF8)
YELLOW = const(0xE0FF)
WHITE = const(0xFFFF)


# 按键代码定义
KEY_ESCAPE = const(0)
KEY_MOUSE0 = const(1)
KEY_MOUSE1 = const(2)
KEY_LEFT = const(3)
KEY_UP = const(4)
KEY_RIGHT = const(5)
KEY_DOWN = const(6)


# 按键响应返回值
ESC = const(0)
ENTER = const(1)
