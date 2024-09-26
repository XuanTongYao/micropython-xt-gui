from .base import *


class XListView(XFrameLayout):
    """列表视图"""

    def __init__(self, pos, wh, color=WHITE) -> None:
        """
        Args:
            color: 边框颜色.
        """
        super().__init__(pos, wh, False, True, color)
        # 最后一个子项的y轴偏移
        self.widget_offset = 0
        # 起始绘制的y轴位置(第一个子项的y轴偏移、滚动条偏移)
        self._start_offset = 0

    def _add_widget(self, widget: XWidget) -> None:
        super()._add_widget(widget)
        self.widget_offset += widget._wh[1]

    def _adjust_layout(self) -> None:
        offset = 0
        start = self._start_offset
        for child in self._childen:
            w = self._wh[0]
            h = child._wh[1]
            child._pos = (0, start + offset)
            child._wh = (w - 4, h)
            offset += h
            child._update()
        # 清空容器区域防止图形重叠
        if self._draw_area is None:
            return
        self._draw_area.fill(0)

    def _key_response(self, KEY_ID: int):
        ret_val = super()._key_response(KEY_ID)
        if KEY_ID in [KEY_UP, KEY_DOWN] and self._focus_list:
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
