from ..utils import *
from framebuf import FrameBuffer


FOCUSED_COLOR = RED


class XWidget:
    """控件的基类

    变换/父控件更新 -> 触发更新(重新计算一些信息)

    """

    def __init__(self, pos: tuple[int, int], wh: tuple[int, int], color=BLACK) -> None:
        """初始化控件

        Args:
            pos: (x,y)相对坐标
            wh: (w,h)宽高大小
            color: 颜色. 默认为黑色.
        """
        self._pos = pos
        self._wh = wh
        self._color = color
        self._parent: XLayout | None = None
        self._layout: FrameBuffer | None = None

    def get_absolute_pos(self) -> tuple[int, int]:
        """获取绝对位置(不可重写)"""
        if self._parent is None:
            return self._pos
        x, y = self._pos
        p_x, p_y = self._parent.get_absolute_pos()
        layout_x, layout_y = self._parent._layout_pos
        return (x + p_x + layout_x, y + p_y + layout_y)

    def draw(self) -> None:
        """绘制"""
        if self._layout is None:
            return
        x, y = self._pos
        w, h = self._wh
        self._layout.rect(x, y, w, h, self._color, True)

    def _update(self) -> None:
        if self._parent is not None:
            self._layout = self._parent._draw_area


class XCtrl(XWidget):
    """允许响应按键输入的控件基类"""

    def __init__(self, pos, wh, color=WHITE, key_input=None) -> None:
        """
        Args:
            key_input: 处理按键输入的函数,固定传入一个按键值参数\n
                对于当前进入的控件:\n
                    返回一个XCtrl对象，表示进入到该对象。\n
                    返回一个ESC，表示退出当前进入的控件。
                对于未进入但已经进入其容器的控件:\n
                    返回一个ENTER，指示上层容器需要进入到该控件。
        """
        super().__init__(pos, wh, color)
        # 光标或焦点是否到达此控件
        self.focused = False
        # 是否进入到控件
        self.enter = False
        self._key_input = key_input


class XLayout(XCtrl):
    """拥有基础布局的容器基类，无焦点控制。

    更新 -> 重新创建容器绘制区域

    添加子控件 -> 添加控件到列表 -> 对所有子控件进行调整布局

    """

    def __init__(self, pos, wh, color=WHITE, key_input=None) -> None:
        super().__init__(pos, wh, color, key_input)
        # 子控件列表
        self._childen: list[XWidget] = []
        self._draw_area = None
        # 容器宽高
        self._layout_wh = (0, 0)
        # 容器相对坐标
        self._layout_pos = (0, 0)

    def _update(self) -> None:
        super()._update()
        self._create_draw_area()
        for child in self._childen:
            child._update()

    def _calc_draw_area(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """计算绘制区域，也就是容器相对于自己的相对坐标和宽高

        Returns:
            (x相对偏移,y相对偏移), (宽,高)
        """
        return (0, 0), self._wh

    def _create_draw_area(self, ignore=False):
        """创建绘制区域(不可重写)"""
        if GuiSingle.GUI_SINGLE is None:
            return
        if self._parent is None and not ignore:
            return

        # 重写_calc_draw_area()函数即可
        (x_offset, y_offset), (w, h) = self._calc_draw_area()

        # 内部限位
        x_max, y_max = self._wh
        if x_offset < 0 or y_offset < 0 or x_offset >= x_max or y_offset >= y_max:
            self._draw_area = None
            return

        # 父容器限位
        if not ignore:
            x, y = self._pos
            x += x_offset
            y += y_offset
            x_max, y_max = self._parent._layout_wh  # type: ignore
            if x >= x_max or y >= y_max or w + x < 0 or y + h < 0:
                self._draw_area = None
                return
            if x < 0:
                x_offset = -self._pos[0]
            if y < 0:
                y_offset = -self._pos[1]
            w = min(w + x, w, x_max - x, x_max)
            h = min(y + h, h, y_max - y, y_max)

        self._layout_pos = (x_offset, y_offset)
        self._layout_wh = (w, h)
        display = GuiSingle.GUI_SINGLE.display
        if isinstance(display, DisplayAPI):
            x, y = self.get_absolute_pos()
            self._draw_area = display.framebuf_slice(x + x_offset, y + y_offset, w, h)
        else:
            raise TypeError("display must be DisplayAPI")

    def _adjust_layout(self) -> None:
        """调整布局"""
        pass

    def _add_widget(self, widget: XWidget) -> None:
        """添加控件"""
        self._childen.append(widget)
        widget._parent = self

    def add_widget(self, widget: XWidget) -> None:
        """添加子控件并调整布局(不可重写)"""
        self._add_widget(widget)
        self._adjust_layout()
        # 手动触发更新
        if self._layout is None:
            return
        for child in self._childen:
            child._update()

    def draw(self) -> None:
        pass

    def draw_deliver(self) -> None:
        """传递绘制(不可重写)"""
        self.draw()
        x_max, y_max = self._layout_wh
        for child in self._childen:
            # 超出容器不绘制
            x, y = child._pos
            if x >= x_max or y >= y_max:
                continue

            if isinstance(child, XLayout):
                child.draw_deliver()
            else:
                child.draw()


class XFrameLayout(XLayout):
    """拥有基础布局的容器基类，也是GUI的顶层容器。"""

    def __init__(
        self,
        pos,
        wh,
        loop_focus=True,
        frame=False,
        color=WHITE,
        top=False,
    ) -> None:
        """
        Args:
            loop_focus: 是否循环切换焦点.
            frame: 是否绘制边框.
            color: 边框颜色.
            top: 设置为顶层
        """
        super().__init__(pos, wh, color, self._key_response)
        # 焦点控件
        self._focus_list: list[XCtrl] = []
        self._focus_index = -1
        self._loop_focus = loop_focus
        self._frame = frame
        self._top = top

        if top and GuiSingle.GUI_SINGLE:
            # 顶层布局特殊化
            self._layout = GuiSingle.GUI_SINGLE.display
            self._create_draw_area(True)

    def _calc_draw_area(self) -> tuple[tuple[int, int], tuple[int, int]]:
        w, h = self._wh
        if self._frame:
            return (2, 2), (w - 4, h - 4)
        else:
            return (0, 0), (w, h)

    def draw(self) -> None:
        if self._layout is None:
            return
        if self._frame:
            x, y = self._pos
            w, h = self._wh
            # 边框和焦点轮廓
            layout = self._layout
            border_color = FOCUSED_COLOR if self.focused else self._color
            layout.rect(x, y, w, h, border_color)
            layout.rect(x + 1, y + 1, w - 2, h - 2, border_color)

    def _add_widget(self, widget: XWidget) -> None:
        """添加控件"""
        super()._add_widget(widget)
        # 调节焦点
        if isinstance(widget, XCtrl):
            self._focus_list.append(widget)
            if self._focus_index == -1:
                self._focus_index = 0
                if self.enter:
                    self._focus_list[self._focus_index].focused = True

    def _key_response(self, key: int):
        """处理按键响应

        对于当前进入的控件:
            返回一个XCtrl对象，表示进入到该对象
            返回一个ESC，表示退出当前进入的控件
        """
        if self.enter:
            if key == KEY_MOUSE0 and self._focus_list:
                focus = self._focus_list[self._focus_index]
                func = focus._key_input
                if func is None:
                    return
                if func(KEY_MOUSE0) == ENTER:
                    return focus
            elif key == KEY_UP or key == KEY_DOWN:
                # 焦点切换
                old_index = self._focus_index
                len_ = len(self._focus_list)
                # 判断循环焦点模式
                modulo = len_ if self._loop_focus else 999999
                if key == KEY_UP:
                    self._focus_index = (self._focus_index - 1 + modulo) % modulo
                else:
                    self._focus_index = (self._focus_index + 1) % modulo

                if 0 <= self._focus_index < len_:
                    self._focus_list[old_index].focused = False
                    self._focus_list[self._focus_index].focused = True
                else:
                    self._focus_index = old_index
            elif key == KEY_ESCAPE:
                self.enter = False
                self.focused = True
                if 0 <= self._focus_index < len(self._focus_list):
                    self._focus_list[self._focus_index].focused = False
                return ESC
        elif key == KEY_MOUSE0:
            self.enter = True
            self.focused = False
            if 0 <= self._focus_index < len(self._focus_list):
                self._focus_list[self._focus_index].focused = True
            return ENTER


class XText(XWidget):

    def __init__(
        self, pos, context: str, color=WHITE, autowrap=True, font_size=None
    ) -> None:
        super().__init__(pos, (0, 0), color)
        self._context = context
        self._autowrap = autowrap
        self._font_size = font_size
        self._lines_index: list[int] = []

    def draw(self) -> None:
        if GuiSingle.GUI_SINGLE is not None:
            GuiSingle.GUI_SINGLE.draw_text(self)

    def _update(self) -> None:
        super()._update()
        if self._parent:
            self._wh = self._parent._layout_wh
        x, y = self._pos
        w, h = self._wh
        if x >= w or y >= h:
            return

        # 预处理文本，计算出每行文本的起始索引和y坐标
        _lines_index = self._lines_index
        _lines_index.clear()
        _lines_index.append(0)
        initial_x = x

        font_size = self._font_size if self._font_size else GuiSingle.GUI_SINGLE.font.font_size  # type: ignore
        half_size = font_size >> 1
        autowarp = self._autowrap
        for i, char in enumerate(self._context):
            # 对特殊字符的处理优化
            if ord(char) < 0x20 and char != "\n":
                continue

            # 自动换行
            if autowarp and x + font_size > w:
                _lines_index.append(i)
                x = initial_x

            if char == "\n":
                x = w
                continue

            x += half_size if ord(char) <= 0x7F else font_size
        _lines_index.append(len(self._context))


class XImage(XWidget):

    def __init__(
        self, pos, wh, raw_data: str | bytes, color=WHITE, background_color=None
    ) -> None:
        super().__init__(pos, wh, color)
        self.background_color = background_color
        # 读取文件并判断格式
        self.texture = texture = Texture2D(raw_data)
        self.img_type = texture.img_type

        if texture.img_type == PBM_P4:
            self.palette = framebuf.FrameBuffer(bytearray(4), 2, 1, framebuf.RGB565)
            self.palette.pixel(1, 0, color)
            if background_color is not None:
                self.palette.pixel(0, 0, background_color)
            if texture.is_bitmap:
                self.img_frame = framebuf.FrameBuffer(
                    texture.data, texture.w, texture.h, framebuf.MONO_HLSB
                )
        elif texture.img_type == PNG:
            if texture.is_bitmap:
                self.img_frame = framebuf.FrameBuffer(
                    texture.data, texture.w, texture.h, framebuf.RGB565
                )

    def draw(self) -> None:
        if self._layout is None:
            return

        # 如果纹理是以bitmap方式加载的，可以直接绘制
        # 如果纹理是以流式方式或非bitmap加载的，则需要使用迭代器逐行绘制
        x, y = self._pos
        if self.img_type == PBM_P4:
            alpha_color = 0 if self.background_color is None else -1
            if self.texture.is_bitmap:
                self._layout.blit(self.img_frame, *self._pos, alpha_color, self.palette)
            else:
                # for unit_frame, go_next_row in self.texture:
                #     self._layout.blit(unit_frame, x, y, alpha_color, self.palette)
                #     if go_next_row:
                #         x = self._pos[0]
                #         y += 1
                #     else:
                #         x += 8
                for row_frame in self.texture:
                    self._layout.blit(row_frame, x, y, alpha_color, self.palette)
                    y += 1
        elif self.img_type == PNG:
            if self.texture.is_bitmap:
                self._layout.blit(self.img_frame, *self._pos)
            else:
                for row_frame in self.texture:
                    self._layout.blit(row_frame, x, y)
                    y += 1
