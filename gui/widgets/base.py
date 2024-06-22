from ..utils import *
from framebuf import FrameBuffer
from framebuf import RGB565

FOCUSED_COLOR = RED


class XWidget:
    """控件的基类"""

    def __init__(self, pos: tuple[int, int], wh: tuple[int, int], color=BLACK) -> None:
        """初始化控件

        Args:
            pos: (x,y)坐标
            wh: (w,h)宽高大小
            color: 颜色. 默认为黑色.
        """
        self._pos = pos
        self._wh = wh
        self._color = color
        self._parent: XLayout | None = None

    def get_absolute_pos(self):
        if self._parent is None:
            return self._pos
        x, y = self._pos
        p_x, p_y = self._parent.get_absolute_pos()
        return (x + p_x, y + p_y)

    def draw(self) -> None:
        """绘制"""
        if self._parent is None:
            return
        x, y = self._pos
        w, h = self._wh
        layout = self._parent._layout_frame
        layout.rect(x, y, w, h, self._color, True)


class XCtrl(XWidget):
    """允许响应按键输入的控件基类"""

    def __init__(self, pos, wh, color=WHITE, key_input=NullFunc) -> None:
        """

        Args:
            KeyInput: 处理按键输入的函数,固定传入一个参数. 默认为什么都不做.
        """
        super().__init__(pos, wh, color)
        # 光标或焦点是否到达此控件
        self.focused = False
        # 是否进入到控件
        self.enter = False
        self._key_input = key_input


class XLayout(XCtrl):
    """拥有基础布局的容器基类"""

    def __init__(
        self,
        pos,
        wh,
        loop_focus=True,
        frame=False,
        color=WHITE,
        top=False,
        GUI=None,
    ) -> None:
        """
        Args:
            loop_focus: 是否循环切换焦点.
            frame: 是否绘制边框.
            color: 边框颜色.
        """
        super().__init__(pos, wh, color, self._key_response)
        # 焦点控件
        self._childen: list[XWidget] = []
        self._focus_list: list[XCtrl] = []
        self._focus_index = -1
        self._loop_focus = loop_focus
        self._frame = frame
        self._top = top
        self._GUI = GUI
        if top:
            self.create_draw_area()

    def create_draw_area(self):
        """计算边框内绘制区域"""
        if self._GUI is None:
            return
        x, y = self.get_absolute_pos()
        w, h = self._wh
        if self._frame:
            w -= 4
            h -= 4
            x += 2
            y += 2
        display = self._GUI.display
        display_w = display.width
        layout_buffer = memoryview(display.buffer)
        byte_offset = (display_w * 2 * y) + (x * 2)
        self._layout_frame = FrameBuffer(
            layout_buffer[byte_offset:], w, h, RGB565, display_w
        )

    def draw(self) -> None:
        if self._frame:
            x, y = self._pos
            w, h = self._wh
            GUI = self._GUI

            if self._top and GUI and isinstance(GUI.display, FrameBuffer):
                # 边框和焦点轮廓
                frame_color = FOCUSED_COLOR if self.focused else self._color
                GUI.display.rect(x, y, w, h, frame_color)
                GUI.display.rect(x + 1, y + 1, w - 2, h - 2, frame_color)
            else:
                # 边框和焦点轮廓
                if self._parent is None:
                    return
                layout = self._parent._layout_frame
                frame_color = FOCUSED_COLOR if self.focused else self._color
                layout.rect(x, y, w, h, frame_color)
                layout.rect(x + 1, y + 1, w - 2, h - 2, frame_color)

    def draw_deliver(self) -> None:
        """传递绘制"""
        self.draw()
        x_max, y_max = self._wh[0] - 1, self._wh[1] - 1
        for child in self._childen:
            ox, oy = child._pos
            if ox < 0 or ox >= x_max or oy < 0 or oy >= y_max:
                continue
            if isinstance(child, XLayout):
                child.draw_deliver()
            else:
                child.draw()

    def draw_text_proxy(
        self,
        text: "str|XText",
        pos=(0, 0),
        color=0xFFFF,
        layout_frame: FrameBuffer | None = None,
        overlap=True,
        t_font=None,
    ):
        if self._GUI is None:
            return
        if isinstance(text, XText):
            pos = text._pos
            color = text._color
            if text._parent is not None:
                layout_frame = text._parent._layout_frame
            text = text._context
        self._GUI.draw_text(text, pos, color, layout_frame, overlap, t_font)

    def add_widget(self, widget: XWidget) -> None:
        """添加子控件并计算绝对位置和布局"""
        self._layout(widget)
        self._add_widget(widget)

    def _layout(self, widget: XWidget) -> None:
        """计算布局"""
        pass

    def _add_widget(self, widget: XWidget) -> None:
        """添加控件"""
        self._childen.append(widget)
        widget._parent = self
        if isinstance(widget, XCtrl):
            self._focus_list.append(widget)
            if self._focus_index == -1:
                self._focus_index = 0
                if self.enter:
                    self._focus_list[self._focus_index].focused = True
            if isinstance(widget, XLayout):
                widget._GUI = self._GUI
                widget.create_draw_area()

    def _key_response(self, KEY_ID: int):
        """处理按键响应"""
        if self.enter:
            if KEY_ID == KEY_MOUSE0 and self._focus_list:
                focus = self._focus_list[self._focus_index]
                if focus._key_input(KEY_MOUSE0) == ENTER:
                    return focus
            elif KEY_ID == KEY_UP or KEY_ID == KEY_DOWN:
                # 焦点切换
                old_index = self._focus_index
                len_ = len(self._focus_list)
                # 判断循环焦点模式
                modulo = len_ if self._loop_focus else 999999
                if KEY_ID == KEY_UP:
                    self._focus_index = (self._focus_index - 1 + modulo) % modulo
                else:
                    self._focus_index = (self._focus_index + 1) % modulo

                if 0 <= self._focus_index < len_:
                    self._focus_list[old_index].focused = False
                    self._focus_list[self._focus_index].focused = True
                else:
                    self._focus_index = old_index
            elif KEY_ID == KEY_ESCAPE:
                self._focus_list[self._focus_index].focused = False
                self.enter = False
                self.focused = True
                return ESC
        elif KEY_ID == KEY_MOUSE0:
            self.enter = True
            self.focused = False
            if 0 <= self._focus_index < len(self._focus_list):
                self._focus_list[self._focus_index].focused = True
            return ENTER


class XText(XWidget):

    def __init__(self, pos, context: str, color=WHITE) -> None:
        super().__init__(pos, (0, 0), color)
        self._context = context

    def draw(self) -> None:
        if self._parent is None:
            return
        self._parent.draw_text_proxy(self)
