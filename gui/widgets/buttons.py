from gui.widgets.base import *


class XButton(XCtrl):
    def __init__(self, pos, wh, key_input=NullFunc, context="", color=WHITE) -> None:
        """按钮控件初始化

        Args:
            KeyInput: 按下回调函数.
        """
        super().__init__(pos, wh, color, key_input)
        self.context = context

    def draw(self) -> None:
        if self._parent is None:
            return
        layout = self._parent._layout_frame
        x, y = self._pos
        w, h = self._wh
        self._parent.draw_text_proxy(self.context, (x + 3, y + 3), self._color, layout)
        frame_color = FOCUSED_COLOR if self.focused else WHITE
        # 边框与焦点轮廓
        layout.rect(x, y, w, h, frame_color)
        layout.rect(x + 1, y + 1, w - 2, h - 2, frame_color)


class XCheckbox(XCtrl):
    """复选框"""

    def __init__(self, pos, size, color=RED) -> None:
        """
        Args:
            color: 选中时颜色
        """
        super().__init__(pos, (size, size), color, self._check)
        self.checked = False

    def draw(self) -> None:
        if self._parent is None:
            return
        layout = self._parent._layout_frame

        x, y = self._pos
        size = self._wh[0]
        color = self._color if self.checked else BLACK

        if self.focused:
            layout.rect(x, y, size, size, FOCUSED_COLOR)
        else:
            layout.rect(x, y, size, size, WHITE)

        x += 1
        y += 1
        layout.line(x, y, x + size - 3, y + size - 3, color)
        layout.line(x, y + size - 3, x + size - 3, y, color)

    def _check(self, KEY_ID):
        if KEY_ID == KEY_MOUSE0:
            self.checked = not self.checked


class XRadio(XCtrl):
    """单选框"""

    def __init__(self, pos, size, color=RED) -> None:
        """
        Args:
            size: 直径
            color: 选中时颜色
        """
        super().__init__(pos, (size, size), color, self._check)
        self.checked = False

    def draw(self) -> None:
        if self._parent is None:
            return
        layout = self._parent._layout_frame
        size = self._wh[0]
        x, y = self._pos
        r = size // 2
        x += r - 1
        y += r - 1
        # 绘制内边框
        layout.ellipse(x, y, r - 2, r - 2, WHITE, False)
        # 绘制焦点轮廓
        frame_color = FOCUSED_COLOR if self.focused else BLACK
        layout.ellipse(x, y, r, r, frame_color, False)
        layout.ellipse(x, y, r - 1, r - 1, frame_color, False)

        # 选中样式
        if self.checked:
            layout.ellipse(x, y, r >> 1, r >> 1, self._color, True)
        else:
            layout.ellipse(x, y, r >> 1, r >> 1, BLACK, True)

    def _check(self, KEY_ID):
        if KEY_ID == KEY_MOUSE0:
            self.checked = not self.checked
