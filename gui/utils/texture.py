import gc
import io
import framebuf
from math import ceil, floor, log2
import deflate
from .core import crc32, read_to_space, rgb888_to_rgb565

# 图像格式枚举
PBM_P4 = const(0)
PNG = const(1)


class Texture2D:
    """
    2D纹理类,用于图像绘制: 在该对象中直接存储framebuf.FrameBuffer形式的图像数据等。

    常见公开属性:
    w: 宽
    h: 高
    type: 图像类型，为 TEX_BITMAP (完整点阵图)或 TEX_STREAMING (流式加载)
    palette_used: 使用调色板
    img_format: 图像格式 PNG JPEG PBM_P4等
    color_mode: 颜色模式，用于确定像素的格式，例如framebuf.RGB565

    bitmap_frame: bitmap帧数据 (TEX_BITMAP 类型独有)
    palette: 调色板帧数据 (使用调色板时存在，灰度图像默认不使用)

    bitdepth: 色深(灰度图像独有)

    私有属性:
    __bitmap_buf : 完整点阵图的缓冲区，用于 TEX_BITMAP 类型。
    __scanline_buf : 一条扫描线的缓冲区, 用于 TEX_STREAMING 类型。
    __scanline_frame : 一条扫描线的的帧数据, 用于 TEX_STREAMING 类型。
    __data : 保存二进制数据流, 用于 TEX_STREAMING 类型。

    """

    # 抽象实现类型
    # bitmap纹理：以bitmap格式存储像素数据在内存中，绘制速度最快，占用内存很高。
    TEX_BITMAP = const(0)
    # 流式纹理：以流式方式按扫描线(行)读取像素数据，绘制时才会解码为bitmap，通常用于从文件读取。
    TEX_STREAMING = const(1)

    PNG_GRAY = const(0)
    PNG_TURECOLOR = const(2)
    PNG_INDEX_COLOR = const(3)

    def __parse_header(self, stream: io.BufferedReader | io.BytesIO) -> int | None:
        """
        解析文件头->计算辅助信息->记录图像数据的起始位置->
        确定颜色模式、是否使用调色板->创建完整点整图缓冲区或扫描线缓冲区->

        Returns:
            图像格式，为None表示解析失败
        """
        # 不同格式逐个尝试解析
        if self.__parse_header_pbm(stream) is not None:
            return PBM_P4
        elif self.__parse_header_png(stream) is not None:
            return PNG

    def __decode_into_mem(self, img):
        """每个__decoder_pbm内创建图像缓存，解码图像数据为bitmap到内存"""
        img_format = self.img_format
        if img_format == PBM_P4:
            for _ in self.__decoder_pbm(img):
                pass
        elif img_format == PNG:
            for _ in self.__decoder_png(img):
                pass

    def __init__(self, raw_data: bytes | str, bitmap=True) -> None:
        """
        Args:
            raw_data: 路径或原始数据
            bitmap: 将数据转换为适当的bitmap格式存储在内存中. 如果为False，则保持二进制流，绘制时解码.
        """
        gc.collect()
        self.type = Texture2D.TEX_BITMAP if bitmap else Texture2D.TEX_STREAMING
        self.palette_used = False
        self.color_mode = framebuf.RGB565

        if isinstance(raw_data, str):
            img = open(raw_data, "rb")
        else:
            img = io.BytesIO(raw_data)
        del raw_data

        # 解析文件头并检查是否支持该类型
        self.img_format = self.__parse_header(img)
        gc.collect()
        if self.img_format is None:
            raise ValueError("Unsupported image format")

        # 创建帧数据
        if self.type == Texture2D.TEX_BITMAP:
            self.bitmap_frame = framebuf.FrameBuffer(
                self.__bitmap_buf, self.w, self.h, self.color_mode
            )
        else:
            self.__scanline_frame = framebuf.FrameBuffer(
                self.__scanline_buf, self.w, 1, self.color_mode
            )

        # 解析图像数据或保持二进制流
        gc.collect()
        if self.type == Texture2D.TEX_BITMAP:
            self.__decode_into_mem(img)
        else:
            self.__data = img
            return
        img.close()

    def __iter__(self):
        """
        Yields:
            每行的帧数据
        """
        if self.type == Texture2D.TEX_BITMAP:
            return
        color_mode = self.color_mode
        self.__data.seek(self.__start_index)
        if self.img_format == PBM_P4:
            for scanline_data in self.__decoder_pbm():
                yield self.__scanline_frame
        elif self.img_format == PNG:
            for scanline_data in self.__decoder_png():
                yield framebuf.FrameBuffer(scanline_data, self.w, 1, color_mode)

    # 文件头解析的具体实现
    def __parse_header_pbm(self, img: io.BufferedReader | io.BytesIO) -> int | None:
        img.seek(0)
        if img.read(2) != b"P4":
            return

        w = read_to_space(img, 3)
        h = read_to_space(img)
        if w.isdigit() and h.isdigit():
            self.w = int(w)
            self.h = int(h)
            self.bitdepth = 1
            self.__start_index = 2 + len(w) + len(h) + 3

            # 确定颜色模式创建缓冲区
            self.color_mode = framebuf.MONO_HLSB
            if self.type == Texture2D.TEX_BITMAP:
                self.__bitmap_buf = bytearray(ceil(self.w / 8) * self.h)
            else:
                self.__scanline_buf = bytearray(ceil(self.w / 8))
            return PBM_P4

    def __parse_header_png(self, img: io.BufferedReader | io.BytesIO) -> int | None:
        img.seek(0)
        if img.read(8) != b"\x89PNG\r\n\x1A\n":
            return

        # 读取头信息
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
        self.bitdepth = self.__png_sample_bitdepth = IHAR_data[8]
        if self.bitdepth == 16:
            # 不支持16位样本色深
            raise TypeError("Unsupported bitdepth")
        self.png_type = IHAR_data[9]
        if self.png_type & 0x04:
            raise TypeError("Alpha channel not supported")
        if IHAR_data[10] != 0:
            raise ValueError("Invalid compression method")
        if IHAR_data[11] != 0:
            raise ValueError("Invalid filter method")
        interlace = IHAR_data[12]
        if interlace != 0:
            # 不支持隔行扫描
            raise TypeError("Interlaced scanning is not supported")

        # 计算每个像素的字节数
        if (
            self.png_type == Texture2D.PNG_GRAY
            or self.png_type == Texture2D.PNG_INDEX_COLOR
        ):
            bpp = self.bitdepth / 8
        else:
            bpp = self.bitdepth * 3 / 8
        self.__png_bpp = ceil(bpp)
        self.__png_scanline_len = ceil(self.w * bpp)

        # 寻找调色板
        if self.png_type == Texture2D.PNG_INDEX_COLOR:
            self.palette_used = True
            while True:
                chunk_len = int.from_bytes(img.read(4), "big")
                chunk_type = img.read(4)
                if len(chunk_type) != 4:
                    raise ValueError("PLTE not found")

                if chunk_type != b"PLTE":
                    img.seek(chunk_len + 4, 1)
                    continue

                # 读取块数据
                PLTE_data = img.read(chunk_len)
                PLTE_crc = img.read(4)
                crc = crc32(chunk_type + PLTE_data)
                if crc.to_bytes(4, "big") != PLTE_crc:
                    raise ValueError("CRC check failed")

                if chunk_len % 3 != 0:
                    raise ValueError("Invalid PLTE chunk")

                color_num = chunk_len // 3
                if color_num > 16:
                    bitdepth = 8
                elif color_num > 4:
                    bitdepth = 4
                elif color_num > 2:
                    bitdepth = 2
                else:
                    bitdepth = 1
                self.bitdepth = bitdepth
                self.palette = framebuf.FrameBuffer(
                    bytearray(color_num * 2), color_num, 1, framebuf.RGB565
                )
                for x in range(0, chunk_len, 3):
                    px = rgb888_to_rgb565(
                        PLTE_data[x], PLTE_data[x + 1], PLTE_data[x + 2], True
                    )
                    self.palette.pixel(x // 3, 0, px)
                break

        self.__start_index = 8

        # 确定颜色模式创建缓冲区
        if self.png_type in [Texture2D.PNG_GRAY, Texture2D.PNG_INDEX_COLOR]:
            if self.bitdepth == 1:
                self.color_mode = framebuf.MONO_HLSB
            elif self.bitdepth == 2:
                self.color_mode = framebuf.GS2_HMSB
            elif self.bitdepth == 4:
                self.color_mode = framebuf.GS4_HMSB
            else:
                self.color_mode = framebuf.GS8
            if self.type == Texture2D.TEX_BITMAP:
                self.__bitmap_buf = bytearray(
                    ceil(self.w / (8 / self.bitdepth)) * self.h
                )
            else:
                self.__scanline_buf = bytearray(ceil(self.w / (8 / self.bitdepth)))
        else:
            self.color_mode = framebuf.RGB565
            if self.type == Texture2D.TEX_BITMAP:
                self.__bitmap_buf = bytearray(self.w * 2 * self.h)
            else:
                self.__scanline_buf = bytearray(self.w * 2)
        return PNG

    def __parse_header_jpeg(self, stream: io.BufferedReader | io.BytesIO) -> int | None:
        stream.seek(0)
        pass

    # 解码器的具体实现
    def __decoder_pbm(self, stream: io.BufferedReader | io.BytesIO | None = None):
        if stream is None:
            stream = self.__data
            for _ in range(self.h):
                stream.readinto(self.__scanline_buf)
                yield self.__scanline_buf
        else:
            stream.readinto(self.__bitmap_buf)

    def __decoder_png(self, stream: io.BufferedReader | io.BytesIO | None = None):
        """
        Args:
            stream: 如果传入IO流，则从流中解码数据到self.data。如果为None，则返回一条行扫描线的数据。
        """
        if stream is None:
            stream = self.__data

        last_scanline = memoryview(bytearray(self.__png_scanline_len))
        scanline = memoryview(bytearray(self.__png_scanline_len))
        if (
            self.png_type == Texture2D.PNG_GRAY
            or self.png_type == Texture2D.PNG_INDEX_COLOR
        ):
            predicted_wbits = ceil(
                log2(ceil(self.w * self.__png_sample_bitdepth / 8) * self.h)
            )
        else:
            predicted_wbits = ceil(
                log2(ceil(self.w * self.__png_sample_bitdepth * 3 / 8) * self.h)
            )

        scanline_remain_byte = 0
        data_offset = 0
        row = 0
        if self.type == Texture2D.TEX_BITMAP:
            dataview = memoryview(self.__bitmap_buf)
        else:
            dataview = memoryview(self.__scanline_buf)
        while True:
            chunk_len = int.from_bytes(stream.read(4), "big")
            chunk_type = stream.read(4)
            if len(chunk_type) != 4:
                raise ValueError("IEND not found")

            if chunk_type not in [b"IEND", b"IDAT"]:
                stream.seek(chunk_len + 4, 1)
                continue

            # 读取块数据
            chunk_data = stream.read(chunk_len)
            chunk_crc = stream.read(4)
            crc = crc32(chunk_type + chunk_data)
            if crc.to_bytes(4, "big") != chunk_crc:
                raise ValueError("CRC check failed")

            if chunk_type == b"IEND":
                return

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
                c_data, deflate.ZLIB, predicted_wbits
            ) as d:
                gc.collect()
                # print(micropython.mem_info(1))
                while True:
                    if scanline_remain_byte == 0:
                        filter = d.read(1)
                        if len(filter) == 1:
                            scanline_remain_byte = self.__png_scanline_len
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
                        for x in range(self.__png_scanline_len):
                            a = x - self.__png_bpp
                            raw_bpp = 0 if a < 0 else scanline[a]
                            scanline[x] = (scanline[x] + raw_bpp) % 256
                    elif filter == b"\x02":
                        # 向上差分
                        for x in range(self.__png_scanline_len):
                            prior = last_scanline[x]
                            scanline[x] = (scanline[x] + prior) % 256
                    elif filter == b"\x03":
                        # 平均
                        for x in range(self.__png_scanline_len):
                            a = x - self.__png_bpp
                            raw_bpp = 0 if a < 0 else scanline[a]
                            prior = last_scanline[x]
                            scanline[x] = (
                                scanline[x] + floor((raw_bpp + prior) / 2)
                            ) % 256
                    elif filter == b"\x04":
                        # 样条差分
                        for x in range(self.__png_scanline_len):
                            a = x - self.__png_bpp
                            raw_bpp = 0 if a < 0 else scanline[a]
                            prior = last_scanline[x]
                            prior_bpp = 0 if a < 0 else last_scanline[a]
                            scanline[x] = (
                                scanline[x] + paeth_predictor(raw_bpp, prior, prior_bpp)
                            ) % 256
                    last_scanline[:] = scanline

                    # 解码行像素数据
                    if self.type == Texture2D.TEX_BITMAP:
                        if self.png_type == Texture2D.PNG_GRAY:
                            dataview[
                                data_offset : data_offset + self.__png_scanline_len
                            ] = scanline
                            data_offset += self.__png_scanline_len
                        elif self.png_type == Texture2D.PNG_TURECOLOR:
                            for x in range(0, self.__png_scanline_len, 3):
                                px = rgb888_to_rgb565(
                                    scanline[x],
                                    scanline[x + 1],
                                    scanline[x + 2],
                                ).to_bytes(2, "big")
                                dataview[data_offset : data_offset + 2] = px
                                data_offset += 2
                        else:
                            # 部分图像编辑器(例如PS)最低只支持8位的样本色深，实际颜色可能小于8位
                            # PNG标准允许1、2、4位的样本色深

                            # 8位样本色深，实际颜色数为16(4位)的扫描线: 0x0X 0x0X ...
                            # 样本实际上只有低4位存在数据需要把两个样本合并成一个字节

                            # 4位样本色深，实际颜色数为4(2位)的扫描线: 0b00XX_00XX 0b00XX_00XX ...
                            # 样本实际上只有5，4，1，0位存在数据需要把四个样本合并成一个字节

                            # 当样本色深与颜色数不匹配时，样本之间存在空白位，否则样本之间是紧凑的

                            # 对于存在空白位的情况，根据扫描线挨个读取字节，从字节提取样本，将样本紧凑化，
                            # 如果使用了framebuf.FrameBuffer，可以使用pixel()直接设置每一个像素为样本
                            # 也可以构造一个调色板然后使用blit()转换
                            if self.bitdepth == self.__png_sample_bitdepth:
                                dataview[
                                    data_offset : data_offset + self.__png_scanline_len
                                ] = scanline
                                data_offset += self.__png_scanline_len
                            else:
                                col = 0
                                sample_per_byte = 8 // self.__png_sample_bitdepth
                                for byte_data in scanline:
                                    # 读取字节
                                    mask = 0xFF
                                    for i in range(1, sample_per_byte + 1):
                                        # 从字节提取样本
                                        shift = 8 - (self.__png_sample_bitdepth * (i))
                                        self.bitmap_frame.pixel(
                                            col, row, (byte_data & mask) >> shift
                                        )
                                        col += 1
                                        mask >>= self.__png_sample_bitdepth
                                        if col == self.w:
                                            break
                                row += 1
                    else:
                        if self.png_type == Texture2D.PNG_GRAY:
                            yield scanline
                        elif self.png_type == Texture2D.PNG_TURECOLOR:
                            data_offset = 0
                            for x in range(0, self.__png_scanline_len, 3):
                                px = rgb888_to_rgb565(
                                    scanline[x],
                                    scanline[x + 1],
                                    scanline[x + 2],
                                ).to_bytes(2, "big")
                                dataview[data_offset : data_offset + 2] = px
                                data_offset += 2
                            yield self.__scanline_buf
                        else:
                            col = 0
                            sample_per_byte = 8 // self.__png_sample_bitdepth
                            for byte_data in scanline:
                                # 读取字节
                                mask = 0xFF
                                for i in range(1, sample_per_byte + 1):
                                    # 从字节提取样本
                                    shift = 8 - (self.__png_sample_bitdepth * (i))
                                    self.__scanline_frame.pixel(
                                        col, 0, (byte_data & mask) >> shift
                                    )
                                    col += 1
                                    mask >>= self.__png_sample_bitdepth
                                    if col == self.w:
                                        break
                            yield self.__scanline_buf


gc.collect()
