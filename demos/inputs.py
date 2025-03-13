import setup_hardware
from gui import ufont
from gui.utils.core import *
from gui.key_handler import KeyHandler
from gui.xt_gui import XT_GUI
from gui.widgets.inputs import XSlider, XSpinBox
from gui.widgets.buttons import XButton

# 创建XT_GUI实例
GUI = XT_GUI(
    setup_hardware.display,
    ufont.BMFont("./resource/fonts/for_demo/16x16_text_demo.bmf", load_into_mem=True),
    loop_focus=True,
)


slide = XSlider((0, 0), (200, 30), 0, 100)
spinbox = XSpinBox((0, 60), (65, 20), 0, 100, suffix="KG")


def echo():
    print(f"Slide百分比:{slide.percent}")
    print(f"SpinBox数据:{spinbox.value}")


show_button = XButton((0, 100), callback=echo, text="echo")

# 添加控件
GUI.add_widgets((slide, spinbox, show_button))


key_esc = KeyHandler(setup_hardware.BTN_ESCAPE, press=(GUI.key_response, KEY_ESCAPE))
key_enter = KeyHandler(setup_hardware.BTN_ENTER, press=(GUI.key_response, KEY_MOUSE0))
key_next = KeyHandler(setup_hardware.BTN_DOWN, press=(GUI.key_response, KEY_DOWN))
key_prev = KeyHandler(setup_hardware.BTN_UP, press=(GUI.key_response, KEY_UP))

key_prtsc = KeyHandler(setup_hardware.BTN_PRTSC, press=(GUI.snapshot,))
GUI.run(key_esc, key_enter, key_next, key_prev, key_prtsc)
