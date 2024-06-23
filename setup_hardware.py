from machine import Pin, SPI
from driver import st7789

# 请根据自身硬件情况更改引脚和波特率
# 初始化显示屏
spi0 = SPI(0, baudrate=30_000_000, phase=1, polarity=1, sck=Pin(2), mosi=Pin(3))
display_driver = st7789.ST7789(
    spi0, 240, 240, reset=Pin(0, Pin.OUT), dc=Pin(1, Pin.OUT)
)
display = st7789.ST7789_API(display_driver)
