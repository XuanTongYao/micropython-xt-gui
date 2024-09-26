from .base import XWidget
from ..utils.core import combined_rgb565, separate_rgb565
from ..utils.texture import *
from ..utils.colors import WHITE


class XImage(XWidget):

    def __init__(
        self,
        pos,
        wh,
        raw_data: str | bytes,
        color=WHITE,
        background_color=None,
        *,
        texture2d: Texture2D | None = None,
        stream_loading=True
    ) -> None:
        super().__init__(pos, wh, color)
        self.background_color = background_color
        # 读取文件并判断格式
        self.texture = (
            Texture2D(raw_data, not stream_loading) if texture2d is None else texture2d
        )
        self.img_type = self.texture.img_format
        self.index_color = False

        if self.texture.color_mode != framebuf.RGB565:
            self.palette_used = True
            if self.texture.palette_used:
                self.palette = self.texture.palette
            else:
                color_num = 2**self.texture.bitdepth
                self.palette = framebuf.FrameBuffer(
                    bytearray(2 * color_num), color_num, 1, framebuf.RGB565
                )
                # 灰度颜色插值
                r, g, b = separate_rgb565(color, True)
                for i in range(0, color_num):
                    ratio = i / (color_num - 1)
                    r_ = ceil(r * ratio)
                    g_ = ceil(g * ratio)
                    b_ = ceil(b * ratio)
                    self.palette.pixel(i, 0, combined_rgb565(r_, g_, b_, True))
                if background_color is not None:
                    self.palette.pixel(0, 0, background_color)
        else:
            self.palette_used = False

    def draw(self) -> None:
        if self._layout is None:
            return

        # 如果纹理是以bitmap方式加载的，可以直接绘制
        # 如果纹理是以流式方式或非bitmap加载的，则需要使用迭代器逐行绘制
        x, y = self._pos

        texture = self.texture

        if self.palette_used:
            palette = self.palette
            alpha_color = 0 if self.background_color is None else -1
            if texture.type == Texture2D.TEX_BITMAP:
                self._layout.blit(
                    texture.bitmap_frame, *self._pos, alpha_color, palette
                )
            else:
                for row_frame in texture:
                    self._layout.blit(row_frame, x, y, alpha_color, palette)
                    y += 1
        else:
            if texture.type == Texture2D.TEX_BITMAP:
                self._layout.blit(texture.bitmap_frame, *self._pos)
            else:
                for row_frame in texture:
                    self._layout.blit(row_frame, x, y)
                    y += 1
