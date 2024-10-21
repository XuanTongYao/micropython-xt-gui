import setup_hardware
from gui import ufont
from gui.utils.core import *
from gui.key_handler import KeyHandler
from gui.xt_gui import XT_GUI
from gui.widgets.containers import XListView
from gui.widgets.buttons import XButton

# 创建XT_GUI实例
GUI = XT_GUI(
    setup_hardware.display,
    ufont.BMFont("./resource/fonts/for_demo/16x16_text_demo.bmf", load_into_mem=True),
    loop_focus=True,
)

listview = XListView((0, 0), (100, 100))
for i in range(8):
    func = lambda i=i: print(f"This is button {i}")
    listview.add_widget(XButton((0, 0), key_press=func, text=str(i)))

# 添加控件
GUI.add_widget(listview)


key_esc = KeyHandler(setup_hardware.BTN_ESCAPE)
key_esc.set_press_func(GUI.key_response, KEY_ESCAPE)
key_enter = KeyHandler(setup_hardware.BTN_ENTER)
key_enter.set_press_func(GUI.key_response, KEY_MOUSE0)
key_next = KeyHandler(setup_hardware.BTN_DOWN)
key_next.set_press_func(GUI.key_response, KEY_DOWN)
key_prev = KeyHandler(setup_hardware.BTN_UP)
key_prev.set_press_func(GUI.key_response, KEY_UP)


GUI.run(key_esc, key_enter, key_next, key_prev)
