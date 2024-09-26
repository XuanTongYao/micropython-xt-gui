import setup_hardware

from gui import ufont
from gui.utils.colors import *
from gui.xt_gui import XT_GUI
from gui.widgets.base import XText

# 创建XT_GUI实例
GUI = XT_GUI(
    setup_hardware.display,
    ufont.BMFont("./resource/fonts/for_demo/16x16_text_demo.bmf", load_in_mem=True),
    cursor_img_file="./resource/Img/Cursor21x32.pbm",
    loop_focus=True,
)

hello = XText((0, 0), "Hello World!")
hello_cn = XText((0, 16), "你好，世界！")
hello_cn_0 = XText((0, 32), "你", BLUE)
hello_cn_1 = XText((16, 32), "好", RED)
hello_cn_2 = XText((32, 32), "，", GREEN)
hello_cn_3 = XText((48, 32), "世", CYAN)
hello_cn_4 = XText((64, 32), "界", MAGENTA)
hello_cn_5 = XText((80, 32), "！", YELLOW)
lorem_ipsum = XText((0, 48), "The quick brown fox jumps over the lazy dog.", RED)


# 添加控件
for widget in [
    hello,
    hello_cn,
    lorem_ipsum,
    hello_cn_0,
    hello_cn_1,
    hello_cn_2,
    hello_cn_3,
    hello_cn_4,
    hello_cn_5,
]:
    GUI.add_widget(widget)

GUI.run()
