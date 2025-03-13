import gc
import framebuf
from math import ceil
import io
from .colors import *
from .key import *
from .event import *


# 图形界面单例
class GuiSingle:
    GUI_SINGLE = None

    @classmethod
    def set_instance(cls, instance):
        GuiSingle.GUI_SINGLE = instance


class FrameBufferOffset(framebuf.FrameBuffer):
    def __init__(self, buffer, width, height, format, stride, x_offset=0) -> None:
        super().__init__(buffer, width, height, format, stride)
        self.x_offset = x_offset


# 屏幕驱动通用接口
class DisplayAPI(framebuf.FrameBuffer):
    def __init__(self, display) -> None:
        self.display = display
        self.width = display.width
        self.height = display.height
        self.color_mode = color_mode = display.color_mode
        if color_mode == framebuf.RGB565:
            self.buffer = bytearray(self.width * self.height * 2)
        elif color_mode in (
            framebuf.MONO_HLSB,
            framebuf.MONO_HMSB,
        ):
            self.buffer = bytearray(ceil(self.width / 8) * self.height)
        elif color_mode == framebuf.MONO_VLSB:
            self.buffer = bytearray(ceil(self.height / 8) * self.width)
        elif color_mode == framebuf.GS2_HMSB:
            self.buffer = bytearray(ceil(self.width / 4) * self.height)
        elif color_mode == framebuf.GS4_HMSB:
            self.buffer = bytearray(ceil(self.width / 2) * self.height)
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
        """帧缓冲切片，使用memoryview实现，不会占用额外空间。

        Args:
            x: x坐标
            y: y坐标
            w: 像素宽
            h: 像素高

        Returns:
            对应矩形的帧缓冲对象。
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

    # 实现类XLayout透明化
    @property
    def _layout_wh(self):
        return self.width, self.height

    @property
    def _layout_pos(self):
        return (0, 0)

    @property
    def _draw_area(self):
        return self

    def get_absolute_pos(self):
        return (0, 0)

    def _event_receiver(self, _):
        pass


# bytes.split(None)的生成器版本
# def split_space(b: bytes, begin=0):
#     begin_index = begin
#     index = begin
#     len_ = len(b)
#     while index < len_:
#         if b[index : index + 1].isspace():
#             yield b[begin_index:index]
#             begin_index = index + 1
#         index += 1
#     return


def read_to_space(buffer: io.BufferedReader | io.BytesIO, begin: int | None = None):
    cache = b""
    if begin is not None:
        buffer.seek(begin)
    while buffer:
        byte = buffer.read(1)
        if byte.isspace():
            return cache
        else:
            cache += byte
    return b""


def crc32(data: bytes) -> int:
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
    return (~crc) & 0xFFFFFFFF


def rgb888_to_rgb565(r8: int, g8: int, b8: int, big_endian=False) -> int:
    r8 >>= 3
    g8 >>= 2
    b8 >>= 3
    color = (r8 << 11) | (g8 << 5) | b8
    if big_endian:
        return (color & 0xFF00) >> 8 | (color & 0x00FF) << 8
    else:
        return color


def separate_rgb565(rgb565: int, big_endian=False) -> tuple[int, int, int]:
    if big_endian:
        rgb565 = (rgb565 & 0xFF00) >> 8 | (rgb565 & 0x00FF) << 8
    r5 = rgb565 >> 11
    g6 = (rgb565 & 0x07E0) >> 5
    b5 = rgb565 & 0x001F
    return (r5, g6, b5)


def combined_rgb565(r5: int, g6: int, b5: int, big_endian=False) -> int:
    rgb565 = (r5 << 11) | (g6 << 5) | b5
    if big_endian:
        return (rgb565 & 0xFF00) >> 8 | (rgb565 & 0x00FF) << 8
    else:
        return rgb565


gc.collect()
