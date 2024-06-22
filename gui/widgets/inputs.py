from .base import *


class XSlider(XCtrl):
    """滑动条"""

    VERTICAL = const(0)
    HORIZONTAL = const(1)

    def __init__(
        self,
        pos,
        wh,
        min_val: int,
        max_val: int,
        color=RED,
        show_text=False,
        orientation=HORIZONTAL,
    ) -> None:
        """
        Args:
            color: 文字和拨杆颜色
            show_text: 是否在右侧显示数值
            orientation: 方向
        """
        super().__init__(pos, wh, color, self._ctrl)
        self.range = (min_val, max_val)
        self.value = min_val
        self.show_text = show_text
        self.orientation = orientation

    def draw(self) -> None:
        # 条的高度/宽度是一半
        # 拨杆全高度/宽度，上下/左右伸出1/4
        if self._parent is None:
            return
        layout = self._parent._layout_frame

        x, y = self._pos
        w, h = self._wh
        value = self.value
        min_val, max_val = self.range

        layout.rect(x, y, w, h, BLACK, True)
        frame_color = FOCUSED_COLOR if self.focused else WHITE
        if self.orientation == XSlider.HORIZONTAL:
            offset = int(((value - min_val) / (max_val - min_val)) * (w - 2))
            # 绘制条和焦点轮廓
            frame_y = y + (h >> 2)
            frame_h = h >> 1
            layout.rect(x, frame_y, w, frame_h, frame_color)
            layout.rect(x + 1, frame_y + 1, w - 2, frame_h - 2, frame_color)

            # 进入样式
            if self.enter:
                layout.rect(x + offset, y, 2, h, self._color)
            else:
                layout.rect(x + offset, y, 2, h, WHITE)
        else:
            offset = int(((value - min_val) / (max_val - min_val)) * (h - 2))
            # 绘制条和焦点轮廓
            frame_x = x + (w >> 2)
            frame_w = w >> 1
            layout.rect(frame_x, y, frame_w, h, frame_color)
            layout.rect(frame_x + 1, y + 1, frame_w - 2, h - 2, frame_color)

            # 进入样式
            if self.enter:
                layout.rect(x, y + h - 2 - offset, w, 2, self._color)
            else:
                layout.rect(x, y + h - 2 - offset, w, 2, WHITE)

        if self.show_text:
            self._parent.draw_text_proxy(
                str(self.value), (x + w + 1, y), self._color, layout, False
            )

    def _ctrl(self, KEY_ID):
        if KEY_ID == KEY_MOUSE0:
            self.enter = not self.enter
            if self.enter:
                return ENTER
            else:
                return ESC
        elif KEY_ID == KEY_RIGHT or KEY_ID == KEY_DOWN:
            if self.value != self.range[0]:
                self.value -= 1
        elif KEY_ID == KEY_LEFT or KEY_ID == KEY_UP:
            if self.value != self.range[1]:
                self.value += 1

    def set_value(self, val) -> None:
        min_val, max_val = self.range
        if min_val <= val <= max_val:
            self.value = val

    def get_percent(self) -> float:
        min_val, max_val = self.range
        return (self.value - min_val) / (max_val - min_val)
