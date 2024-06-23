# XT_GUI 库

这是一个基于 micropython 的 轻量级 GUI 库.

使用 micropython 中的 framebuf 库，构建一个高效帧缓存，GUI 所有的绘制操作都先在帧缓存上进行再同步到 GDDRAM，速度较快。

注意：目前只支持 RGB565 屏幕

## 硬件要求

运行 python 解释器后剩余空闲内存大于整个屏幕帧缓存占用的空间，并至少留有 10KByte。

```python
# 占用空间简单计算公式
_1位单色屏 = ceil(width*height/8)
_RGB565屏 = ceil(width*height*2)
```

例如：

SSD1306 分辨率为 128x64，色彩模式 1 位单色。帧缓存占用空间为 1024 Byte；

ST7789 分辨率位 240x240，色彩模式 RGB565。帧缓存占用空间为 115,200 Byte

## 快速上手

### 远程调试(无需安装)

该方法不会改变主机的文件系统，但运行速度非常慢，而且内存占用大。

1. 准备运行`micropython`的开发板和一个`ST7789`的`LCD`屏幕，并使用 4 线串行接口的方式完成连接
2. 克隆或下载本仓库到 PC 机本地
3. 打开`setup_hardware.py`并修改相关引脚配置

   ```python
   # 请根据自身硬件情况更改引脚和波特率
   # 初始化显示屏
   spi0 = SPI(0, baudrate=30_000_000, phase=1, polarity=1, sck=Pin(2), mosi=Pin(3))
   display_driver = st7789.ST7789(
      spi0, 240, 240, reset=Pin(0, Pin.OUT), dc=Pin(1, Pin.OUT)
   )
   display = st7789.ST7789_API(display_driver)
   ```

4. 下载官方的 [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html#mpremote) 工具`pip3 install mpremote`
5. 挂载代码目录到主机(请确保运行命令时路径处于代码目录，串口不被其他程序占用)`mpremote mount .`
6. 运行你想运行的 demo`>>> import demos.widgets_demos.foo_bar`
7. 部分 demo 中有些代码需要修改引脚等

## 特性
