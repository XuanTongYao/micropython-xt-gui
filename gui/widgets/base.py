from ..utils.core import *
from framebuf import FrameBuffer

FOCUSED_COLOR = RED
BORDER = const(2)
D_BORDER = const(2 * BORDER)


class XWidget:
    """控件的基类

    变换/父控件更新 -> 触发更新(重新计算一些信息)

    """

    def __init__(self, pos: tuple[int, int], wh: tuple[int, int], color=BLACK):
        """初始化控件

        Args:
            pos: (x,y)相对坐标
            wh: (w,h)宽高大小
            color: 颜色. 默认为黑色.
        """
        self._pos = pos
        self._wh = wh
        self._color = color
        self._parent: XLayout = None  # type: ignore # 父控件
        self._redraw_flag: bool = True  # 重绘标记

    # 公共方法
    def set_parent(self, parent: "XLayout"):
        if self._parent != parent:
            self._parent = parent
            self._redraw_flag = True

    def set_pos(self, pos: tuple[int, int]):
        """不可重写"""
        if self._pos != pos:
            self._pos = pos
            self._transfer_event_trigger()

    def set_wh(self, wh: tuple[int, int]):
        """不可重写"""
        if self._wh != wh:
            self._wh = wh
            self._transfer_event_trigger()

    def set_transfer(self, pos: tuple[int, int], wh: tuple[int, int]):
        """不可重写"""
        changed = False
        if self._pos != pos:
            self._pos = pos
            changed = True
        if self._wh != wh:
            self._wh = wh
            changed = True
        if changed:
            self._transfer_event_trigger()

    def set_color(self, color: int):
        if self._color != color:
            self._color = color
            self._redraw_flag = True

    def get_absolute_pos(self) -> tuple[int, int]:
        """获取绝对位置(不可重写)"""
        if self._parent is None:
            return self._pos
        x, y = self._pos
        p_x, p_y = self._parent.get_absolute_pos()
        layout_x, layout_y = self._parent._layout_pos
        return (x + p_x + layout_x, y + p_y + layout_y)

    # 事件触发器
    def _transfer_event_trigger(self):
        """变换事件触发器"""
        self._redraw_flag = True
        if self._parent is not None:
            self._parent._event_receiver(TRANSFER_EVENT)
        # print("触发变换事件")  # Debug

    # 事件接收器
    def _event_receiver(self, event: int):
        """事件接收器(不可重写)"""
        if event == TRANSFER_EVENT:
            self._transfer_event_handler()
        elif event == REBUILD_DRAW_AREA_EVENT:
            self._rebuild_draw_area_event_handler()
        elif event == CLEAR_DRAW_AREA_EVENT:
            self._clear_draw_area_event_handler()
        else:
            self._custom_event_receiver(event)

    def _custom_event_receiver(self, event: int):
        pass

    # 事件处理器
    def _transfer_event_handler(self):
        """变换事件处理器(必须继承并执行)"""
        # print("收到变换事件", self)  # Debug
        pass

    def _rebuild_draw_area_event_handler(self):
        """重建绘制区域事件处理器(必须继承并执行)"""
        self._redraw_flag = True
        # print("收到重建事件", self)  # Debug

    def _clear_draw_area_event_handler(self):
        """擦除绘制区域事件处理器(必须继承并执行)"""
        self._redraw_flag = True
        # print("收到擦除事件", self)  # Debug

    # 绘制相关
    def _draw__(self):
        """透明化调用绘制(不可重写)"""
        self._redraw_flag = False
        self._draw()

    def _draw(self):
        """绘制"""
        x, y = self._pos
        w, h = self._wh
        self._parent._draw_area.rect(x, y, w, h, self._color, True)


class XCtrl(XWidget):
    """允许响应按键输入的控件基类"""

    def __init__(self, pos, wh, color=WHITE, key_input=None):
        """
        Args:
            key_input: 处理按键输入的函数,固定传入一个按键值参数\n
                对于当前进入的控件:\n
                    返回一个XCtrl对象，表示进入到该对象。\n
                    返回一个ESC，表示退出当前进入的控件。
                对于未进入但已经进入其容器的控件:\n
                    返回一个ENTER，指示上层容器需要进入到该控件。
        """
        super().__init__(pos, wh, color)
        # 光标或焦点是否到达此控件
        # TODO 进入之后是否应该清除焦点？XFrameLayout会自己清除。其他类是否应该由父控件清除？
        self._focused: bool = False  # 焦点是否位于该控件
        self._enter: bool = False  # 是否进入到控件
        self._key_input = key_input

    @property
    def focused(self):
        return self._focused

    @focused.setter
    def focused(self, val: bool):
        if self._focused != val:
            self._focused = val
            self._redraw_flag = True


class XLayout(XCtrl):
    """拥有基础布局的容器基类，无焦点控制。

    更新 -> 重新创建容器绘制区域

    添加子控件 -> 添加控件到列表 -> 对所有子控件进行调整布局

    """

    def __init__(self, pos, wh, color=WHITE, key_input=None):
        super().__init__(pos, wh, color, key_input)
        self._children: list[XWidget] = []  # 子控件列表
        self._cleared = True  # 已擦除标志
        self._layout_wh: tuple[int, int] = (0, 0)  # 容器宽高
        self._layout_pos = (0, 0)  # 容器相对坐标

    # 公共方法
    def set_parent(self, parent: "XLayout"):
        super().set_parent(parent)
        self._rebuild_draw_area()
        self._redraw_flag = True

    def clear(self):
        """擦除(不可重写)"""
        if self._layout_wh != (0, 0):
            self._draw_area.fill(0)
            self._cleared = True
            self._clear_draw_area_event_trigger()

    def add_widget(self, widget: XWidget):
        """添加子控件并调整布局(必须实现这个参数的版本)"""
        self._add_widget(widget)
        self._adjust_layout()

    def add_widgets(self, widgets: list[XWidget] | tuple[XWidget, ...]):
        """添加多个子控件并调整布局(必须实现这个参数的版本,避免多余调整布局的性能问题)"""
        for widget in widgets:
            self._add_widget(widget)
        self._adjust_layout()

    def remove_widget(self, widget: XWidget):
        """移除子控件并调整布局(必须实现这个参数的版本)"""
        if widget in self._children:
            self._children.pop(self._children.index(widget))
            widget.set_parent(None)  # type: ignore
            self.clear()
            self._adjust_layout()

    # 事件触发器
    def _transfer_event_trigger(self):
        super()._transfer_event_trigger()
        if self._parent is not None:
            self._rebuild_draw_area()

    def _rebuild_draw_area_event_trigger(self):
        """重建容器绘制区域事件触发器"""
        for child in self._children:
            child._event_receiver(REBUILD_DRAW_AREA_EVENT)
        self._adjust_layout()

    def _clear_draw_area_event_trigger(self):
        """擦除容器绘制区域事件触发器"""
        for child in self._children:
            child._event_receiver(CLEAR_DRAW_AREA_EVENT)

    # 事件处理器
    def _transfer_event_handler(self):
        super()._transfer_event_handler()
        if not self._cleared:
            self.clear()

    def _rebuild_draw_area_event_handler(self):
        super()._rebuild_draw_area_event_handler()
        self._rebuild_draw_area()
        for child in self._children:
            child._event_receiver(REBUILD_DRAW_AREA_EVENT)

    def _clear_draw_area_event_handler(self):
        super()._clear_draw_area_event_handler()
        for child in self._children:
            child._event_receiver(CLEAR_DRAW_AREA_EVENT)

    # 绘制相关
    def _calc_draw_area(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """计算绘制区域，也就是容器相对于自己的相对坐标和宽高

        Returns:
            (x相对偏移,y相对偏移), (宽,高)
        """
        return (0, 0), self._wh

    def _rebuild_draw_area(self):
        """创建绘制区域(不可重写)"""
        if GuiSingle.GUI_SINGLE is None:
            return

        if self._parent._layout_wh == (0, 0):
            self._layout_wh = (0, 0)
            self._rebuild_draw_area_event_trigger()
            return

        # 重写_calc_draw_area()函数即可
        (x_offset, y_offset), (w, h) = self._calc_draw_area()

        # 内部限位
        x_max, y_max = self._wh
        if x_offset < 0 or y_offset < 0 or x_offset >= x_max or y_offset >= y_max:
            self._layout_wh = (0, 0)
            self._rebuild_draw_area_event_trigger()
            return

        # 父容器限位
        x, y = self._pos
        x += x_offset
        y += y_offset
        x_max, y_max = self._parent._layout_wh
        if x >= x_max or y >= y_max or w + x < 0 or y + h < 0:
            self._layout_wh = (0, 0)
            self._rebuild_draw_area_event_trigger()
            return
        if x < 0:
            x_offset = -self._pos[0]
        if y < 0:
            y_offset = -self._pos[1]
        w = min(w + x, w, x_max - x, x_max)
        h = min(y + h, h, y_max - y, y_max)

        # 重建绘制区域
        self._layout_pos = (x_offset, y_offset)
        self._layout_wh = (w, h)
        display = GuiSingle.GUI_SINGLE.display
        if isinstance(display, DisplayAPI):
            x, y = self.get_absolute_pos()
            # 容器绘制区域(容器区域)
            self._draw_area = display.framebuf_slice(x + x_offset, y + y_offset, w, h)
            self._rebuild_draw_area_event_trigger()
        else:
            raise TypeError("display must be DisplayAPI")

    def _adjust_layout(self):
        """调整布局"""
        pass

    def _add_widget(self, widget: XWidget):
        """添加控件"""
        self._children.append(widget)
        widget.set_parent(self)

    def _draw(self):
        pass

    def _draw_deliver(self):
        """传递绘制(不可重写)"""
        if self._redraw_flag:
            self._draw__()
        # 绘制区域无效时不绘制所有子控件
        if self._layout_wh == (0, 0):
            return

        self._cleared = False
        x_max, y_max = self._layout_wh
        for child in self._children:
            # 超出容器不绘制
            x, y = child._pos
            if x >= x_max or y >= y_max:
                continue

            if isinstance(child, XLayout):
                child._draw_deliver()
            elif child._redraw_flag:
                child._draw__()


class XFrameLayout(XLayout):
    """拥有基础布局的容器基类，也是GUI的顶层容器。"""

    def __init__(
        self,
        pos,
        wh,
        loop_focus=True,
        frame=False,
        color=WHITE,
    ):
        """
        Args:
            loop_focus: 是否循环切换焦点.
            frame: 是否绘制边框.
            color: 边框颜色.
            top: 设置为顶层
        """
        super().__init__(pos, wh, color, self._key_response)
        # 焦点控件
        self._focus_list: list[XCtrl] = []  # 焦点列表
        self._focus_index = 0  # 当前焦点
        self._loop_focus = loop_focus  # 允许循环切换焦点
        self._frame = frame  # 有边框

    def _calc_draw_area(self) -> tuple[tuple[int, int], tuple[int, int]]:
        w, h = self._wh
        if self._frame:
            return (BORDER, BORDER), (w - D_BORDER, h - D_BORDER)
        else:
            return (0, 0), (w, h)

    def _draw(self):
        if self._frame:
            x, y = self._pos
            w, h = self._wh
            # 边框和焦点轮廓
            layout = self._parent._draw_area
            border_color = FOCUSED_COLOR if self.focused else self._color
            layout.rect(x, y, w, h, border_color)
            layout.rect(x + 1, y + 1, w - 2, h - 2, border_color)

    def _add_widget(self, widget: XWidget):
        """添加控件"""
        super()._add_widget(widget)
        # 调节焦点
        if isinstance(widget, XCtrl):
            self._focus_list.append(widget)
            if self._enter and len(self._focus_list) == 1:
                self._focus_list[self._focus_index].focused = True

    def _key_response(self, key: int):
        """处理按键响应

        对于当前进入的控件:
            返回一个XCtrl对象，表示进入到该对象
            返回一个ESC，表示退出当前进入的控件
        """
        if self._enter:
            if key == KEY_MOUSE0 and self._focus_list:
                focus = self._focus_list[self._focus_index]
                func = focus._key_input
                if func is None:
                    return
                if func(KEY_MOUSE0) == ENTER:
                    return focus
            elif (key == KEY_UP or key == KEY_DOWN) and self._focus_list:
                # 焦点切换
                old_index = self._focus_index
                len_ = len(self._focus_list)
                # 判断循环焦点模式
                if key == KEY_UP:
                    self._focus_index = (
                        (old_index - 1 + len_) % len_
                        if self._loop_focus
                        else max(old_index - 1, 0)
                    )
                else:
                    self._focus_index = (
                        (old_index + 1) % len_
                        if self._loop_focus
                        else min(old_index + 1, len_ - 1)
                    )

                if self._focus_index != old_index:
                    self._focus_list[old_index].focused = False
                    self._focus_list[self._focus_index].focused = True
            elif key == KEY_ESCAPE:
                self._enter = False
                self.focused = True
                if self._focus_list:
                    self._focus_list[self._focus_index].focused = False
                return ESC
        elif key == KEY_MOUSE0:
            self._enter = True
            self.focused = False
            if self._focus_list:
                self._focus_list[self._focus_index].focused = True
            return ENTER


class XText(XWidget):

    def __init__(self, pos, context: str, color=WHITE, autowrap=True, font_size=None):
        super().__init__(pos, (0, 0), color)
        self._context = context  # 内容
        self._autowrap = autowrap  # 是否自动换行
        # 字体大小（目前无用）
        self._font_size = font_size if font_size is not None else GuiSingle.GUI_SINGLE.font.font_size  # type: ignore
        self._lines_index: list[int] = []  # 文本预处理结果(每行起始位置在内容中的索引)
        # 多行滚动条位置，起始为0，向下为正，建议只在翻页容器使用
        self._scrollbar_pos = 0

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, context: str):
        self._context = context
        self._text_pre_processing()
        self._redraw_flag = True

    # 公共方法
    def set_parent(self, parent: XLayout):
        super().set_parent(parent)
        self._text_pre_processing()

    def _draw(self):
        if GuiSingle.GUI_SINGLE is not None:
            GuiSingle.GUI_SINGLE.draw_text(self)

    def _rebuild_draw_area_event_handler(self):
        super()._rebuild_draw_area_event_handler()
        self._text_pre_processing()

    def _set_scrollbar_pos(self, pos: int):
        self._scrollbar_pos = pos
        self._redraw_flag = True

    def _text_pre_processing(self):
        if self._parent:
            self._wh = self._parent._layout_wh
        x, y = self._pos
        w, h = self._wh
        if x >= w or y >= h:
            # print("超出容器，不绘制", x, y, w, h)  # Debug
            return

        # 预处理文本，计算出每行文本的起始索引和y坐标
        _lines_index = self._lines_index
        _lines_index.clear()
        _lines_index.append(0)
        initial_x = x

        font_size = self._font_size
        half_size = font_size >> 1
        autowarp = self._autowrap
        for i, char in enumerate(self._context):
            # 对特殊字符的处理优化
            if ord(char) < 0x20 and char != "\n":
                continue

            # 自动换行
            if autowarp and x + font_size > w:
                _lines_index.append(i)
                x = initial_x

            if char == "\n":
                x = w
                continue

            x += half_size if ord(char) <= 0x7F else font_size
        _lines_index.append(len(self._context))
        # print("更新，行索引", _lines_index)


gc.collect()
