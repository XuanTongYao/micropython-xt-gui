import setup_hardware
from gui import ufont
from gui.utils.core import *
from gui.key_handler import KeyHandler
from gui.xt_gui import XT_GUI
from gui.widgets.containers import XListView
from gui.widgets.buttons import XButton

import os

# 创建XT_GUI实例
GUI = XT_GUI(
    setup_hardware.display,
    ufont.BMFont("./resource/fonts/for_demo/16x16_text_demo.bmf", load_into_mem=True),
    loop_focus=True,
)

key_esc = KeyHandler(setup_hardware.BTN_ESCAPE, press=(GUI.key_response, KEY_ESCAPE))
key_enter = KeyHandler(setup_hardware.BTN_ENTER, press=(GUI.key_response, KEY_MOUSE0))
key_next = KeyHandler(setup_hardware.BTN_DOWN, press=(GUI.key_response, KEY_DOWN))
key_prev = KeyHandler(setup_hardware.BTN_UP, press=(GUI.key_response, KEY_UP))


main = XListView((0, 0), (240, 240))
sys_setup_menu = XListView((0, 0), (240, 240))
language_menu = XListView((0, 0), (240, 240))

GUI.add_widget(main)

# 主菜单
main.add_widget(
    XButton((0, 0), text="Weather", callback=lambda: print("Weather. Just an example."))
)
main.add_widget(
    XButton((0, 0), text="Music", callback=lambda: print("Music. Just an example."))
)
main.add_widget(
    XButton(
        (0, 0),
        text="System setup",
        callback=lambda: GUI.add_layer(specified_layout=sys_setup_menu),
    )
)

# 系统设置菜单
sys_setup_menu.add_widget(XButton((0, 0), text="Time", callback=lambda: print("Time.")))
sys_setup_menu.add_widget(
    XButton((0, 0), text="Brightness", callback=lambda: print("Brightness."))
)
sys_setup_menu.add_widget(
    XButton(
        (0, 0),
        text="Language",
        callback=lambda: GUI.add_layer(specified_layout=language_menu),
    )
)

# 语言菜单
for i in ["English", "Chinese", "Japanese"]:
    language_menu.add_widget(XButton((0, 0), text=i, callback=lambda x=i: print(x)))

key_prtsc = KeyHandler(setup_hardware.BTN_PRTSC, press=(GUI.snapshot,))
GUI.run(key_esc, key_enter, key_next, key_prev, key_prtsc)
