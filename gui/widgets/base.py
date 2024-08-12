from ..utils import *
from framebuf import FrameBuffer
from framebuf import RGB565

FOCUSED_COLOR = RED


class XWidget:
    """控件的基类"""

    def __init__(self, pos: tuple[int, int], wh: tuple[int, int], color=BLACK) -> None:
        """初始化控件

        Args:
            pos: (x,y)相对坐标
            wh: (w,h)宽高大小
            color: 颜色. 默认为黑色.
        """
        self._pos = pos
        self._wh = wh
        self._color = color
        self._parent: XLayout | None = None
        self._layout: FrameBuffer | None = None

    def get_absolute_pos(self) -> tuple[int, int]:
        if self._parent is None:
            return self._pos
        x, y = self._pos
        p_x, p_y = self._parent.get_absolute_pos()
        layout_x, layout_y = self._parent._layout_pos
        return (x + p_x + layout_x, y + p_y + layout_y)

    def draw(self) -> None:
        """绘制"""
        if self._layout is None:
            return
        x, y = self._pos
        w, h = self._wh
        self._layout.rect(x, y, w, h, self._color, True)


class XCtrl(XWidget):
    """允许响应按键输入的控件基类"""

    def __init__(self, pos, wh, color=WHITE, key_input=None) -> None:
        """

        Args:
            KeyInput: 处理按键输入的函数,固定传入一个参数.
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
        self._GUI = GUI
        # 如果构造时指定了GUI,则认为该布局是顶层布局
        if GUI:
            self._top = True
            self._layout = GUI.display.buffer
            self.create_draw_area()
        else:
            self._top = False

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
            self._layout_pos = (2, 2)
        else:
            self._layout_pos = (0, 0)

        self._layout_wh = (w, h)
        display = self._GUI.display
        if isinstance(display, DisplayAPI):
            self._draw_area = display.framebuf_slice(x, y, w, h)

    def update_layout(self):
        """更新子控件布局缓存"""
        for child in self._childen:
            child._layout = self._draw_area
            if isinstance(child, XLayout):
                child._GUI = self._GUI
                child.create_draw_area()
                child.update_layout()

    def draw(self) -> None:
        if self._frame:
            x, y = self._pos
            w, h = self._wh
            GUI = self._GUI

            if self._top and GUI and isinstance(GUI.display, FrameBuffer):
                # 边框和焦点轮廓
                border_color = FOCUSED_COLOR if self.focused else self._color
                GUI.display.rect(x, y, w, h, border_color)
                GUI.display.rect(x + 1, y + 1, w - 2, h - 2, border_color)
            else:
                # 边框和焦点轮廓
                if self._layout is None:
                    return
                layout = self._layout
                border_color = FOCUSED_COLOR if self.focused else self._color
                layout.rect(x, y, w, h, border_color)
                layout.rect(x + 1, y + 1, w - 2, h - 2, border_color)

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

    def draw_text_proxy(self, xtext: "XText"):
        if self._GUI is None:
            return
        self._GUI.draw_text(xtext)

    def add_widget(self, widget: XWidget) -> None:
        """添加子控件并调整布局"""
        self._adjust_layout(widget)
        self._add_widget(widget)

    def _adjust_layout(self, widget: XWidget) -> None:
        """针对子控件调整布局"""
        pass

    def _add_widget(self, widget: XWidget) -> None:
        """添加控件"""
        self._childen.append(widget)
        widget._parent = self
        if self._parent is None and not self._top:
            return
        widget._layout = self._draw_area
        if isinstance(widget, XCtrl):
            self._focus_list.append(widget)
            if self._focus_index == -1:
                self._focus_index = 0
                if self.enter:
                    self._focus_list[self._focus_index].focused = True
            if isinstance(widget, XLayout):
                widget._GUI = self._GUI
                widget.create_draw_area()
                widget.update_layout()

    def _key_response(self, key: int):
        """处理按键响应"""
        if self.enter:
            if key == KEY_MOUSE0 and self._focus_list:
                focus = self._focus_list[self._focus_index]
                func = focus._key_input
                if func is None:
                    return
                if func(KEY_MOUSE0) == ENTER:
                    return focus
            elif key == KEY_UP or key == KEY_DOWN:
                # 焦点切换
                old_index = self._focus_index
                len_ = len(self._focus_list)
                # 判断循环焦点模式
                modulo = len_ if self._loop_focus else 999999
                if key == KEY_UP:
                    self._focus_index = (self._focus_index - 1 + modulo) % modulo
                else:
                    self._focus_index = (self._focus_index + 1) % modulo

                if 0 <= self._focus_index < len_:
                    self._focus_list[old_index].focused = False
                    self._focus_list[self._focus_index].focused = True
                else:
                    self._focus_index = old_index
            elif key == KEY_ESCAPE:
                self._focus_list[self._focus_index].focused = False
                self.enter = False
                self.focused = True
                return ESC
        elif key == KEY_MOUSE0:
            self.enter = True
            self.focused = False
            if 0 <= self._focus_index < len(self._focus_list):
                self._focus_list[self._focus_index].focused = True
            return ENTER


class XText(XWidget):

    def __init__(self, pos, context: str, color=WHITE, line=1) -> None:
        super().__init__(pos, (0, 0), color)
        self._context = context
        self._line = line

    def draw(self) -> None:
        if self._parent is None:
            return
        self._parent.draw_text_proxy(self)
