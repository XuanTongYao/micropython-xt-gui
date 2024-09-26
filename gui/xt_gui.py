from math import ceil, floor
import utime
import framebuf
import gc
import asyncio
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

    # @timed_function
    # 240x240 屏幕 RP2040超频后单次运行耗时(典型值) 60 ms
    def draw_text(self, xtext: XText, overlap=True):
        if xtext._layout is None:
            return
        display = xtext._layout
        autowarp = xtext._autowrap
        x, y = xtext._pos
        w, h = xtext._wh

        initial_x = x
        font = self.font
        font_size = xtext._font_size
        if font_size != font.font_size:
            return
        half_size = font_size >> 1
        # 每行最后一个字最大x坐标
        last_char_x = w - font_size

        palette = self.pa_cache
        palette.pixel(1, 0, xtext._color)

        word_frame = self._word_frame
        half_word_frame = self._half_word_frame
        word_buf = self._word_buf
        # 计算要绘制的起始行和结束行
        # 起始行在上页显示一半时有bug，下页不会全部显示
        # 改成floor还是有bug，积累误差
        # 现在好像没有bug了
        begin_line = floor((-y) / font_size) if y < 0 else 0
        end_line = min(ceil((h - y) / font_size), len(xtext._lines_index) - 1)
        if begin_line >= len(xtext._lines_index):
            return
        begin_index = xtext._lines_index[begin_line]
        end_index = xtext._lines_index[end_line]
        # 开始绘制
        if y < 0:
            y = -((-y) % font_size)

        # y = max(y, 0)
        for char in xtext._context[begin_index:end_index]:
            # 对特殊字符的处理优化
            if char == "\n":
                y += font_size
                x = initial_x
                continue
            elif ord(char) < 0x20:
                continue

            # 自动换行
            if autowarp and x > last_char_x:
                y += font_size
                x = initial_x

            if overlap and char == " ":
                x += half_size
                continue

            # 超出显示范围跳过
            if x >= w:
                continue

            tmp = half_word_frame if ord(char) <= 0x7F else word_frame
            font.fast_get_bitmap(char, word_buf)
            if overlap:
                display.blit(tmp, x, y, 0, palette)
            else:
                display.blit(tmp, x, y, -1, palette)
            # X坐标偏移一个字
            # 半角字符只绘制一半的像素量，速度会更快
            x += half_size if ord(char) <= 0x7F else font_size

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
        self._top_layer_layout.add_widget(widget)

    # @timed_function
    def refrash_frame(self):
        """刷新帧，将帧数据写入显存"""
        self.display.update_frame()  # type: ignore

    async def print_debug_info(self):
        while True:
            await asyncio.sleep(2)
            print("Remaining memory:", gc.mem_free())
            print("Current layer:", len(self.layer_stack))
            if self.enter_widget_stack:
                print("Current enter widget:", self.enter_widget_stack[-1])

    @timed_function
    def show_gui(self):
        """绘制并显示整个GUI"""
        self._top_layer_layout.draw_deliver()
        self.refrash_frame()

    async def __show_gui_loop(self):
        if DEBUG:
            asyncio.create_task(self.print_debug_info())
        while True:
            self._top_layer_layout.draw_deliver()
            self.refrash_frame()
            await asyncio.sleep(0)
            gc.collect()

    def run(self, *key_handlers):
        """进入异步主循环，并启动key_handler的按键扫描循环"""
        for key_handler in key_handlers:
            if not callable(key_handler):
                raise TypeError("key_handler must be callable to run async scan_loop")
            key_handler()
        asyncio.run(self.__show_gui_loop())

    def key_response(self, key: int):
        """处理按键响应的函数，将key参数传递到当前进入的XCtrl的_key_input函数中"""
        if self.enter_widget_stack:
            func = self.enter_widget_stack[-1]._key_input
            ret_val = None if func is None else func(key)
        else:
            func = self._bottom_layer_layout._key_input
            ret_val = None if func is None else func(key)
        if ret_val == ESC and self.enter_widget_stack:
            self.esc_widget()
        elif isinstance(ret_val, XCtrl):
            self.enter_widget(ret_val)

    def enter_widget(self, widget: XCtrl):
        self.enter_widget_stack.append(widget)

    def esc_widget(self):
        xctrl = self.enter_widget_stack.pop()
        if xctrl == self._top_layer_layout and self.layer_stack:
            self.remove_layer()

    def add_layer(
        self,
        *,
        specified_layout: XLayout | None = None,
        default_widgets: list[XWidget] | None = None,
    ):
        if specified_layout is not None and not hasattr(
            specified_layout, "unable_to_enter"
        ):
            self._top_layer_layout = specified_layout
            specified_layout._layout = GuiSingle.GUI_SINGLE.display  # type: ignore
            specified_layout._create_draw_area(True)
            specified_layout._update()
        elif not hasattr(specified_layout, "unable_to_enter"):
            self._top_layer_layout = XFrameLayout(
                (0, 0), (self.width, self.height), self.loop_focus, top=True
            )

        self._top_layer_layout.enter = True
        self.layer_stack.append(self._top_layer_layout)
        self.enter_widget(self._top_layer_layout)
        if default_widgets is not None:
            for widget in default_widgets:
                self._top_layer_layout.add_widget(widget)
        self.draw_background()

    def remove_layer(self):
        self.layer_stack.pop()
        if self.layer_stack:
            self._top_layer_layout = self.layer_stack[-1]
        else:
            self._top_layer_layout = self._bottom_layer_layout
        self.draw_background()

    def __init__(
        self, display: DisplayAPI, font, cursor_img_file: str, loop_focus=True
    ) -> None:
        """初始化
        Args:
            Font: 等宽字体类
                需要实现的属性：
                font_size           字体大小
                get_bitmap(Char)    获取字符Char二值化点阵图的函数,返回行优先的点阵图
            cursor_img_file: .pbm(P4) 格式的文件
            loop_focus: 向前向后切换焦点是否循环
        """
        self.font = font
        self.display = display
        self.width = display.width
        self.height = display.height
        self.loop_focus = loop_focus

        # 基础渲染层容器布局
        self._bottom_layer_layout = XFrameLayout(
            (0, 0), (self.width, self.height), loop_focus, top=True
        )
        self._bottom_layer_layout.enter = True
        self._top_layer_layout = self._bottom_layer_layout
        # 已进入的控件栈，按键事件会传递给顶层控件处理
        self.enter_widget_stack: list[XCtrl] = list()
        # 绘制层栈，只绘制顶层布局的控件。用于进入页面覆盖显示。
        self.layer_stack: list[XLayout] = list()

        # 字体初始化
        font_size = font.font_size
        # 字体数据缓存
        self._word_buf = bytearray(ceil(font_size * font_size / 8))
        # 字体帧缓存
        self._word_frame = framebuf.FrameBuffer(
            self._word_buf, font_size, font_size, framebuf.MONO_HLSB
        )
        self._half_word_frame = framebuf.FrameBuffer(
            self._word_buf, font_size >> 1, font_size, framebuf.MONO_HLSB, font_size
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

    def __new__(cls, *args, **kwargs) -> "XT_GUI":
        if GuiSingle.GUI_SINGLE is None:
            gui = super().__new__(cls)
            GuiSingle.set_instance(gui)
            return gui
        else:
            return GuiSingle.GUI_SINGLE


gc.collect()
