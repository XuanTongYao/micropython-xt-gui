"""
MIT License

Copyright (c) 2019 Ivan Belokobylskiy

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

# st7789 tft driver in MicroPython based on devbis' st7789py_mpy module from
# https://github.com/devbis/st7789py_mpy.

# I've modified and simplified some of them to make better use of framebuf.


import time, framebuf
from micropython import const
import ustruct as struct
from machine import SPI

# commands
ST7789_NOP = const(0x00)
ST7789_SWRESET = const(0x01)
ST7789_RDDID = const(0x04)
ST7789_RDDST = const(0x09)

ST7789_SLPIN = const(0x10)
ST7789_SLPOUT = const(0x11)
ST7789_PTLON = const(0x12)
ST7789_NORON = const(0x13)

ST7789_INVOFF = const(0x20)
ST7789_INVON = const(0x21)
ST7789_DISPOFF = const(0x28)
ST7789_DISPON = const(0x29)
ST7789_CASET = const(0x2A)
ST7789_RASET = const(0x2B)
ST7789_RAMWR = const(0x2C)
ST7789_RAMRD = const(0x2E)

ST7789_PTLAR = const(0x30)
ST7789_VSCRDEF = const(0x33)
ST7789_COLMOD = const(0x3A)
ST7789_MADCTL = const(0x36)
ST7789_VSCSAD = const(0x37)

ST7789_MADCTL_MY = const(0x80)
ST7789_MADCTL_MX = const(0x40)
ST7789_MADCTL_MV = const(0x20)
ST7789_MADCTL_ML = const(0x10)
ST7789_MADCTL_BGR = const(0x08)
ST7789_MADCTL_MH = const(0x04)
ST7789_MADCTL_RGB = const(0x00)

ST7789_RDID1 = const(0xDA)
ST7789_RDID2 = const(0xDB)
ST7789_RDID3 = const(0xDC)
ST7789_RDID4 = const(0xDD)

COLOR_MODE_65K = const(0x50)
COLOR_MODE_262K = const(0x60)
COLOR_MODE_12BIT = const(0x03)
COLOR_MODE_16BIT = const(0x05)
COLOR_MODE_18BIT = const(0x06)
COLOR_MODE_16M = const(0x07)

# Color definitions
BLACK = const(0x0000)
BLUE = const(0x001F)
RED = const(0xF800)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)

_ENCODE_PIXEL = ">H"
_ENCODE_POS = ">HH"

_BUFFER_SIZE = const(256)


def _encode_pos(x, y):
    """Encode a postion into bytes."""
    return struct.pack(_ENCODE_POS, x, y)


def _encode_pixel(color):
    """Encode a pixel color into bytes."""
    return struct.pack(_ENCODE_PIXEL, color)


class ST7789:

    def __init__(
        self,
        spi: SPI,
        width,
        height,
        reset,
        dc,
        cs=None,
        backlight=None,
        xstart=0,
        ystart=0,
        rotation=0,
    ):
        """
        Initialize display.
        """
        if (width, height) != (240, 240) and (width, height) != (135, 240):
            raise ValueError(
                "Unsupported display. Only 240x240 and 135x240 are supported."
            )

        self._display_width = self.width = width
        self._display_height = self.height = height
        self.spi = spi
        self.reset = reset
        self.dc = dc
        self.cs_n = cs
        self.backlight = backlight
        self._rotation = rotation % 4

        self.xstart = xstart
        self.ystart = ystart

        self.spi.write(bytes(0xFF))  #

        self.hard_reset()
        self.soft_reset()
        self.sleep_mode(False)

        self._set_color_mode(COLOR_MODE_65K | COLOR_MODE_16BIT)
        time.sleep_ms(50)
        self.rotation(self._rotation)
        self.inversion_mode(True)
        time.sleep_ms(10)
        self.write(ST7789_NORON)
        time.sleep_ms(10)
        if backlight is not None:
            backlight.value(1)
        self.set_fullscreen()
        self.clear_gddram()
        self.write(ST7789_DISPON)
        time.sleep_ms(500)

    def write(self, command=None, data=None):
        """SPI write to the device: commands and data."""
        if self.cs_n:
            self.cs_n.off()

        if command is not None:
            self.dc.off()
            self.spi.write(bytes([command]))
        if data is not None:
            self.dc.on()
            self.spi.write(data)

        if self.cs_n:
            self.cs_n.on()

    def hard_reset(self):
        """
        Hard reset display.
        """
        if self.cs_n:
            self.cs_n.off()

        if self.reset:
            self.reset.on()
        time.sleep_ms(50)
        if self.reset:
            self.reset.off()
        time.sleep_ms(50)
        if self.reset:
            self.reset.on()
        time.sleep_ms(150)

        if self.cs_n:
            self.cs_n.on()

    def soft_reset(self):
        """
        Soft reset display.
        """
        self.write(ST7789_SWRESET)
        time.sleep_ms(150)

    def sleep_mode(self, value: bool):
        """
        Enable or disable display sleep mode.
        """
        if value:
            self.write(ST7789_SLPIN)
        else:
            self.write(ST7789_SLPOUT)

    def inversion_mode(self, value: bool):
        """
        Enable or disable display inversion mode.
        """
        if value:
            self.write(ST7789_INVON)
        else:
            self.write(ST7789_INVOFF)

    def _set_color_mode(self, mode):
        """
        Set display color mode.

        Args:
            mode (int): color mode
                COLOR_MODE_65K, COLOR_MODE_262K, COLOR_MODE_12BIT,
                COLOR_MODE_16BIT, COLOR_MODE_18BIT, COLOR_MODE_16M
        """
        self.write(ST7789_COLMOD, bytes([mode & 0x77]))

    def rotation(self, rotation):
        """
        Set display rotation.

        Args:
            rotation (int): 0-Portrait, 1-Landscape, 2-Inverted Portrait,
            3-Inverted Landscape
        """
        self._rotation = rotation % 4
        if self._rotation == 0:  # Portrait
            madctl = ST7789_MADCTL_RGB
            self.width = self._display_width
            self.height = self._display_height
            if self._display_width == 135:
                self.xstart = 52
                self.ystart = 40

        elif self._rotation == 1:  # Landscape
            madctl = ST7789_MADCTL_MX | ST7789_MADCTL_MV | ST7789_MADCTL_RGB
            self.width = self._display_height
            self.height = self._display_width
            if self._display_width == 135:
                self.xstart = 40
                self.ystart = 53

        elif self._rotation == 2:  # Inverted Portrait
            madctl = ST7789_MADCTL_MX | ST7789_MADCTL_MY | ST7789_MADCTL_RGB
            self.width = self._display_width
            self.height = self._display_height
            if self._display_width == 135:
                self.xstart = 53
                self.ystart = 40
        else:  # Inverted Landscape
            madctl = ST7789_MADCTL_MV | ST7789_MADCTL_MY | ST7789_MADCTL_RGB
            self.width = self._display_height
            self.height = self._display_width
            if self._display_width == 135:
                self.xstart = 40
                self.ystart = 52

        self.write(ST7789_MADCTL, bytes([madctl]))

    def set_fullscreen(self):
        """设置显示窗口为全屏"""
        self.write(
            ST7789_CASET, _encode_pos(0 + self.xstart, self.width - 1 + self.xstart)
        )
        self.write(
            ST7789_RASET, _encode_pos(0 + self.ystart, self.height - 1 + self.ystart)
        )
        self.write(ST7789_RAMWR)

    def write_gddram(self, buffer):
        """在当前窗口写入GDDRAM数据"""
        self.write(ST7789_RAMWR, buffer)

    def clear_gddram(self):
        chunks, rest = divmod(self.width * self.height, _BUFFER_SIZE)
        pixel = _encode_pixel(0)
        self.dc.on()
        if chunks:
            data = pixel * _BUFFER_SIZE
            for _ in range(chunks):
                self.write(None, data)
        if rest:
            self.write(None, pixel * rest)


class ST7789_API(framebuf.FrameBuffer):
    def __init__(self, st7789: ST7789) -> None:
        self.st7789 = st7789
        st7789.set_fullscreen()
        self.width = st7789.width
        self.height = st7789.height
        self.buffer = bytearray(self.width * self.height * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)

    def clear(self):
        self.fill(0)
        self.update_frame()

    def update_frame(self):
        self.st7789.write_gddram(self.buffer)

    def show(self):
        self.st7789.write_gddram(self.buffer)
