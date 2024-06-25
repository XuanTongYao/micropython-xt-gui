import setup_hardware
from gui import ufont
from gui.utils import *
from gui.key_handler import KeyHandler
from gui.xt_gui import XT_GUI
from gui.widgets.buttons import XButton, XCheckbox, XRadio

# 创建XT_GUI实例
GUI = XT_GUI(
    setup_hardware.display,
    ufont.BMFont("./resource/fonts/for_demo/16x16_text_demo.bmf", load_in_mem=True),
    cursor_img_file="./resource/Img/Cursor21x32.pbm",
    loop_focus=True,
)

hello_button = XButton((0, 0), (32, 16 + 6), text="你好")
you_checkbox = XCheckbox((32, 0), (32, 16), 16, text="你好")
hao_radio = XRadio((64, 0), (32, 16), 16, text="你好")

# 添加控件
for widget in [hello_button, you_checkbox, hao_radio]:
    GUI.add_widget(widget)


key_esc = KeyHandler(setup_hardware.BTN_ESCAPE)
key_esc.set_press_func(GUI.key_response, KEY_ESCAPE)
key_enter = KeyHandler(setup_hardware.BTN_ENTER)
key_enter.set_press_func(GUI.key_response, KEY_MOUSE0)
key_next = KeyHandler(setup_hardware.BTN_DOWN)
key_next.set_press_func(GUI.key_response, KEY_DOWN)

GUI.run()
