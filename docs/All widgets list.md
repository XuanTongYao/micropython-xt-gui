# 控件列表

## 目录

- [控件列表](#控件列表)
  - [目录](#目录)
  - [基础控件](#基础控件)
  - [高级控件](#高级控件)
    - [按钮控件](#按钮控件)
    - [容器控件](#容器控件)
    - [显示控件](#显示控件)
    - [输入控件](#输入控件)
  - [特殊控件](#特殊控件)
    - [图像控件](#图像控件)

## 基础控件

[源代码](/gui/widgets/base.py)

最基础的控件，其中规定了控件的基本属性，默认行为。所有控件都要继承它们中的一个或多个类。
除了XText，不建议直接使用基础控件。

| 类                                      | 描述                                               |
| --------------------------------------- | -------------------------------------------------- |
| [XWidget](./basic_widgets/Base.md)      | 所有控件类的基类                                   |
| [XCtrl](./basic_widgets/Base.md)        | 所有可控制控件类的基类                             |
| [XLayout](./basic_widgets/Base.md)      | 所有容器控件类的基类，带有无边框基础平面布局       |
| [XFrameLayout](./basic_widgets/Base.md) | 支持焦点切换的容器控件类基类，带有可选边框平面布局 |
| [XText](./basic_widgets/Base.md)        | 文字显示控件                                       |

## 高级控件

从基础控件继承的，具有更多功能的控件。

### 按钮控件

[源代码](/gui/widgets/buttons.py)

各种按钮。

| 类                                         | 描述   |
| ------------------------------------------ | ------ |
| [XButton](./advanced_widgets/Buttons.md)   | 按钮   |
| [XRadio](./advanced_widgets/Buttons.md)    | 单选框 |
| [XCheckbox](./advanced_widgets/Buttons.md) | 复选框 |

### 容器控件

[源代码](/gui/widgets/containers.py)

允许包含多个子控件，具有布局和焦点控制的容器控件。

| 类                                            | 描述               |
| --------------------------------------------- | ------------------ |
| [XListView](./advanced_widgets/Containers.md) | 列表视图           |
| [XVHBox](./advanced_widgets/Containers.md)    | 垂直/水平盒子视图  |
| [XGridBox](./advanced_widgets/Containers.md)  | 网格盒子视图 |

### 显示控件

[源代码](/gui/widgets/displayers.py)

用于显示某样东西的控件，可能具有控制的功能。

| 类                                                 | 描述             |
| -------------------------------------------------- | ---------------- |
| [XPlainTextView](./advanced_widgets/Displayers.md) | 多页翻页显示文本 |

### 输入控件

[源代码](/gui/widgets/inputs.py)

| 类                                       | 描述       |
| ---------------------------------------- | ---------- |
| [XSlider](./advanced_widgets/Inputs.md)  | 滑块滑动条 |
| [XSpinBox](./advanced_widgets/Inputs.md) | 整数选择框 |

## 特殊控件

### 图像控件

[源代码](/gui/widgets/image.py)

| 类                                | 描述   |
| --------------------------------- | ------ |
| [XImage](./basic_widgets/Base.md) | 2D图像 |
