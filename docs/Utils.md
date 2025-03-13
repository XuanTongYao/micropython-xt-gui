# 实用工具

- [实用工具](#实用工具)
  - [颜色常量定义](#颜色常量定义)
  - [按键键值定义](#按键键值定义)
  - [内建事件定义](#内建事件定义)
  - [核心](#核心)
    - [DisplayAPI](#displayapi)
    - [色彩转换函数](#色彩转换函数)
  - [2D纹理](#2d纹理)

## 颜色常量定义

[源码](/gui/utils/colors.py)

- `BLACK = const(0x0000)`
- `BLUE = const(0x1F00)`
- `RED = const(0x00F8)`
- `GREEN = const(0xE007)`
- `CYAN = const(0x0FF7)`
- `MAGENTA = const(0x1FF8)`
- `YELLOW = const(0xE0FF)`
- `WHITE = const(0xFFFF)`

## 按键键值定义

[源码](/gui/utils/key.py)

按键值(按键代码)

- `KEY_ESCAPE = const(0)`
- `KEY_MOUSE0 = const(1)`
- `KEY_MOUSE1 = const(2)`
- `KEY_LEFT = const(3)`
- `KEY_UP = const(4)`
- `KEY_RIGHT = const(5)`
- `KEY_DOWN = const(6)`

按键响应返回值

- `ESC = const(0)`
- `ENTER = const(1)`

## 内建事件定义

[源码](/gui/utils/event.py)

- `TRANSFER_EVENT = const(0)`
- `REBUILD_DRAW_AREA_EVENT = const(1)`
- `CLEAR_DRAW_AREA_EVENT = const(2)`

## 核心

### DisplayAPI

`DisplayAPI`类是屏幕驱动通用接口，作为GUI核心与显示驱动的中间件，内部维护帧缓冲区，实现双缓冲绘图。

```py
display_driver=ST7789(...)
display = DisplayAPI(display_driver)
```

构造时需要传入一个参数为显示器驱动对象。我们并不关心该对象内部如何实现的，该对象只需要提供以下的属性和方法供我们使用即可。

```py
# 显示器像素宽高
width: int
height: int
# 显示器颜色模式
color_mode: int
def write_gddram(self, buffer:bytearray):
  """
  将buffer中的像素数据写入到显示器
  buffer包含了全屏幕的像素数据
  """
  ...
```

- 显示器颜色模式应该是定义在[framebuf](https://docs.micropython.org/en/latest/library/framebuf.html)库中的常量。
- 对于传入函数`write_gddram`的参数`buffer`，其内部像素数据的组成方式取决于使用的显示器颜色模式。

---

`DisplayAPI`类可以调用`framebuf_slice(self, x, y, w, h)`方法创建[帧缓冲切片](/Readme.md#帧缓冲切片)。

---

`DisplayAPI`类实现了类`XLayout`透明化，在有关绘制的方法中，`DisplayAPI`实例可以作为控件的父类，并且访问那些通常是`XLayout`类才拥有的属性，包括但不限于：`_layout_pos`、`get_absolute_pos()`

### 色彩转换函数

```py
# rgb888 转 rgb565
def rgb888_to_rgb565(r8: int, g8: int, b8: int, big_endian=False) -> int:
  ...

# 分离rgb565的rgb值
def separate_rgb565(rgb565: int, big_endian=False) -> tuple[int, int, int]:
  ...

# 合并rgb565的rgb值
def combined_rgb565(r5: int, g6: int, b5: int, big_endian=False) -> int:
  ...
```

## 2D纹理

实用工具中包含了一个[Texture2D](/gui/utils/texture.py)类，用于图片/图像绘制。实现了流式纹理和内存纹理(完全加载到内存中的)，同时包含各种图像格式的解码器。

在使用中通过创建[XImage](/docs/special_widgets/Image.md)控件来绘制图像，由于解码图像需要消耗大量的内存、解码函数也十分庞大，非必要时不import该模块。

目前已经支持的图像格式:

- PBM_P4 完全支持
- PNG 基本支持，不支持16位样本色深，不支持Alpha通道

> Texture2D只关心能够影响图像绘制的数据。
