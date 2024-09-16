import framebuf
from math import ceil, floor
import io
import deflate

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


def split_space(b: bytes, begin=0):
    begin_index = begin
    index = begin
    len_ = len(b)
    while index < len_:
        if b[index : index + 1].isspace():
            yield b[begin_index:index]
            begin_index = index + 1
        index += 1
    return


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


def rgb888_to_rgb565(r8, g8, b8, big_endian=False) -> int:
    r8 >>= 3
    g8 >>= 2
    b8 >>= 3
    if big_endian:
        return (b8 << 11) | (g8 << 5) | r8
    else:
        return (r8 << 11) | (g8 << 5) | b8


# 图像格式枚举
PBM_P4 = const(0)
PNG = const(1)


class Texture2D:

    PNG_TURECOLOR = 2
    PNG_GRAY = 0

    def __decoder_pbm(self, stream: io.BufferedReader | io.BytesIO | None = None):
        if stream is None:
            if isinstance(self.data, bytearray):
                return
            stream = self.data
            row_buff = bytearray(ceil(self.w / 8))
            for _ in range(self.h):
                stream.readinto(row_buff)
                yield row_buff
        else:
            self.data = bytearray(stream.read(ceil(self.w / 8) * self.h))

    def __decoder_png(self, stream: io.BufferedReader | io.BytesIO | None = None):
        """
        Args:
            stream: 如果传入IO流，则从流中解码数据到self.data。如果为None，则返回一条行扫描线的数据。
        """
        one_line = False
        if stream is None:
            if isinstance(self.data, bytearray):
                return
            else:
                one_line = True
                stream = self.data
                if self.colortype == Texture2D.PNG_TURECOLOR:
                    row_buff = bytearray(self.w * 2)
                else:
                    row_buff = bytearray(ceil(self.w / (8 / self.bitdepth)))
        elif not isinstance(self.data, bytearray):
            return

        last_scanline = memoryview(bytearray(self.SCANLINE_BYTES))
        scanline = memoryview(bytearray(self.SCANLINE_BYTES))
        scanline_remain_byte = 0
        data_offset = 0
        while True:
            chunk_len = int.from_bytes(stream.read(4), "big")
            chunk_type = stream.read(4)
            if len(chunk_type) != 4:
                raise ValueError("IEND not found")

            if chunk_type == b"IEND" or chunk_type == b"IDAT":
                chunk_data = stream.read(chunk_len)
                chunk_crc = stream.read(4)
                crc = crc32(chunk_type + chunk_data)
                if crc.to_bytes(4, "big") != chunk_crc:
                    raise ValueError("CRC check failed")

                if chunk_type == b"IEND":
                    self.img_type = PNG
                    if not one_line:
                        stream.close()
                    return
                else:

                    def paeth_predictor(a, b, c):
                        p = a + b - c
                        pa = abs(p - a)
                        pb = abs(p - b)
                        pc = abs(p - c)
                        if pa <= pb and pa <= pc:
                            return a
                        elif pb <= pc:
                            return b
                        else:
                            return c

                    # 解码: 解压->从解压数据中读取一条完整的扫描线数据->解码过滤器->解码像素数据
                    with io.BytesIO(chunk_data) as c_data, deflate.DeflateIO(
                        c_data, deflate.ZLIB, 13
                    ) as d:
                        while True:
                            if scanline_remain_byte == 0:
                                filter = d.read(1)
                                if len(filter) == 1:
                                    scanline_remain_byte = self.SCANLINE_BYTES
                                else:
                                    break
                            # 读取扫描线样本
                            n = d.readinto(scanline[-scanline_remain_byte:])
                            scanline_remain_byte -= n

                            if scanline_remain_byte != 0:
                                break

                            # 解码过滤器
                            if filter == b"\x01":
                                # 差分
                                for x in range(self.SCANLINE_BYTES):
                                    a = x - self.bpp
                                    raw_bpp = 0 if a < 0 else scanline[a]
                                    scanline[x] = (scanline[x] + raw_bpp) % 256
                            elif filter == b"\x02":
                                # 向上差分
                                for x in range(self.SCANLINE_BYTES):
                                    prior = last_scanline[x]
                                    scanline[x] = (scanline[x] + prior) % 256
                            elif filter == b"\x03":
                                # 平均
                                for x in range(self.SCANLINE_BYTES):
                                    a = x - self.bpp
                                    raw_bpp = 0 if a < 0 else scanline[a]
                                    prior = last_scanline[x]
                                    scanline[x] = (
                                        scanline[x] + floor((raw_bpp + prior) / 2)
                                    ) % 256
                            elif filter == b"\x04":
                                # 样条差分
                                for x in range(self.SCANLINE_BYTES):
                                    a = x - self.bpp
                                    raw_bpp = 0 if a < 0 else scanline[a]
                                    prior = last_scanline[x]
                                    prior_bpp = 0 if a < 0 else last_scanline[a]
                                    scanline[x] = (
                                        scanline[x]
                                        + paeth_predictor(raw_bpp, prior, prior_bpp)
                                    ) % 256
                            last_scanline[:] = scanline

                            # 解码行像素数据
                            if isinstance(self.data, bytearray):
                                dataview = memoryview(self.data)
                                if self.colortype == Texture2D.PNG_GRAY:
                                    dataview[
                                        data_offset : data_offset + self.SCANLINE_BYTES
                                    ] = scanline
                                    data_offset += self.SCANLINE_BYTES
                                else:
                                    for x in range(0, self.SCANLINE_BYTES, 3):
                                        px = rgb888_to_rgb565(
                                            scanline[x],
                                            scanline[x + 1],
                                            scanline[x + 2],
                                        ).to_bytes(2, "big")
                                        dataview[data_offset : data_offset + 2] = px
                                        data_offset += 2
                            else:
                                dataview = memoryview(row_buff)
                                if self.colortype == Texture2D.PNG_GRAY:
                                    yield scanline
                                    data_offset += self.SCANLINE_BYTES
                                else:
                                    data_offset = 0
                                    for x in range(0, self.SCANLINE_BYTES, 3):
                                        px = rgb888_to_rgb565(
                                            scanline[x],
                                            scanline[x + 1],
                                            scanline[x + 2],
                                        ).to_bytes(2, "big")
                                        dataview[data_offset : data_offset + 2] = px
                                        data_offset += 2
                                    yield row_buff
            else:
                stream.seek(chunk_len + 4, 1)

    def __parse_header_pbm(self, img: io.BufferedReader | io.BytesIO) -> int | None:
        img.seek(0)
        if img.read(2) != b"P4":
            return

        w = read_to_space(img, 3)
        h = read_to_space(img)
        if w.isdigit() and h.isdigit():
            self.w = int(w)
            self.h = int(h)
            self.start_index = 2 + len(w) + len(h) + 3
            return PBM_P4

    def __parse_header_png(self, img: io.BufferedReader | io.BytesIO) -> int | None:
        img.seek(0)
        if img.read(8) != b"\x89PNG\r\n\x1A\n":
            return

        IHAR_len = int.from_bytes(img.read(4), "big")
        IHAR_type = img.read(4)
        if IHAR_type != b"IHDR":
            raise ValueError("Invalid PNG file")

        IHAR_data = img.read(IHAR_len)
        IHAR_crc = img.read(4)
        if crc32(IHAR_type + IHAR_data).to_bytes(4, "big") != IHAR_crc:
            raise ValueError("IHDR CRC mismatch")

        self.w = int.from_bytes(IHAR_data[0:4], "big")
        self.h = int.from_bytes(IHAR_data[4:8], "big")
        self.bitdepth = IHAR_data[8]
        if self.bitdepth == 16:
            # 不支持16位样本色深
            raise TypeError("Unsupported bitdepth")
        self.colortype = IHAR_data[9]
        if self.colortype & 0x01 or self.colortype & 0x04:
            raise TypeError("Color palette and Alpha channel not supported")
        if IHAR_data[10] != 0:
            raise ValueError("Invalid compression method")
        if IHAR_data[11] != 0:
            raise ValueError("Invalid filter method")
        self.interlace = IHAR_data[12]
        if self.interlace != 0:
            # 不支持隔行扫描
            raise TypeError("Interlaced scanning is not supported")
        return PNG

    def __parse_header_jpeg(self, stream: io.BufferedReader | io.BytesIO) -> int | None:
        stream.seek(0)
        pass

    def _parse_header(self, stream: io.BufferedReader | io.BytesIO) -> int | None:
        """
        Returns:
            图像类型，为None表示解析失败
        """
        # 不同格式逐个尝试解析
        if self.__parse_header_pbm(stream) is not None:
            return PBM_P4
        elif self.__parse_header_png(stream) is not None:
            return PNG

    def __init__(
        self, raw_data: bytes | str, load_into_mem=False, *, bitmap=True
    ) -> None:
        """
        Args:
            raw_data: 路径或原始数据
            load_into_mem: 图像数据全部加载到内存中. 如果raw_data传入bytes-like对象，则强制加载到内存中.
            bitmap: 将数据转换为适当的bitmap格式. 如果关闭，则存储原始数据. load_into_mem为True时才会生效.
        """
        self.is_bitmap = bitmap if load_into_mem else False
        self.img_type = None
        if isinstance(raw_data, str):
            img = open(raw_data, "rb")
            del raw_data
        else:
            load_into_mem = True
            img = io.BytesIO(raw_data)
            del raw_data

        # 解析文件头并检查是否支持该类型
        img_type = self._parse_header(img)
        if img_type is None:
            raise ValueError("Unsupported image format")

        # 对不同格式进行不同处理
        if img_type == PBM_P4:
            self.img_type = PBM_P4
            if load_into_mem:
                # PBM_P4原始数据就是bitmap格式的
                self.is_bitmap = True
                for _ in self.__decoder_pbm(img):
                    pass
            elif not isinstance(img, io.BytesIO):
                self.data = img
                return
        elif img_type == PNG:
            # 计算每个像素的字节数
            if self.colortype == Texture2D.PNG_GRAY:
                bpp = self.bitdepth / 8
                self.bpp = ceil(bpp)
                self.SCANLINE_BYTES = ceil(self.w * bpp)
                # 创建图像缓存
                if self.is_bitmap:
                    self.data = bytearray(ceil(self.w / (8 / self.bitdepth)) * self.h)
            else:
                bpp = self.bitdepth * 3 / 8
                self.bpp = ceil(bpp)
                self.SCANLINE_BYTES = ceil(self.w * bpp)
                if self.is_bitmap:
                    self.data = bytearray(self.w * 2 * self.h)
                    # PNG没有RGB565的像素格式

            if self.is_bitmap:
                for _ in self.__decoder_png(img):
                    pass
            else:
                self.img_type = PNG
                self.start_index = 8
                self.data = img
                return
        img.close()

    def __iter__(self):
        if self.is_bitmap or isinstance(self.data, bytearray):
            return
        self.data.seek(self.start_index)
        if self.img_type == PBM_P4:
            for scanline_data in self.__decoder_pbm():
                yield framebuf.FrameBuffer(scanline_data, self.w, 1, framebuf.MONO_HLSB)
            # unit_buff = bytearray(1)
            # for _ in range(self.h):
            #     remaining_x = self.w
            #     while remaining_x > 0:
            #         self.data.readinto(unit_buff)
            #         if remaining_x >= 8:
            #             yield framebuf.FrameBuffer(
            #                 unit_buff, 8, 1, framebuf.MONO_HLSB
            #             ), False
            #         else:
            #             yield framebuf.FrameBuffer(
            #                 unit_buff, remaining_x, 1, framebuf.MONO_HLSB
            #             ), True
            #         remaining_x -= 8
        elif self.img_type == PNG:
            for scanline_data in self.__decoder_png():
                yield framebuf.FrameBuffer(scanline_data, self.w, 1, framebuf.RGB565)
