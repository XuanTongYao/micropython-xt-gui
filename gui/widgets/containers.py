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

    def _layout(self, widget: XWidget) -> None:
        w = self._wh[0]
        oh = widget._wh[1]
        widget._pos = (0, self.widget_offset)
        widget._wh = (w - 4, oh)
        self.widget_offset += oh
