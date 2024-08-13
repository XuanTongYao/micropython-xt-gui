import framebuf
from math import ceil

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


class FrameBufferOffset(framebuf.FrameBuffer):
    def __init__(self, buffer, width, height, format, stride, x_offset=0) -> None:
        super().__init__(buffer, width, height, format, stride)
        self.x_offset = x_offset


class DisplayAPI(framebuf.FrameBuffer):
    def __init__(self, display) -> None:
        self.display = display
        self.width = display.width
        self.height = display.height
        self.color_mode = color_mode = display.color_mode
        if color_mode == framebuf.RGB565:
            self.buffer = bytearray(self.width * self.height * 2)
        elif color_mode in (
            framebuf.MONO_VLSB,
            framebuf.MONO_HLSB,
            framebuf.MONO_HMSB,
        ):
            self.buffer = bytearray(ceil(self.width * self.height / 8))
        elif color_mode == framebuf.GS2_HMSB:
            self.buffer = bytearray(ceil(self.width * self.height / 4))
        elif color_mode == framebuf.GS4_HMSB:
            self.buffer = bytearray(ceil(self.width * self.height / 2))
        elif color_mode == framebuf.GS8:
            self.buffer = bytearray(self.width * self.height)
        else:
            raise ValueError("Unsupported color mode")
        super().__init__(self.buffer, self.width, self.height, color_mode)

    def clear(self):
        self.fill(0)
        self.update_frame()

    def update_frame(self):
        self.display.write_gddram(self.buffer)

    def framebuf_slice(self, x, y, w, h):
        """帧缓存切片，使用memoryview实现，不会占用额外空间。

        Args:
            x: x坐标
            y: y坐标
            w: 像素宽
            h: 像素高

        Returns:
            对应矩形的帧缓存对象。
        """
        width = self.width
        color_mode = self.color_mode

        if color_mode == framebuf.RGB565:
            byte_offset = (width * 2 * y) + (x * 2)
        elif color_mode in (
            framebuf.MONO_VLSB,
            framebuf.MONO_HLSB,
            framebuf.MONO_HMSB,
        ):
            byte_offset = (ceil(width / 8) * y) + (x // 8)
        elif color_mode == framebuf.GS2_HMSB:
            byte_offset = (ceil(width / 4) * y) + (x // 4)
        elif color_mode == framebuf.GS4_HMSB:
            byte_offset = (ceil(width / 2) * y) + (x // 2)
        elif color_mode == framebuf.GS8:
            byte_offset = (width * y) + x
        else:
            raise ValueError("Unsupported color mode")

        tmp = memoryview(self.buffer)
        if color_mode in (framebuf.RGB565, framebuf.GS8):
            return framebuf.FrameBuffer(tmp[byte_offset:], w, h, self.color_mode, width)
        else:
            return FrameBufferOffset(
                tmp[byte_offset:], w, h, self.color_mode, width, 8 - (x % 8)
            )


# 图形界面单例
class GuiSingle:
    GUI_SINGLE = None

    @classmethod
    def set_instance(cls, instance):
        GuiSingle.GUI_SINGLE = instance
