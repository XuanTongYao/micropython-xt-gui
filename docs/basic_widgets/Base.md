# 基础控件

- [基础控件](#基础控件)
  - [XWidget](#xwidget)
    - [属性](#属性)
    - [公共成员方法](#公共成员方法)
    - [弱私有方法](#弱私有方法)
    - [私有方法](#私有方法)
    - [详细描述](#详细描述)
  - [XCtrl](#xctrl)
    - [属性](#属性-1)
    - [公共成员方法](#公共成员方法-1)
    - [弱私有方法](#弱私有方法-1)
    - [私有方法](#私有方法-1)
    - [详细描述](#详细描述-1)
  - [XLayout](#xlayout)
    - [属性](#属性-2)
    - [公共成员方法](#公共成员方法-2)
    - [弱私有方法](#弱私有方法-2)
    - [私有方法](#私有方法-2)
    - [详细描述](#详细描述-2)
  - [XFrameLayout](#xframelayout)
    - [属性](#属性-3)
    - [公共成员方法](#公共成员方法-3)
    - [弱私有方法](#弱私有方法-3)
    - [私有方法](#私有方法-3)
    - [详细描述](#详细描述-3)
  - [XText](#xtext)
    - [属性](#属性-4)
    - [公共成员方法](#公共成员方法-4)
    - [弱私有方法](#弱私有方法-4)
    - [私有方法](#私有方法-4)
    - [详细描述](#详细描述-4)

## XWidget

**XWidget**是所有控件类的基类。

`blue_rect = XWidget((50, 50), (140, 140), BLUE)`

<!-- ![alt text](/img/1723683958363.jpg) -->

### 属性

- `_pos: tuple[int, int]`x,y坐标
- `_wh: tuple[int, int]`w,h宽高大小
- `_color: int`颜色
- `_parent: XLayout`父控件
- `_layout: FrameBuffer`父容器区域

### 公共成员方法

- `get_absolute_pos() -> tuple[int, int]:`获取控件绝对坐标。
- `draw():`绘制图形到父容器区域帧缓冲，触发绘制时会调用该函数。对于`XWidget`，这个函数会绘制一个对应参数的实心矩形。
- `_update():`更新并重新计算一些信息，触发更新时会调用该函数。使用函数对控件进行变换时会触发更新。对于`XWidget`，这个函数会将父容器区域设置为父控件的绘制区。

### 弱私有方法

### 私有方法

### 详细描述

## XCtrl

`XCtrl`是所有允许响应按键输入的控件的基类，继承自[XWidget](./Readme.md#xwidget)。

### 属性

- `focused: bool`焦点是否位于该控件
- `enter: bool`是否进入到该控件
- `_key_input: callable[int]`处理按键输入的函数，传入一个按键值参数

### 公共成员方法

### 弱私有方法

### 私有方法

### 详细描述

## XLayout

`XLayout`是拥有基础平面布局(无边框)的容器基类，继承自[XCtrl](./Readme.md#xctrl)。

### 属性

- `_childen: list[XWidget]`子控件列表
- `_draw_area`绘制区(容器区域)
- `_layout_wh: tuple[int, int]`容器宽高
- `_layout_pos: tuple[int, int]`容器相对于自身的坐标

### 公共成员方法

- `add_widget(widget: XWidget):`添加子控件并调整布局，并将所有子控件触发更新。
- `draw_deliver():`传递绘制。首先绘制自身，然后将绘制传递到子控件。
- `_calc_draw_area() -> tuple[tuple[int, int], tuple[int, int]]:`计算绘制区域，并返回容器相对坐标与宽高。
- `_create_draw_area(ignore=False):`创建绘制区域。根据`_calc_draw_area()`的返回值创建绘制区域，绘制区域会限制在父容器区域内，ignore=True时忽略父容器检查以及限制(只适用于顶层容器)。
- `_update():`首先执行父类的同名函数，然后创建绘制区域，并将触发更新传递给子控件。
- `_adjust_layout():`调整布局。
- `_add_widget(widget: XWidget):`添加控件到子控件列表并设置控件的父控件为当前控件。

### 弱私有方法

### 私有方法

### 详细描述

## XFrameLayout

`XFrameLayout`是所有的非底层容器控件的基类，自带一个可选边框平面布局，同时也是GUI默认的顶层容器，继承自[XLayout](./Readme.md#xlayout)。

`frame = XFrameLayout((50, 50), (140, 140), frame=True, color=BLUE)`

![alt text](/img/1723683958342.jpg)

### 属性

- `_focus_list: list[XCtrl]`焦点列表
- `_focus_index: int`当前焦点
- `_loop_focus: bool`是否允许循环切换焦点
- `_frame: bool`是否开启边框
- `_top: bool`是否为顶层容器

### 公共成员方法

- `_key_response(key: int) -> (XCtrl | int | None):`处理按键响应。负责焦点切换，控件的进入与退出。

### 弱私有方法

### 私有方法

### 详细描述

## XText

`XText`是显示文字的一个类，继承自[XWidget](./Readme.md#xwidget)。

`text = XText((0, 120), context="Hello World!你好世界！", color=RED)`

![alt text](img/1723683958352.jpg)

### 属性

- `_context: str`内容
- `_line: int`最大行数

### 公共成员方法

### 弱私有方法

### 私有方法

### 详细描述
