"""
MIT License

Copyright (c) 2024 XuanTongYao
Copyright (c) 2022 AntonVanke

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

#   Github: https://github.com/XuanTongYao/MicroPython-uFont
#   Github_upstream: https://github.com/AntonVanke/MicroPython-uFont
#   Gitee: https://gitee.com/liio/MicroPython-uFont
#   Tools: https://github.com/AntonVanke/MicroPython-ufont-Tools
#   Videos:
#       https://www.bilibili.com/video/BV12B4y1B7Ff/
#       https://www.bilibili.com/video/BV1YD4y16739/
__version__ = 3

import utime
import struct
import gc
import framebuf, micropython
from math import ceil

DEBUG = True

# 字体文件头长度
_HEADER_LEN = const(0x10)

# 索引分块(起始与结束)
# 拉丁字母
_BLOCK_LATIN_B = const(0)
_BLOCK_LATIN_E = const(0x024F)

# 西里尔字母
_BLOCK_CYRILLIC_B = const(0x0400)
_BLOCK_CYRILLIC_E = const(0x052F)

# 中日韩统一表意文字
_BLOCK_CJK_B = const(0x4E00)
_BLOCK_CJK_E = const(0x9FFF)

_UNICODE_BLOCK_RANGE = (
    (_BLOCK_LATIN_B, _BLOCK_LATIN_E),
    (_BLOCK_CYRILLIC_B, _BLOCK_CYRILLIC_E),
    (_BLOCK_CJK_B, _BLOCK_CJK_E),
)


def timed_function(f, *args, **kwargs):
    """测试函数运行时间"""
    # 当交叉编译后无法获取函数名
    try:
        _name = f.__name__
    except AttributeError:
        _name = "Unknown"

    def new_func(*args, **kwargs):
        if DEBUG:
            t = utime.ticks_us()
            result = f(*args, **kwargs)
            delta = utime.ticks_diff(utime.ticks_us(), t)
            print("Function {} Time = {:6.3f}ms".format(_name, delta / 1000))
            return result
        else:
            return f(*args, **kwargs)

    return new_func


class BMFont:

    # @micropython.native
    @timed_function
    def text(
        self,
        display,
        string: str,
        x: int,
        y: int,
        color: int = 0xFFFF,
        bg_color: int = 0,
        font_size: int | None = None,
        half_char: bool = True,
        auto_wrap: bool = False,
        show: bool = True,
        clear: bool = False,
        alpha_color: int = 0,
        reverse: bool = False,
        color_type: int = -1,
        line_spacing: int = 0,
    ):
        """
        Args:
            display: 显示对象
            string: 显示文字
            x: 字符串左上角 x 轴坐标
            y: 字符串左上角 y 轴坐标
            color: 字体颜色(RGB565)
            bg_color: 字体背景颜色(RGB565)
            font_size: 字号大小
            half_char: 半宽显示 ASCII 字符
            auto_wrap: 自动换行
            show: 实时显示
            clear: 清除之前显示内容
            alpha_color: 透明色(RGB565) 当颜色与 alpha_color 相同时则透明
            reverse: 反色(MONO)
            color_type: 色彩模式 0:MONO 1:RGB565
            line_spacing: 行间距

        Returns:
        MoreInfo: https://github.com/AntonVanke/MicroPython-uFont/blob/master/README.md
        """
        width = display.width
        height = display.height

        # 如果没有指定字号则使用默认字号
        font_size = self.font_size if font_size is None else font_size
        # 与默认字号不同的字号将引发放缩
        font_resize = font_size != self.font_size
        # 记录初始的 x 位置
        initial_x = x

        # 自动判断颜色类型
        if color_type == -1 and (width * height) > len(display.buffer):
            color_type = 0
        elif color_type == -1:
            color_type = 1

        # 清屏
        try:
            if clear:
                display.clear()
        except AttributeError:
            print("请自行调用 display.fill() 清屏")

        # 点阵缓存
        bitmap_cache = self.bitmap_cache or bytearray(
            ceil(self.font_size * self.font_size / 8)
        )

        # 构建调色板
        if color_type == 0:
            palette = framebuf.FrameBuffer(bytearray(2), 2, 1, framebuf.MONO_HLSB)
            # 处理黑白屏幕背景反转(反色)，反转调色板的颜色即可
            if reverse or color == 0 != bg_color:
                palette.pixel(0, 0, 1)
                alpha_color = -1
            else:
                palette.pixel(1, 0, 1)
        else:
            palette = framebuf.FrameBuffer(bytearray(4), 2, 1, framebuf.RGB565)
            palette.pixel(0, 0, bg_color)
            palette.pixel(1, 0, color)

        # 构建FrameBuffer
        # 给放缩模式提前构建FrameBuffer并不会提升速度
        # 因为显示文字前需要擦除原有内容，重新申请一块内存速度更快
        if not font_resize:
            framebuf_ = framebuf.FrameBuffer(
                bitmap_cache, font_size, font_size, framebuf.MONO_HLSB
            )

        for char in string:
            if auto_wrap and (
                (x + font_size // 2 > width and ord(char) < 128 and half_char)
                or (x + font_size > width and (not half_char or ord(char) > 128))
            ):
                y += font_size + line_spacing
                x = initial_x

            # 对控制字符的处理
            if char == "\n":
                y += font_size + line_spacing
                x = initial_x
                continue
            elif char == "\t":
                x = ((x // font_size) + 1) * font_size + initial_x % font_size
                continue
            elif ord(char) < 0x20:
                continue

            # 超过范围的字符不会显示*
            if x > width or y > height:
                continue

            # 获取字体的点阵数据
            self.fast_get_bitmap(char, bitmap_cache)

            # 由于颜色参数提前决定了调色板
            # 这里按照放缩/无放缩进行显示即可
            if font_resize:
                display.blit(
                    framebuf.FrameBuffer(
                        self._hlsb_font_size(bitmap_cache, font_size, self.font_size),
                        font_size,
                        font_size,
                        framebuf.MONO_HLSB,
                    ),
                    x,
                    y,
                    alpha_color,
                    palette,
                )
            else:
                display.blit(framebuf_, x, y, alpha_color, palette)

            # 英文字符半格显示
            if half_char and ord(char) < 128:
                x += font_size >> 1
            else:
                x += font_size

        display.show() if show else 0

    # @micropython.native
    # @timed_function
    def _fast_get_index(self, word: str) -> int:
        """
        获取索引，利用分块加速二分收敛速度
        Args:
            word: 字符

        Returns:
            字符在字体文件中的索引，如果未找到则返回 -1
        """
        word_code = ord(word)
        # 超出范围直接返回
        if not (self.font_begin <= word_code <= self.font_end):
            return -1
        font = self.font
        start = _HEADER_LEN
        end = self.start_bitmap
        if not self.load_into_mem:
            for i, (b, e) in enumerate(_UNICODE_BLOCK_RANGE):
                if b <= word_code <= e and self.block_boundary[i] is not None:
                    start, end = self.block_boundary[i]
                    break

        # 二分法查询
        if self.enable_mem_index:
            cache = self.FontIndexCache
            start = (start - _HEADER_LEN) // 2
            end = (end - _HEADER_LEN) // 2
            while start <= end:
                mid = (start + end) >> 1
                target_code = cache[mid]
                if word_code == target_code:
                    return mid
                elif word_code < target_code:
                    end = mid - 1
                else:
                    start = mid + 1
        else:
            while start <= end:
                mid = ((start + end) >> 2) * 2
                font.seek(mid, 0)
                target_code = struct.unpack(">H", font.read(2))[0]
                if word_code == target_code:
                    return (mid - _HEADER_LEN) >> 1
                elif word_code < target_code:
                    end = mid - 2
                else:
                    start = mid + 2
        return -1

    # @timed_function
    # @micropython.native
    def _hlsb_font_size(
        self, byte_data: bytearray, new_size: int, old_size: int
    ) -> bytearray:
        # 缩放比例进行反向处理是为了利用浮点乘法提高性能
        scale_inverted = old_size / new_size
        _temp = bytearray(new_size * ((new_size >> 3) + 1))
        _new_index = -1
        for _col in range(new_size):
            col_factor = int(_col * scale_inverted) * old_size
            for _row in range(new_size):
                new_bit_index = _row % 8
                if new_bit_index == 0:
                    _new_index += 1
                _old_index = col_factor + int(_row * scale_inverted)
                _temp[_new_index] = _temp[_new_index] | (
                    (byte_data[_old_index >> 3] >> (7 - _old_index % 8) & 1)
                    << (7 - new_bit_index)
                )
        return _temp

    # @timed_function
    def fast_get_bitmap(self, word: str, buff: bytearray):
        """获取点阵数据"""
        if self.load_into_mem:
            bitmap = self.all_font_data.get(ord(word), None)
            if bitmap is None:
                print("未找到字符：", word)
                # 这里不要使用固定长度数据，可能引起buff大小变化
                # 字体缺失生成一个实心像素块
                for i in range(len(buff)):
                    buff[i] = 0xFF
                return
            # if len(buff) < self.bitmap_size:
            #     buff[:] = bitmap[: len(buff)]
            # else:
            buff[: self.bitmap_size] = bitmap
        else:
            index = self._fast_get_index(word)
            if index == -1:
                print("未找到字符：", word)
                for i in range(len(buff)):
                    buff[i] = 0xFF
                return

            self.font.seek(self.start_bitmap + index * self.bitmap_size, 0)
            self.font.readinto(buff)

    def close_file(self):
        """关闭文件流。！！！在退出程序前必须手动调用"""
        self.font.close()

    def __init__(
        self,
        font_file,
        enable_mem_index=False,
        enable_bitmap_cache=False,
        load_into_mem=False,
    ):
        """
        Args:
            font_file: 字体文件路径
            enable_mem_index: 启用内存索引，将索引信息全部载入内存，更快速，每个索引2字节，内存小的机器慎用
            enable_block_index: 启用分块索引，根据unicode区段，先进行分块，初始化时间较长
            enable_bitmap_cache: 启用点阵缓存，在类成员中申请bytearray对象，避免频繁创建
            load_in_mem: 载入全部字体数据到内存，如果开启则忽略内存索引和分块索引，内存小的机器慎用

        """
        self.font_file = font_file
        # 载入字体文件
        self.font = open(font_file, "rb")
        # 获取字体文件头
        #   字体文件头大小 16 byte ,按照顺序依次是
        #       2 byte 文件标识
        #       1 byte 版本号
        #       1 byte 映射方式
        #       3 byte 位图开始字节
        #       1 byte 字号
        #       1 byte 单字点阵字节大小
        #       7 byte 保留
        self.bmf_info = self.font.read(_HEADER_LEN)

        # 判断字体是否正确
        #   文件头和常用的图像格式 BMP 相同，需要添加版本验证来辅助验证
        if self.bmf_info[0:2] != b"BM":
            raise TypeError("字体文件格式不正确: " + font_file)
        self.version = self.bmf_info[2]
        if self.version != 3:
            raise TypeError("字体文件版本不正确: " + str(self.version))

        # 目前映射方式并没有加以验证，原因是 MONO_HLSB 最易于处理
        self.map_mode = self.bmf_info[3]

        # 位图数据位于文件尾，需要通过位图开始字节来确定字体数据实际位置
        self.start_bitmap = struct.unpack(">I", b"\x00" + self.bmf_info[4:7])[0]
        # 默认的文字字号，用于缩放方面的处理
        self.font_size = self.bmf_info[7]
        # 用来定位字体数据位置
        self.bitmap_size = self.bmf_info[8]

        # 查询字体空间范围
        self.font_begin = struct.unpack(">H", self.font.read(2))[0]
        self.font.seek(self.start_bitmap - 2, 0)
        self.font_end = struct.unpack(">H", self.font.read(2))[0]
        word_num = (self.start_bitmap - _HEADER_LEN) // 2

        # 点阵数据缓存
        if enable_bitmap_cache:
            self.bitmap_cache = bytearray(ceil(self.font_size * self.font_size / 8))
        else:
            self.bitmap_cache = None

        # 全部数据载入内存
        self.font.seek(_HEADER_LEN, 0)
        self.load_into_mem = load_into_mem
        if load_into_mem:
            # 存储全部字体数据
            self.all_font_data: dict[int, bytes] = {}
            for word_index in range(word_num):
                self.font.seek(_HEADER_LEN + word_index * 2, 0)
                word_code = struct.unpack(">H", self.font.read(2))[0]
                self.font.seek(self.start_bitmap + word_index * self.bitmap_size, 0)
                data = self.font.read(self.bitmap_size)
                self.all_font_data[word_code] = data
            gc.collect()
            return

        # 建立内存索引
        self.enable_mem_index = enable_mem_index
        if enable_mem_index:
            self.FontIndexCache = struct.unpack(
                f">{word_num}H", self.font.read(self.start_bitmap - _HEADER_LEN)
            )

        # 建立分块索引
        self.block_boundary: list = [None for _ in range(3)]
        font = self.font
        block_num = len(_UNICODE_BLOCK_RANGE)
        font.seek(_HEADER_LEN, 0)
        len_ = 1000
        not_eof = True
        block = 0
        find_start = False
        start, end = 0, 0
        while not_eof:
            if len_ + font.tell() > self.start_bitmap:
                len_ = self.start_bitmap - font.tell()
                not_eof = False
            tmp = struct.unpack(f">{len_//2}H", font.read(len_))
            word_index = 0
            for word_code in tmp:
                # 注意：字体文件索引空间是线性的
                # 第一次满足分块 就记录此时索引为分块起始索引
                # 直到找到不满足分块的 记录索引为分块结束索引，然后找到其他分块的索引
                for i, (b, e) in enumerate(_UNICODE_BLOCK_RANGE):
                    if b <= word_code <= e:
                        if find_start:
                            break
                        else:
                            block = i
                            find_start = True
                            start = font.tell() - len_ + (word_index * 2)
                            break
                    elif find_start and i == block:
                        end = font.tell() - len_ + (word_index * 2)
                        find_start = False
                        self.block_boundary[block] = (start, end)

                if block == block_num:
                    not_eof = False
                    break
                word_index += 1
        if find_start:
            self.block_boundary[block] = (start, self.start_bitmap)
        gc.collect()
