from ..utils import *
from framebuf import FrameBuffer


FOCUSED_COLOR = RED


class XWidget:
    """控件的基类

    变换/父控件更新 -> 触发更新(重新计算一些信息)

    """

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
        """获取绝对位置(不可重写)"""
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

    def _update(self) -> None:
        if self._parent is not None:
            self._layout = self._parent._draw_area


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
    """拥有基础布局的容器基类，无焦点控制。

    更新 -> 重新创建容器绘制区域

    添加子控件 -> 添加控件到列表 -> 对所有子控件进行调整布局

    """

    def __init__(self, pos, wh, color=WHITE, key_input=None) -> None:
        super().__init__(pos, wh, color, key_input)
        # 焦点控件
        self._childen: list[XWidget] = []
        self._draw_area = None
        self._layout_wh = (0, 0)
        self._layout_pos = (0, 0)

    def _update(self) -> None:
        super()._update()
        self._create_draw_area()
        for child in self._childen:
            child._update()

    def _calc_draw_area(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """计算绘制区域

        Returns:
            (x相对偏移,y相对偏移), (宽,高)
        """
        return (0, 0), self._wh

    def _create_draw_area(self, ignore=False):
        """创建容器绘制区域(不可重写)"""
        if GuiSingle.GUI_SINGLE is None:
            return
        if self._parent is None and not ignore:
            return

        # 重写_calc_draw_area()函数即可
        (x_offset, y_offset), (w, h) = self._calc_draw_area()

        # 限位
        if not ignore:
            x_max, y_max = self._parent._layout_wh  # type: ignore
            if x_offset < 0 or y_offset < 0 or x_offset >= x_max or y_offset >= y_max:
                raise ValueError("x_offset or y_offset out of range ")
            w = min(w, x_max - x_offset)
            h = min(h, y_max - y_offset)

        # 容器相对坐标
        self._layout_pos = (x_offset, y_offset)
        # 容器宽高
        self._layout_wh = (w, h)
        display = GuiSingle.GUI_SINGLE.display
        if isinstance(display, DisplayAPI):
            x, y = self.get_absolute_pos()
            self._draw_area = display.framebuf_slice(x + x_offset, y + y_offset, w, h)
        else:
            raise TypeError("display must be DisplayAPI")

    def draw(self) -> None:
        pass

    def draw_deliver(self) -> None:
        """传递绘制(不可重写)"""
        self.draw()
        x_max, y_max = self._layout_wh
        for child in self._childen:
            # 超出容器不绘制
            x, y = child._pos
            if x < 0 or y < 0 or x >= x_max or y >= y_max:
                continue

            if isinstance(child, XLayout):
                child.draw_deliver()
            else:
                child.draw()

    def add_widget(self, widget: XWidget) -> None:
        """添加子控件并调整布局(不可重写)"""
        self._add_widget(widget)
        self._adjust_layout()
        # 手动触发更新
        if self._layout is None:
            return
        for child in self._childen:
            child._update()

    def _adjust_layout(self) -> None:
        """调整布局"""
        pass

    def _add_widget(self, widget: XWidget) -> None:
        """添加控件"""
        self._childen.append(widget)
        widget._parent = self


class XFrameLayout(XLayout):
    """拥有基础布局的容器基类"""

    def __init__(
        self,
        pos,
        wh,
        loop_focus=True,
        frame=False,
        color=WHITE,
        top=False,
    ) -> None:
        """
        Args:
            loop_focus: 是否循环切换焦点.
            frame: 是否绘制边框.
            color: 边框颜色.
            top: 设置为顶层
        """
        super().__init__(pos, wh, color, self._key_response)
        # 焦点控件
        self._focus_list: list[XCtrl] = []
        self._focus_index = -1
        self._loop_focus = loop_focus
        self._frame = frame
        self._top = top

        if top and GuiSingle.GUI_SINGLE:
            # 顶层布局特殊化
            self._layout = GuiSingle.GUI_SINGLE.display
            self._create_draw_area(True)

    def _calc_draw_area(self) -> tuple[tuple[int, int], tuple[int, int]]:
        w, h = self._wh
        if self._frame:
            return (2, 2), (w - 4, h - 4)
        else:
            return (0, 0), (w, h)

    def draw(self) -> None:
        if self._layout is None:
            return
        if self._frame:
            x, y = self._pos
            w, h = self._wh
            # 边框和焦点轮廓
            layout = self._layout
            border_color = FOCUSED_COLOR if self.focused else self._color
            layout.rect(x, y, w, h, border_color)
            layout.rect(x + 1, y + 1, w - 2, h - 2, border_color)

    def _add_widget(self, widget: XWidget) -> None:
        """添加控件"""
        super()._add_widget(widget)
        # 调节焦点
        if isinstance(widget, XCtrl):
            self._focus_list.append(widget)
            if self._focus_index == -1:
                self._focus_index = 0
                if self.enter:
                    self._focus_list[self._focus_index].focused = True

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
        if self._layout is not None and GuiSingle.GUI_SINGLE is not None:
            GuiSingle.GUI_SINGLE.draw_text(self)
