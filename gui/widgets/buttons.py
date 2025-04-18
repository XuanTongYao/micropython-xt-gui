from .base import *


class XButton(XLayout):

    unable_to_enter = True  # 控件不可进入

    def __init__(
        self, pos, wh=None, callback=None, text="", color=WHITE, text_size=16
    ) -> None:
        """按钮控件初始化

        Args:
            wh: 宽高，如果为None则根据text与text_size自动调整
            callback: 按下回调函数.
        """
        if wh is None:
            wh = (
                text_size * len(text) + 6,
                text_size + 6,
            )
        super().__init__(pos, wh, color, self._press)
        self.xtext = XText((0, 0), text, self._color)  # 显示的文字控件
        self.callback = callback
        self.add_widget(self.xtext)

    def _calc_draw_area(self) -> tuple[tuple[int, int], tuple[int, int]]:
        w, h = self._wh
        return (3, 3), (w - 6, h - 6)

    def _draw(self) -> None:
        layout = self._parent._draw_area
        x, y = self._pos
        w, h = self._wh

        border_color = FOCUSED_COLOR if self._focused else WHITE
        # 边框与焦点轮廓
        layout.rect(x, y, w, h, border_color)
        layout.rect(x + 1, y + 1, w - 2, h - 2, border_color)

    def _press(self, _) -> None:
        if self.callback is None:
            return
        self.callback()


class XRadio(XLayout):
    """单选框"""

    unable_to_enter = True  # 控件不可进入

    def __init__(self, pos, wh, size, text="", color=RED) -> None:
        """
        Args:
            size: 直径
            color: 选中时颜色
        """
        if wh[0] - size - 1 <= 0 or wh[1] < size:
            raise ValueError("size too large")

        super().__init__(pos, wh, color, self._check)
        self.xtext = XText((0, 0), text, self._color)
        self._checked = False  # 被选中
        self._size = size
        self._group = None  # 组别(目前无用)
        self.add_widget(self.xtext)

    @property
    def checked(self):
        return self._checked

    @checked.setter
    def checked(self, val):
        if self._checked != val:
            self._checked = val
            self._redraw_flag = True

    @property
    def group(self):
        return self._group

    @group.setter
    def group(self, group: "list[XRadio]"):
        self._group = group
        group.append(self)

    def _calc_draw_area(self) -> tuple[tuple[int, int], tuple[int, int]]:
        w, h = self._wh
        return (self._size + 1, 0), (w - self._size - 1, h)

    def _draw(self) -> None:
        layout = self._parent._draw_area
        size = self._size
        x, y = self._pos
        r = size >> 1
        x += r - 1
        y += r - 1

        # 绘制内边框
        layout.ellipse(x, y, r - 2, r - 2, WHITE, False)
        # 绘制焦点轮廓
        border_color = FOCUSED_COLOR if self._focused else BLACK
        layout.ellipse(x, y, r, r, border_color, False)
        layout.ellipse(x, y, r - 1, r - 1, border_color, False)

        # 选中样式
        if self._checked:
            layout.ellipse(x, y, r >> 1, r >> 1, self._color, True)
        else:
            layout.ellipse(x, y, r >> 1, r >> 1, BLACK, True)

    def _check(self, KEY_ID):
        if KEY_ID == KEY_MOUSE0:
            if self._group is None:
                self.checked = not self._checked
                self._redraw_flag = True
            elif not self._checked:
                for radio in self._group:
                    radio.checked = False
                self.checked = True


class XCheckbox(XRadio):
    """复选框"""

    def __init__(self, pos, wh, size, text="", color=RED) -> None:
        """
        Args:
            size: 勾选框边长
            color: 选中时颜色
        """
        super().__init__(pos, wh, size, text, color)

    def _draw(self) -> None:
        layout = self._parent._draw_area

        x, y = self._pos
        size = self._size

        # 绘制焦点轮廓
        if self._focused:
            layout.rect(x, y, size, size, FOCUSED_COLOR)
        else:
            layout.rect(x, y, size, size, WHITE)

        x += 1
        y += 1
        color = self._color if self._checked else BLACK
        layout.line(x, y, x + size - 3, y + size - 3, color)
        layout.line(x, y + size - 3, x + size - 3, y, color)

    def _check(self, KEY_ID):
        if KEY_ID == KEY_MOUSE0:
            self.checked = not self._checked
