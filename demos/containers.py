import setup_hardware
from gui import ufont
from gui.utils.core import *
from gui.key_handler import KeyHandler
from gui.xt_gui import XT_GUI
from gui.widgets.containers import XListView, XVHBox, XGridBox
from gui.widgets.buttons import XButton

# 创建XT_GUI实例
GUI = XT_GUI(
    setup_hardware.display,
    ufont.BMFont("./resource/fonts/for_demo/16x16_text_demo.bmf", load_into_mem=True),
    loop_focus=True,
)

listview = XListView((0, 0), (50, 80), color=GREEN)
for i in range(8):
    func = lambda i=i: print(f"This is button {i}")
    listview.add_widget(XButton((0, 0), callback=func, text=str(i)))

verticalbox = XVHBox((60, 0), (70, 120), color=BLUE)
horizontalbox = XVHBox((0, 150), (200, 50), color=CYAN, vertical=False)
for i in range(3):
    func = lambda i=i: print(f"This is button {i}")
    horizontalbox.add_widget(
        XButton((0, 0), callback=func, text=f"i:{str(i)}", color=GREEN)
    )
    verticalbox.add_widget(
        XButton((0, 0), callback=func, text=f"i:{str(i)}", color=GREEN)
    )

gridbox = XGridBox((140, 0), (100, 100), 3, 3)

# 添加控件
GUI.add_widgets((listview, verticalbox, gridbox, horizontalbox))

# 自动添加到最近的空位
gridbox.add_widget(
    XButton((0, 0), callback=lambda: print(f"This is button 0"), text=f"0", color=GREEN)
)
gridbox.add_widget_row_col(
    XButton(
        (0, 0), callback=lambda: print(f"This is button 3"), text=f"3", color=GREEN
    ),
    1,
    0,
)
# 自动添加到最近的空位
gridbox.add_widget(
    XButton((0, 0), callback=lambda: print(f"This is button 1"), text=f"1", color=GREEN)
)

key_esc = KeyHandler(setup_hardware.BTN_ESCAPE, press=(GUI.key_response, KEY_ESCAPE))
key_enter = KeyHandler(setup_hardware.BTN_ENTER, press=(GUI.key_response, KEY_MOUSE0))
key_next = KeyHandler(setup_hardware.BTN_DOWN, press=(GUI.key_response, KEY_DOWN))
key_prev = KeyHandler(setup_hardware.BTN_UP, press=(GUI.key_response, KEY_UP))


key_prtsc = KeyHandler(setup_hardware.BTN_PRTSC, press=(GUI.snapshot,))
GUI.run(key_esc, key_enter, key_next, key_prev, key_prtsc)
