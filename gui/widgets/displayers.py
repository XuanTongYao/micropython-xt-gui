from .base import *
from math import floor


class XPlainTextView(XLayout):

    def __init__(self, pos, wh, default_context="", color=WHITE) -> None:
        super().__init__(pos, wh, color, self._key_response)
        self.__text = XText((0, 0), default_context)
        super().add_widget(self.__text)
        self._page_height = floor(self._wh[1] / self.__text._font_size) * self.__text._font_size  # type: ignore

    def add_widget(self, widget: XWidget) -> None:
        pass

    def set_text(self, text):
        self.__text._context = text
        self.__text._update()

    def _key_response(self, key):
        if key == KEY_ESCAPE:
            return ESC
        if key == KEY_MOUSE0:
            return ENTER
        if key == KEY_DOWN:
            self._draw_area.fill(0)
            y = self.__text._pos[1]

            self.__text._pos = (0, y - self._page_height)
        if key == KEY_UP:
            self._draw_area.fill(0)
            y = self.__text._pos[1]
            if y < 0:
                self.__text._pos = (0, y + self._page_height)
