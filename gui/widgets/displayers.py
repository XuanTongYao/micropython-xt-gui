from .base import *
from math import floor


class XPlainTextView(XLayout):
    """多行多页文本显示控件，XText本身支持多行显示。本控件支持多页翻页显示"""

    def __init__(self, pos, wh, default_context="", color=WHITE) -> None:
        super().__init__(pos, wh, color, self._key_response)
        self.__text = XText((0, 16), default_context)
        super().add_widget(self.__text)
        self._page_height = floor((self._wh[1] - 16) / self.__text._font_size) * self.__text._font_size  # type: ignore
        self._total_pages = ceil(
            len(self.__text._lines_index) * self.__text._font_size / self._page_height
        )
        self._page = 1
        self.__page_show = XText(
            (0, 0), f"1/{self._total_pages}", font_size=16, autowrap=False
        )
        super().add_widget(self.__page_show)

    def add_widget(self, widget: XWidget) -> None:
        pass

    def set_text(self, text):
        self._page = 1
        self.__text.set_context(text)
        # print("设置文本更新") # Debug
        self._total_pages = ceil(
            len(self.__text._lines_index) * self.__text._font_size / self._page_height
        )
        # print(
        #     self.__text._lines_index,
        #     "行数",
        #     len(self.__text._lines_index),
        #     "字体大小",
        #     self.__text._font_size,
        # )  # Debug
        self.__page_show.set_context(f"1/{self._total_pages}")
        self.__text._scrollbar_pos = 0

    def _key_response(self, key):
        if key == KEY_ESCAPE:
            return ESC
        if key == KEY_DOWN:
            if self._page < self._total_pages:
                self._draw_area.fill(0)

                self.__text._set_scrollbar_pos(
                    self.__text._scrollbar_pos + self._page_height
                )
                self._page += 1
                # print("下翻页")  # Debug
        if key == KEY_UP:
            if self._page > 1:
                self._draw_area.fill(0)
                self.__text._set_scrollbar_pos(
                    self.__text._scrollbar_pos - self._page_height
                )
                self._page -= 1
        self.__page_show.set_context(f"{self._page}/{self._total_pages}")
