import setup_hardware
from gui import ufont
from gui.utils.core import *
from gui.key_handler import KeyHandler
from gui.xt_gui import XT_GUI
from gui.widgets.containers import XListView
from gui.widgets.buttons import XButton
from gui.widgets.base import XLayout, XText
from gui.widgets.displayers import XPlainTextView

import os


# 创建XT_GUI实例
GUI = XT_GUI(
    setup_hardware.display,
    ufont.BMFont("./resource/fonts/for_demo/16x16_text_demo.bmf", load_into_mem=True),
    loop_focus=True,
)


# 主界面
GUI.add_widget(XText((0, 0), "eBook", BLUE))
file_list = XListView((0, 16), (240, 224))
GUI.add_widget(file_list)


# 打开文本
def open_book(filename):
    global textview, text
    print("打开文件: " + filename)
    GUI.add_layer(specified_layout=textview)
    with open("./resource/books/" + filename, "r", encoding="UTF-8") as f:
        textview.set_text(f.read())


# 遍历books目录
for book in os.listdir("./resource/books/"):
    print(book)
    func = lambda book=book: open_book(book)
    file_list.add_widget(XButton((0, 0), (0, 16 + 6), func, text=book))


# 文本显示区
textview = XPlainTextView((0, 0), (240, 240))

key_esc = KeyHandler(setup_hardware.BTN_ESCAPE, press=(GUI.key_response, KEY_ESCAPE))
key_enter = KeyHandler(setup_hardware.BTN_ENTER, press=(GUI.key_response, KEY_MOUSE0))
key_next = KeyHandler(setup_hardware.BTN_DOWN, press=(GUI.key_response, KEY_DOWN))
key_prev = KeyHandler(setup_hardware.BTN_UP, press=(GUI.key_response, KEY_UP))

key_prtsc = KeyHandler(setup_hardware.BTN_PRTSC, press=(GUI.snapshot,))
GUI.run(key_esc, key_enter, key_next, key_prev, key_prtsc)
