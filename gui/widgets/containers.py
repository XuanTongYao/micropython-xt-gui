from gui.utils.core import WHITE
from .base import *


class XListView(XFrameLayout):
    """列表视图"""

    def __init__(self, pos, wh, color=WHITE) -> None:
        """
        Args:
            color: 边框颜色.
        """
        super().__init__(pos, wh, False, True, color)
        # 起始绘制的y轴位置(第一个子项的y轴偏移、滚动条偏移)
        self._start_offset = 0

    def _adjust_layout(self) -> None:
        offset = 0
        start = self._start_offset
        for child in self._childen:
            w = self._wh[0]
            h = child._wh[1]
            child.set_transfer((0, start + offset), (w - 4, h))
            offset += h

    def _key_response(self, key: int):
        ret_val = super()._key_response(key)
        if key in [KEY_UP, KEY_DOWN] and self._focus_list:
            focus = self._focus_list[self._focus_index]
            y = focus._pos[1]
            h = focus._wh[1]
            # 焦点超出滚动区域，调整起始绘制偏移到合适的位置
            if y < 0:
                self._start_offset -= y
                self._adjust_layout()
            elif y + h > self._layout_wh[1]:
                self._start_offset -= y + h - self._layout_wh[1]
                self._adjust_layout()
        return ret_val


class XVerticalBox(XFrameLayout):
    """垂直盒子视图。控件垂直布局"""

    def __init__(self, pos, wh, color=WHITE, average=True) -> None:
        """
        Args:
            color: 边框颜色.
            average: 是否平均分配控件位置。
        """
        super().__init__(pos, wh, False, True, color)
        self._average = average

    def _adjust_layout(self) -> None:
        spacing = 0
        if self._average:
            # 获取子控件高度和
            total_height = sum([child._wh[1] for child in self._childen])
            # 计算控件间距
            spacing = max(0, (self._wh[1] - total_height)) // (len(self._childen) + 1)

        offset = spacing
        for child in self._childen:
            child.set_transfer((0, offset), (self._wh[0] - 4, child._wh[1]))
            offset += child._wh[1] + spacing


class XHorizontalBox(XFrameLayout):
    """水平盒子视图。控件水平布局
    水平方向填充
    """

    def __init__(self, pos, wh, color=WHITE, average=True) -> None:
        """
        Args:
            color: 边框颜色.
            average: 是否平均分配控件位置.
        """
        super().__init__(pos, wh, False, True, color)
        self._average = average

    def _adjust_layout(self) -> None:
        offset = 0
        if self._average:
            avg_width = self._wh[0] // len(self._childen)
            for child in self._childen:
                child.set_transfer((0, offset), (avg_width, self._wh[1] - 4))
                offset += avg_width
        else:
            for child in self._childen:
                child.set_transfer((0, offset), (child._wh[0], self._wh[1] - 4))
                offset += child._wh[0]


class XGridBox(XFrameLayout):
    """网格盒子视图。控件网格布局"""

    # 很显然添加控件需要输入行列参数
    # 但是为了保持add_widget的基本行为，我规定了不能重写
    # 正在像一种更好的解决方法

    def __init__(self, pos, wh, color=WHITE, average=True) -> None:
        """
        Args:
            color: 边框颜色.
            average: 是否平均分配控件位置.
        """
        super().__init__(pos, wh, False, True, color)
        self._average = average

    def _adjust_layout(self) -> None:
        offset = 0
        if self._average:
            avg_width = self._wh[0] // len(self._childen)
            for child in self._childen:
                child.set_transfer((0, offset), (avg_width, self._wh[1] - 4))
                offset += avg_width
        else:
            for child in self._childen:
                child.set_transfer((0, offset), (child._wh[0], self._wh[1] - 4))
                offset += child._wh[0]
