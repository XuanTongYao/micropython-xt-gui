from gui.utils.core import WHITE
from .base import *


class XListView(XFrameLayout):
    """列表视图"""

    # FIXME 如果是元素超出容器左上边界，元素内文字会从起始点绘制，而不是预期的显示出裁剪后右下部分

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
        for child in self._children:
            w = self._layout_wh[0]
            h = child._wh[1]
            child.set_transfer((0, start + offset), (w, h))
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


class XVHBox(XFrameLayout):
    """垂直/水平盒子视图。控件垂直/水平布局"""

    def __init__(self, pos, wh, color=WHITE, average=True, vertical=True) -> None:
        """
        Args:
            color: 边框颜色.
            average: 是否平均分配控件位置。
        """
        super().__init__(pos, wh, False, True, color)
        self._average = average
        self._vertical = vertical

    def _adjust_layout(self) -> None:
        spacing = 0
        if self._average:
            # 获取子控件高度和
            total_thickness = sum(
                [child._wh[self._vertical] for child in self._children]
            )
            # 计算控件间距
            spacing = max(0, (self._layout_wh[self._vertical] - total_thickness)) // (
                len(self._children) + 1
            )

        offset = spacing
        for child in self._children:
            if self._vertical:
                child.set_transfer((0, offset), (self._layout_wh[0], child._wh[1]))
            else:
                child.set_transfer((offset, 0), (child._wh[0], self._layout_wh[1]))
            offset += child._wh[self._vertical] + spacing


class XGridBox(XFrameLayout):
    """网格盒子视图。控件网格布局"""

    # 很显然添加控件需要输入行列参数
    # 但是为了保持add_widget的基本行为，已经规定了不能重写
    # 正在想一种更好的解决方法

    def __init__(self, pos, wh, row, col, color=WHITE, spacing=2) -> None:
        """
        Args:
            color: 边框颜色.
            average: 是否平均分配控件位置.
        """
        super().__init__(pos, wh, False, True, color)
        self._rows: list[list[XWidget | None]] = []
        self._rows.append([None for _ in range(col)])
        self._max_row = row
        self._max_col = col
        self._spacing = spacing

    def add_widget_row_col(self, widget: XWidget, row, col):
        if row > self._max_row or col > self._max_col or row < 0 or col < 0:
            raise IndexError("Invaild index.")
        for _ in range(row, self._max_row):
            self._rows.append([None for _ in range(self._max_col)])
        if self._rows[row][col] is None:
            self._rows[row][col] = widget
        else:
            raise IndexError("This index is not empty")
        super()._add_widget(widget)
        self._adjust_layout()

    def find_child(self, widget: XWidget) -> None | tuple[int, int]:
        for row, list_row in enumerate(self._rows):
            for col, child in enumerate(list_row):
                if widget == child:
                    return (row, col)
        return None

    def _add_widget(self, widget: XWidget):
        # 自动补位添加
        # 遍历找寻空位
        found_empty = False
        for row, list_row in enumerate(self._rows):
            for col, widget_ in enumerate(list_row):
                if widget_ is None:
                    found_empty = True
                    empty_row = row
                    empty_col = col
                    break
                else:
                    continue
            if found_empty:
                break
        if found_empty:
            self._rows[empty_row][empty_col] = widget
        elif len(list_row) < self._max_row:
            new_row: list[XWidget | None] = [None for _ in range(self._max_col)]
            new_row[0] = widget
            self._rows.append(new_row)
        else:
            raise IndexError("Space is full.")
        super()._add_widget(widget)

    def _child_weight(self, widget: XWidget):
        tmp = self.find_child(widget)
        if tmp is None:
            return -1
        return 3 * tmp[0] + tmp[1]

    def _adjust_layout(self) -> None:
        w, h = self._layout_wh
        col_width = w // self._max_col
        row_height = h // self._max_row
        y_offset = 0
        spacing = self._spacing
        double_spacing = 2 * spacing
        for row, list_row in enumerate(self._rows):
            x_offset = 0
            for col, child in enumerate(list_row):
                if child is None:
                    x_offset += col_width
                    continue
                else:
                    child.set_transfer(
                        (x_offset + spacing, y_offset + spacing),
                        (col_width - double_spacing, row_height - double_spacing),
                    )
                x_offset += col_width
            y_offset += row_height
        self._focus_list.sort(key=lambda child: self._child_weight(child))
