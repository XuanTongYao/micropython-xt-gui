from driver import fj08kn, st7789
from gui.widgets.containers import XListView
from machine import Pin, SPI, ADC, PWM
from gui import ufont
from gui.xt_gui import *
from gui.widgets.buttons import *
from gui.widgets.inputs import *
from gui.key_proxy import KeyProxy
import gui.xt_gui as XTGUI

LED = Pin(4, Pin.OUT)
BTN_B = Pin(5, Pin.IN)
BTN_A = Pin(6, Pin.IN, Pin.PULL_UP)
BTN_START = Pin(7, Pin.IN, Pin.PULL_UP)
BTN_SELECT = Pin(8, Pin.IN, Pin.PULL_UP)

XTGUI.DEBUG = False
# machine.freq(250000000)


spi0 = SPI(0, baudrate=30_000_000, phase=1, polarity=1, sck=Pin(2), mosi=Pin(3))
display = st7789.ST7789(spi0, 240, 240, reset=Pin(0, Pin.OUT), dc=Pin(1, Pin.OUT))
displayer = st7789.ST7789_API(display)

Joystick = fj08kn.FJ08K(ADC(Pin(29)), ADC(Pin(28)))
Up = Joystick.get_simulate_key(1)
Down = Joystick.get_simulate_key(3)


GUI = XT_GUI(
    displayer,
    ufont.BMFont("/Resource/Fonts/16x16Sim.bmf"),
    cursor_img_file="/Resource/Img/Cursor21x32.pbm",
    loop_focus=True,
)


# GUI.DrawBinaryImage("/Resource/Img/Cursor21x32.pbm", (50, 50), XT_GUI.WHITE)
def printHello(Key_ID):
    print("Hello")


B = XButton((0, 0), (32 + 6, 16 + 6), context="你好", key_input=printHello)
KL = XButton((32 + 7, 0), (32 + 6, 16 + 6), context="世界")
Checkbox = XCheckbox((32 + 7 + 32 + 7, 0), 32)
Radio = XRadio((32 + 7 + 32 + 7 + 33, 0), 32)
slider = XSlider(
    (0, 40), (50, 24), 0, 100, color=GREEN, show_text=True, orientation=XSlider.VERTICAL
)


def slider_plus_10(_):
    slider.set_value(slider.value + 10)


def slider_mius_10(_):
    slider.set_value(slider.value - 10)


listv = XListView((0, 70), (100, 100))


for w in [B, KL, Checkbox, Radio, slider, listv]:
    GUI.add_widget(w)

listv.add_widget(
    XButton((0, 0), (32 + 6, 16 + 6), context="+10", key_input=slider_plus_10)
)
listv.add_widget(
    XButton((0, 16 + 6), (32 + 6, 16 + 6), context="-10", key_input=slider_mius_10)
)


KeyP = KeyProxy([BTN_B, BTN_A, Down, Up, BTN_START])
KeyP.ReleaseArgs[0:4] = KEY_ESCAPE, KEY_MOUSE0, KEY_DOWN, KEY_UP, KEY_ESCAPE
KeyP.HoldArgs[0:4] = KEY_ESCAPE, KEY_MOUSE0, KEY_DOWN, KEY_UP, KEY_ESCAPE
KeyP.ReleaseCALLBACKs[0:4] = [GUI.key_response] * 5
KeyP.HoldCALLBACKs[0:4] = [GUI.key_response] * 5

pwm = PWM(LED)
pwm.freq(1000)


while True:
    KeyP.Scan()
    GUI.show_gui()
    if Radio.checked:
        pwm.duty_u16(int(slider.get_percent() * 65535))
    else:
        pwm.duty_u16(0)
