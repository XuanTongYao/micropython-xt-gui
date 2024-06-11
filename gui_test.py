from machine import Pin, SPI, PWM
from driver import st7789
from gui import ufont
from gui.utils import *
from gui.xt_gui import XT_GUI
from gui.widgets.buttons import XButton, XCheckbox, XRadio
from gui.widgets.inputs import XSlider
from gui.widgets.containers import XListView
from gui.key_proxy import KeyProxySimplified

# LED灯，进行PWM输出
LED = Pin(4, Pin.OUT)
# 请根据自身硬件情况更改引脚和上拉电阻设置
# 退出按键
BTN_ESCAPE = Pin(5, Pin.IN)
# 确认/进入按键
BTN_ENTER = Pin(6, Pin.IN, Pin.PULL_UP)
# 下键
BTN_DOWN = Pin(7, Pin.IN, Pin.PULL_UP)
# 上键
BTN_UP = Pin(8, Pin.IN, Pin.PULL_UP)

# 请根据自身硬件情况更改引脚和波特率
# 初始化显示屏
spi0 = SPI(0, baudrate=30_000_000, phase=1, polarity=1, sck=Pin(2), mosi=Pin(3))
display = st7789.ST7789(spi0, 240, 240, reset=Pin(0, Pin.OUT), dc=Pin(1, Pin.OUT))
displayer = st7789.ST7789_API(display)


# 下面的代码不需要额外更改
# 创建XT_GUI实例
GUI = XT_GUI(
    displayer,
    ufont.BMFont("./resource/fonts/16x16Sim.bmf", True),
    cursor_img_file="./resource/Img/Cursor21x32.pbm",
    loop_focus=True,
)


# 声明回调函数，用于按钮等的触发
def printHello(_):
    print("Hello")


def slider_plus_10(_):
    slider.set_value(slider.value + 10)


def slider_mius_10(_):
    slider.set_value(slider.value - 10)


# 设置了按下触发的回调，焦点选中并按下确认/进入按键会打印"Hello"
hello_button = XButton((0, 0), (32 + 6, 16 + 6), context="你好", key_input=printHello)
# 没有设置回调，按下确认按键什么都不会发生
world_b = XButton((32 + 7, 0), (32 + 6, 16 + 6), context="世界")
# 多选框演示
checkbox = XCheckbox((32 + 7 + 32 + 7, 0), 32)
# 单选框演示，勾选后PWM输出将启用
radio = XRadio((32 + 7 + 32 + 7 + 33, 0), 32)
# 滑动条，焦点选中并按下确认按键会进入到该控件，按上下键调节PWM输出占空比
slider = XSlider(
    (0, 40), (50, 24), 0, 100, color=GREEN, show_text=True, orientation=XSlider.VERTICAL
)
# 纵向列表视图演示，这是一个容器，可以添加控件到其中
listv = XListView((0, 70), (100, 100))

# 向XT_GUI实例添加上面的控件
for w in [hello_button, world_b, checkbox, radio, slider, listv]:
    GUI.add_widget(w)

# 向列表视图加入两个按钮，快速调节滑动条的值
listv.add_widget(
    XButton((0, 0), (32 + 6, 16 + 6), context="+10", key_input=slider_plus_10)
)
listv.add_widget(
    XButton((0, 16 + 6), (32 + 6, 16 + 6), context="-10", key_input=slider_mius_10)
)

# 按键消抖相关
key_p = KeyProxySimplified([BTN_ESCAPE, BTN_ENTER, BTN_DOWN, BTN_UP])
key_p.press_callbacks[0:3] = [GUI.key_response] * 4
key_p.press_args[0:3] = KEY_ESCAPE, KEY_MOUSE0, KEY_DOWN, KEY_UP

pwm = PWM(LED)
pwm.freq(1000)


while True:
    key_p.scan()
    GUI.show_gui()
    if radio.checked:
        pwm.duty_u16(int(slider.get_percent() * 65535))
    else:
        pwm.duty_u16(0)
