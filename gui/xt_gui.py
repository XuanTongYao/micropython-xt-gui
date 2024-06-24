from math import ceil
import utime
import framebuf
import gc
from .widgets.base import *

DEBUG = True


def timed_function(f, *args, **kwargs):
    myname = str(f).split(" ")[1]

    def new_func(*args, **kwargs):
        if DEBUG:
            t = utime.ticks_us()
            result = f(*args, **kwargs)
            delta = utime.ticks_diff(utime.ticks_us(), t)
            print("Function {} Time = {:6.3f}ms".format(myname, delta / 1000))
            return result
        else:
            return f(*args, **kwargs)

    return new_func


class XT_GUI:
    """XT_GUI类

    类会在底层创建一个XLayout基础布局容器，焦点切换和控件添加都是在
    该容器上完成的


    所有的Draw绘制函数都是对帧缓存进行的操作.
    如果没有写入到GDDRAM则不会显示到屏幕上.
    所有颜色都是RGB565.
    由于FrameBuffer的字节序固定为LE,传输到显示器的颜色信息可能有错误.
    目前光标影响性能，已经禁用
    为了高性能，除了实现相关功能，函数都没有进行严格类型检查
    ShowGUI函数会检查部分类型的遮蔽情况,决定是否重绘
    如果出现图像异常可以在ShowGUI之前调用DrawBackground强制重绘背景
    """

    def draw_binary_image(
        self,
        Data: bytes | str,
        PosXY,
        Color: int = WHITE,
        BColor: int | None = None,
        SizeWH=(1, 1),
        Format="pbm",
    ):
        """绘制二值化点阵图
        Args:
            Data: 不带文件头的数据或者文件路径
            PosXY: 起始位置
            Color: 前景颜色
            BColor: 背景颜色,如果为None则透明
            SizeWH: 宽高
            Format: 文件格式
        """
        X, Y = PosXY
        W, H = SizeWH
        Palette = framebuf.FrameBuffer(bytearray(4), 2, 1, framebuf.RGB565)
        Palette.pixel(1, 0, Color)
        ImgFrame = None
        if type(Data) is bytes:
            if Format == "pbm":
                ImgFrame = framebuf.FrameBuffer(
                    bytearray(Data), W, H, framebuf.MONO_HLSB
                )
        else:
            with open(Data, "rb") as Img:
                head = Img.readline()
                if head == b"P4\x0A":
                    W = int(Img.readline().decode("ASCII"))
                    H = int(Img.readline().decode("ASCII"))
                    Img = bytearray(Img.read(ceil(W / 8) * H))
                    ImgFrame = framebuf.FrameBuffer(Img, W, H, framebuf.MONO_HLSB)

        if ImgFrame is None:
            print("数据缺失或无法识别格式")
            return

        if BColor is None:
            self.display.blit(ImgFrame, X, Y, 0, Palette)
        else:
            Palette.pixel(0, 0, BColor)
            self.display.blit(ImgFrame, X, Y, -1, Palette)

    def draw_text(
        self,
        text: str,
        pos,
        color,
        layout_frame: FrameBuffer | None = None,
        overlap=True,
        t_font=None,
    ):
        x, y = pos
        font = self.font if t_font is None else t_font
        display = self.display if layout_frame is None else layout_frame
        font_size = font.font_size
        half = font_size >> 1
        palette = self.pa_cache
        palette.pixel(1, 0, color)
        word_frame = self._word_frame
        word_cache = self._word_cache
        for char in text:
            font.fast_get_bitmap(char, word_cache)
            if overlap:
                display.blit(word_frame, x, y, 0, palette)
            else:
                display.blit(word_frame, x, y, -1, palette)
            # X坐标偏移一个字，
            # 半角字符依照全角字符绘制的，只是坐标偏移不同，速度不会更快
            if 0 <= ord(char) <= 0x7F:
                x += half
            else:
                x += font_size

    def draw_background(self):
        self.display.fill(0)

    # def DrawCursor(self):
    #     Palette = self.PaCache
    #     Palette.pixel(1, 0, self.CursorC)
    #     self.Display.blit(
    #         self.CursorFrame, self.CursorPosX, self.CursorPosY, 0, Palette
    #     )

    # def cursor_move(self, base_px: int, axis_x_zoom, axis_y_zoom):
    #     self.CursorPosX += int(base_px * axis_x_zoom)
    #     self.CursorPosY += int(base_px * axis_y_zoom)
    #     if self.CursorPosX > self.width:
    #         self.CursorPosX = self.width
    #     elif self.CursorPosX < 0:
    #         self.CursorPosX = 0
    #     if self.CursorPosY > self.height:
    #         self.CursorPosY = self.height
    #     elif self.CursorPosY < 0:
    #         self.CursorPosY = 0

    def add_widget(self, widget: XWidget):
        self._layout.add_widget(widget)

    # @timed_function
    def refrash_frame(self):
        """刷新帧，将帧数据写入显存"""
        self.display.update_frame()  # type: ignore

    @timed_function
    def show_gui(self):
        """绘制并显示整个GUI"""
        self._layout.draw_deliver()
        self.refrash_frame()

    def key_response(self, KEY_ID: int):
        """处理按键响应的函数"""
        if self.enter_widget_stack:
            func = self.enter_widget_stack[-1]._key_input
            if func is not None:
                ret_val = func(KEY_ID)
        else:
            if self._layout._key_input is not None:
                ret_val = self._layout._key_input(KEY_ID)
        if ret_val == ESC and len(self.enter_widget_stack):
            self.esc_widget()
        elif isinstance(ret_val, XCtrl):
            self.enter_widget(ret_val)

    def enter_widget(self, widget: XCtrl):
        self.enter_widget_stack.append(widget)

    def esc_widget(self):
        self.enter_widget_stack.pop()

    def __init__(self, display, font, cursor_img_file: str, loop_focus=True) -> None:
        """初始化
        Args:
            Display: 继承自FrameBuffer的显示器类,详细请看文档
                需要实现的属性:
                Width               像素宽度
                Height              像素高度
                buffer:bytearray    帧缓冲字节数据
                UpdateFrame         将帧缓冲更新到显存的函数
            Font: 等宽字体类
                需要实现的属性：
                font_size           字体大小
                get_bitmap(Char)    获取字符Char二值化点阵图的函数,返回行优先的点阵图
            cursor_img_file: .pbm(P4) 格式的文件
            loop_focus: 向前向后切换焦点是否循环
        """
        self.font = font
        if isinstance(display, framebuf.FrameBuffer):
            self.display = display
        else:
            raise TypeError("显示对象类型错误")
        self.width = display.width  # type: ignore
        self.height = display.height  # type: ignore

        # 基本容器布局
        self._layout = XLayout(
            (0, 0), (self.width, self.height), loop_focus, top=True, GUI=self
        )
        self._layout.enter = True
        # 已进入的控件栈，按键事件会传递给顶层控件处理
        self.enter_widget_stack: list[XCtrl] = list()

        # 字体初始化
        font_size = font.font_size
        # 字体数据缓存
        self._word_cache = bytearray(ceil(font_size * font_size / 8))
        # 字体帧缓存
        self._word_frame = framebuf.FrameBuffer(
            self._word_cache, font_size, font_size, framebuf.MONO_HLSB
        )

        # 调色板缓存
        self.pa_cache = framebuf.FrameBuffer(bytearray(4), 2, 1, framebuf.RGB565)

        # # 光标指针初始化
        # with open(CursorImgFile, "rb") as CursorImg:
        #     Head = CursorImg.readline()
        #     if Head == b"P4\x0A":
        #         self.CursorW = Width = int(CursorImg.readline().decode("ASCII"))
        #         self.CursorH = Height = int(CursorImg.readline().decode("ASCII"))
        #         Len = ceil(Width / 8) * Height
        #         CursorImgRaw = bytearray(CursorImg.read(Len))
        #         self.CursorFrame = framebuf.FrameBuffer(
        #             CursorImgRaw, Width, Height, framebuf.MONO_HLSB
        #         )
        #         # 指针颜色
        #         self.CursorC = WHITE
        #         # 指针当前位置
        #         self.CursorPosX = 0
        #         self.CursorPosY = 0
        gc.collect()
