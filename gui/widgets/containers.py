from .base import *
from .base import XWidget


class XListView(XLayout):
    """列表视图"""

    def __init__(self, pos, wh, color=WHITE) -> None:
        """
        Args:
            color: 边框颜色.
        """
        super().__init__(pos, wh, False, True, color)
        # 最后一个子项的y轴偏移
        self.widget_offset = 0

    def _adjust_layout(self, widget: XWidget) -> None:
        w = self._wh[0]
        oh = widget._wh[1]
        widget._pos = (0, self.widget_offset)
        widget._wh = (w - 4, oh)
        self.widget_offset += oh

    def _key_response(self, KEY_ID: int):
        super()._key_response(KEY_ID)
        if KEY_ID in [KEY_UP, KEY_DOWN] and self._focus_list:
            focus = self._focus_list[self._focus_index]
            y = focus._pos[1]
            h = focus._wh[1]
            if y < 0:
                # 计算y轴新偏移量
                offset = -y
                # 调整子控件的位置以更新布局
                for child in self._childen:
                    child._pos = (child._pos[0], child._pos[1] + offset)
            elif y + h >= self._wh[1]:
                offset = self._wh[1] - y - h - 1
                for child in self._childen:
                    child._pos = (child._pos[0], child._pos[1] + offset)
