from machine import Pin, SPI
from driver import st7789
from gui.utils import DisplayAPI

# 请根据自身硬件情况更改引脚和波特率等
# 初始化显示屏
spi0 = SPI(0, baudrate=30_000_000, phase=1, polarity=1, sck=Pin(2), mosi=Pin(3))
display_driver = st7789.ST7789(
    spi0, 240, 240, reset=Pin(0, Pin.OUT), dc=Pin(1, Pin.OUT)
)
display_driver.set_fullscreen()
display = DisplayAPI(display_driver)


# 请根据自身硬件情况更改按键引脚

# 退出按键
BTN_ESCAPE = Pin(5, Pin.IN)
# 确认/进入按键
BTN_ENTER = Pin(6, Pin.IN, Pin.PULL_UP)
# # 下键
# BTN_DOWN = Pin(7, Pin.IN, Pin.PULL_UP)
# # 上键
# BTN_UP = Pin(8, Pin.IN, Pin.PULL_UP)

# FJ08KN摇杆模拟按键
from driver import fj08kn
from machine import ADC

joystick = fj08kn.FJ08K(ADC(Pin(29)), ADC(Pin(28)))
BTN_UP = joystick.get_simulate_key(1)
BTN_DOWN = joystick.get_simulate_key(3)
