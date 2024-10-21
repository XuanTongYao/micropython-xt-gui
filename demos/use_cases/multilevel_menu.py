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

key_esc = KeyHandler(setup_hardware.BTN_ESCAPE)
key_esc.set_press_func(GUI.key_response, KEY_ESCAPE)
key_enter = KeyHandler(setup_hardware.BTN_ENTER)
key_enter.set_press_func(GUI.key_response, KEY_MOUSE0)
key_next = KeyHandler(setup_hardware.BTN_DOWN)
key_next.set_press_func(GUI.key_response, KEY_DOWN)
key_prev = KeyHandler(setup_hardware.BTN_UP)
key_prev.set_press_func(GUI.key_response, KEY_UP)


main = XListView((0, 0), (240, 240))
sys_setup_menu = XListView((0, 0), (240, 240))
language_menu = XListView((0, 0), (240, 240))

GUI.add_widget(main)

# 主菜单
main.add_widget(
    XButton(
        (0, 0), text="Weather", key_press=lambda: print("Weather. Just an example.")
    )
)
main.add_widget(
    XButton((0, 0), text="Music", key_press=lambda: print("Music. Just an example."))
)
main.add_widget(
    XButton(
        (0, 0),
        text="System setup",
        key_press=lambda: GUI.add_layer(specified_layout=sys_setup_menu),
    )
)

# 系统设置菜单
sys_setup_menu.add_widget(
    XButton((0, 0), text="Time", key_press=lambda: print("Time."))
)
sys_setup_menu.add_widget(
    XButton((0, 0), text="Brightness", key_press=lambda: print("Brightness."))
)
sys_setup_menu.add_widget(
    XButton(
        (0, 0),
        text="Language",
        key_press=lambda: GUI.add_layer(specified_layout=language_menu),
    )
)

# 语言菜单
for i in ["English", "Chinese", "Japanese"]:
    language_menu.add_widget(XButton((0, 0), text=i, key_press=lambda x=i: print(x)))

GUI.run(key_esc, key_enter, key_next, key_prev)
