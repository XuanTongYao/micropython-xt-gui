from .base import *


class XButton(XCtrl):
    def __init__(self, pos, wh, key_press=None, text="", color=WHITE) -> None:
        """按钮控件初始化

        Args:
            key_press: 按下回调函数.
        """
        super().__init__(pos, wh, color, self._press)
        self.text = text
        self.key_press = key_press
        self._text_frame = None

    def pre_draw(self, parent: "XLayout") -> None:
        if parent._GUI is None:
            return
        self._parent = parent
        self._layout = parent._layout_frame
        absolute_x, absolute_y = self.get_absolute_pos()
        w, h = self._wh

        display = parent._GUI.display
        display_w = display.width
        text_buffer = memoryview(display.buffer)
        byte_offset = (display_w * 2 * (absolute_y + 3)) + ((absolute_x + 3) * 2)
        self._text_frame = FrameBuffer(
            text_buffer[byte_offset:], w - 6, h - 6, RGB565, display_w
        )

    def draw(self) -> None:
        if self._parent is None or self._layout is None:
            return
        layout = self._layout
        x, y = self._pos
        w, h = self._wh

        self._parent.draw_text_proxy(
            self.text, color=self._color, layout_frame=self._text_frame
        )
        border_color = FOCUSED_COLOR if self.focused else WHITE
        # 边框与焦点轮廓
        layout.rect(x, y, w, h, border_color)
        layout.rect(x + 1, y + 1, w - 2, h - 2, border_color)

    def _press(self) -> None:
        if self.key_press is None:
            return
        self.key_press()


class XRadio(XCtrl):
    """单选框"""

    def __init__(self, pos, wh, size, text="", color=RED) -> None:
        """
        Args:
            size: 直径
            color: 选中时颜色
        """
        if wh[0] - size - 1 <= 0 or wh[1] < size:
            raise ValueError("size too large")

        super().__init__(pos, wh, color, self._check)
        self.text = text
        self.checked = False
        self._size = size
        self._text_frame = None
        self._group = None

    def set_group(self, group: "list[XRadio]") -> None:
        self._group = group
        group.append(self)

    def pre_draw(self, parent: "XLayout") -> None:
        if parent._GUI is None:
            return
        self._parent = parent
        self._layout = parent._layout_frame
        absolute_x, absolute_y = self.get_absolute_pos()
        w, h = self._wh

        display = parent._GUI.display
        display_w = display.width
        text_buffer = memoryview(display.buffer)
        byte_offset = (display_w * 2 * absolute_y) + ((absolute_x + self._size + 1) * 2)
        self._text_frame = FrameBuffer(
            text_buffer[byte_offset:], w - self._size - 1, h, RGB565, display_w
        )

    def draw(self) -> None:
        if self._parent is None or self._layout is None:
            return
        layout = self._layout
        size = self._size
        x, y = self._pos
        r = size >> 1
        x += r - 1
        y += r - 1
        self._parent.draw_text_proxy(
            self.text, color=self._color, layout_frame=self._text_frame
        )
        # 绘制内边框
        layout.ellipse(x, y, r - 2, r - 2, WHITE, False)
        # 绘制焦点轮廓
        border_color = FOCUSED_COLOR if self.focused else BLACK
        layout.ellipse(x, y, r, r, border_color, False)
        layout.ellipse(x, y, r - 1, r - 1, border_color, False)

        # 选中样式
        if self.checked:
            layout.ellipse(x, y, r >> 1, r >> 1, self._color, True)
        else:
            layout.ellipse(x, y, r >> 1, r >> 1, BLACK, True)

    def _check(self, KEY_ID):
        if KEY_ID == KEY_MOUSE0:
            if self._group is None:
                self.checked = not self.checked
            elif not self.checked:
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

    def draw(self) -> None:
        if self._parent is None or self._layout is None:
            return
        layout = self._layout

        x, y = self._pos
        size = self._size

        self._parent.draw_text_proxy(
            self.text, color=self._color, layout_frame=self._text_frame
        )
        # 绘制焦点轮廓
        if self.focused:
            layout.rect(x, y, size, size, FOCUSED_COLOR)
        else:
            layout.rect(x, y, size, size, WHITE)

        x += 1
        y += 1
        color = self._color if self.checked else BLACK
        layout.line(x, y, x + size - 3, y + size - 3, color)
        layout.line(x, y + size - 3, x + size - 3, y, color)

    def _check(self, KEY_ID):
        if KEY_ID == KEY_MOUSE0:
            self.checked = not self.checked
