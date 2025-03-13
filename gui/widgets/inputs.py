from array import array
from gui.utils.core import WHITE
from .base import *


class XSlider(XCtrl):
    """滑块滑动条"""

    def __init__(self, pos, wh, min_val: int, max_val: int, color=BLUE) -> None:
        """
        Args:
            color: 滑块和填充颜色
        """
        super().__init__(pos, wh, color, self._ctrl)
        if min_val > max_val:
            raise ValueError("min_val is greater than max_val")
        self._range = (min_val, max_val)
        self._value = min_val

    def _draw(self) -> None:
        # [===|    ]
        # 边框白色
        # 左侧填充颜色，中间实心圆形滑块，右侧不填充
        # 条的厚度是1/2，滑块在条的厚度方向超出1/8也就是半径1/8+1/4
        # 内边距: 厚度方向1/8
        layout = self._parent._draw_area
        x, y = self._pos
        w, h = self._wh
        frame_color = FOCUSED_COLOR if self.focused else WHITE
        layout.rect(x, y, w, h, BLACK, True)
        # 自动判断方向
        if w >= h:
            # 水平
            bar_thickness = h // 2
            padding_y = h // 8
            radius = bar_thickness // 2 + padding_y
            bar_length = w - radius - radius
            bar_x = x + radius
            bar_y = y + h // 4
            fill_len = int(self.percent * bar_length)
            # 先绘制填充
            if fill_len != 0:
                layout.rect(bar_x, bar_y, fill_len, bar_thickness, self._color, True)
            # 绘制边框与焦点轮廓
            layout.rect(bar_x, bar_y, bar_length, bar_thickness, frame_color)
            layout.rect(
                bar_x + 1, bar_y + 1, bar_length - 2, bar_thickness - 2, frame_color
            )
            # 绘制滑块
            slider_center = (bar_x + fill_len, y + bar_thickness)
            layout.ellipse(*slider_center, radius - 2, radius - 2, self._color, True)
            # 进入样式
            enter_color = FOCUSED_COLOR if self._enter else WHITE
            layout.ellipse(*slider_center, radius, radius, enter_color, False)
            layout.ellipse(*slider_center, radius - 1, radius - 1, enter_color, False)

        else:
            # 垂直
            bar_thickness = w // 2
            padding_x = w // 8
            radius = bar_thickness // 2 + padding_x
            bar_length = h - radius - radius
            bar_x = x + w // 4
            bar_y = y + radius
            fill_len = int(self.percent * bar_length)
            # 先绘制填充
            if fill_len != 0:
                layout.rect(
                    bar_x,
                    2 * bar_y - fill_len,
                    bar_thickness,
                    fill_len,
                    self._color,
                    True,
                )
            # 绘制边框与焦点轮廓
            layout.rect(bar_x, bar_y, bar_thickness, bar_length, frame_color)
            layout.rect(
                bar_x + 1, bar_y + 1, bar_thickness - 2, bar_length - 2, frame_color
            )
            # 绘制滑块
            slider_center = (x + bar_thickness, 2 * bar_y - fill_len)
            layout.ellipse(
                *slider_center,
                radius - 2,
                radius - 2,
                self._color,
                True,
            )
            # 进入样式
            enter_color = FOCUSED_COLOR if self._enter else WHITE
            layout.ellipse(*slider_center, radius, radius, enter_color, False)
            layout.ellipse(*slider_center, radius - 1, radius - 1, enter_color, False)

    def _ctrl(self, KEY_ID):
        if KEY_ID == KEY_MOUSE0:
            self._enter = not self._enter
            if self._enter:
                self.focused = False
                return ENTER
            else:
                self.focused = True
                return ESC
        elif KEY_ID == KEY_RIGHT or KEY_ID == KEY_DOWN:
            if self._value != self._range[0]:
                self._value -= 1
                self._redraw_flag = True
        elif KEY_ID == KEY_LEFT or KEY_ID == KEY_UP:
            if self._value != self._range[1]:
                self._value += 1
                self._redraw_flag = True

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, val) -> None:
        min_val, max_val = self._range
        if min_val <= val <= max_val:
            self._value = val
            self._redraw_flag = True

    @property
    def percent(self) -> float:
        min_val, max_val = self._range
        return (self._value - min_val) / (max_val - min_val)


class XSpinBox(XLayout):

    ARRAY_WITHD = const(12)
    HALF_ARRAY = const(ARRAY_WITHD // 2)

    def __init__(
        self,
        pos,
        wh,
        min_val: int,
        max_val: int,
        single_step: int = 1,
        prefix: str = "",
        suffix: str = "",
        color=WHITE,
    ):
        super().__init__(pos, wh, color, self._ctrl)
        if min_val > max_val:
            raise ValueError("min_val is greater than max_val")
        self._range = (min_val, max_val)
        self._value = min_val
        self._prefix = prefix
        self._suffix = suffix
        self._single_step = single_step
        self.xtext = XText((0, 0), prefix + str(min_val) + suffix, self._color)
        self.add_widget(self.xtext)

    def _ctrl(self, KEY_ID):
        if KEY_ID == KEY_MOUSE0:
            self._enter = not self._enter
            if self._enter:
                self.focused = False
                return ENTER
            else:
                self.focused = True
                return ESC
        elif KEY_ID == KEY_RIGHT or KEY_ID == KEY_DOWN:
            if self._value != self._range[0]:
                self._value -= 1
                self.xtext.set_context(self._prefix + str(self._value) + self._suffix)
                self.clear()
        elif KEY_ID == KEY_LEFT or KEY_ID == KEY_UP:
            if self._value != self._range[1]:
                self._value += 1
                self.xtext.set_context(self._prefix + str(self._value) + self._suffix)
                self.clear()

    def _calc_draw_area(self) -> tuple[tuple[int, int], tuple[int, int]]:
        w, h = self._wh
        return (BORDER, BORDER), (w - XSpinBox.ARRAY_WITHD, h - D_BORDER)

    def _draw(self):
        layout = self._parent._draw_area
        x, y = self._pos
        w, h = self._wh
        frame_color = FOCUSED_COLOR if self.focused else WHITE
        # 绘制右侧
        tip_x = x + w - XSpinBox.ARRAY_WITHD
        layout.rect(tip_x, y, XSpinBox.ARRAY_WITHD - BORDER, h, frame_color, True)
        # 挖空三角形
        half_h = h // 2
        layout.poly(
            tip_x,
            y,
            array(
                "h",
                [
                    XSpinBox.HALF_ARRAY,
                    BORDER,
                    2,
                    half_h - 1,
                    XSpinBox.ARRAY_WITHD - BORDER,
                    half_h - 1,
                ],
            ),
            BLACK,
            True,
        )
        layout.poly(
            tip_x,
            y,
            array(
                "h",
                [
                    XSpinBox.HALF_ARRAY,
                    h - BORDER,
                    2,
                    half_h + 1,
                    XSpinBox.ARRAY_WITHD - BORDER,
                    half_h + 1,
                ],
            ),
            BLACK,
            True,
        )
        # 绘制边框与焦点轮廓
        layout.rect(x, y, w, h, frame_color)
        layout.rect(x + 1, y + 1, w - 2, h - 2, frame_color)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, val: int) -> None:
        if self._value == val:
            return
        min_val, max_val = self._range
        if min_val <= val <= max_val:
            self._value = val
            self.xtext.set_context(self._prefix + str(self._value) + self._suffix)
            self.clear()

    @property
    def suffix(self) -> str:
        return self._suffix

    @suffix.setter
    def suffix(self, suffix: str):
        if self._suffix != suffix:
            self._suffix = suffix
            self.xtext.set_context(self._prefix + str(self._value) + self._suffix)
            self.clear()

    @property
    def prefix(self) -> str:
        return self._prefix

    @prefix.setter
    def set_prefix(self, prefix: str):
        if self._prefix != prefix:
            self._prefix = prefix
            self.xtext.set_context(self._prefix + str(self._value) + self._suffix)
            self.clear()

    def set_range(self, range: tuple[int, int]):
        if self._range == range:
            return
        min_val, max_val = range
        if min_val > max_val:
            return
        self._range = range
        self.value = max(min(max_val, self.value), min_val)


# TODO 这些控件都需要显示文字，怎么样显示文字更加高效。
class XComboBox(XCtrl):
    # TODO
    pass
