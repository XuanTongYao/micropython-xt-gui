import setup_hardware
from gui import ufont
from gui.utils.core import *
from gui.key_handler import KeyHandler
from gui.xt_gui import XT_GUI
from gui.widgets.buttons import XButton, XCheckbox, XRadio

# 创建XT_GUI实例
GUI = XT_GUI(
    setup_hardware.display,
    ufont.BMFont("./resource/fonts/for_demo/16x16_text_demo.bmf", load_into_mem=True),
    loop_focus=True,
)


def print_hello():
    print("Hello world!")


hello_button = XButton((0, 0), text="你好", key_press=print_hello)
hello_checkbox = XCheckbox((38, 0), (49, 16), 16, text="你好")
hello_radio = XRadio((87, 0), (49, 16), 16, text="你好")

# 添加控件
for widget in [hello_button, hello_checkbox, hello_radio]:
    GUI.add_widget(widget)


key_esc = KeyHandler(setup_hardware.BTN_ESCAPE)
key_esc.set_press_func(GUI.key_response, KEY_ESCAPE)
key_enter = KeyHandler(setup_hardware.BTN_ENTER)
key_enter.set_press_func(GUI.key_response, KEY_MOUSE0)
key_next = KeyHandler(setup_hardware.BTN_DOWN)
key_next.set_press_func(GUI.key_response, KEY_DOWN)

GUI.run(key_esc, key_enter, key_next)
