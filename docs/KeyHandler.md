# 物理按键处理

- [物理按键处理](#物理按键处理)

使用了[KeyHandler](/gui/key_handler.py)类针对单个物理按键进行消抖和其他处理。

设置三种不同的回调函数

**回调函数至少传入一个参数**，这是[schedule函数](https://docs.micropython.org/en/latest/library/micropython.html)所要求的。

```py
# 设置按下回调
def set_press_func(self, func, *args):
    ...

# 设置抬起回调
def set_release_func(self, func, *args):
    ...

# 设置长按周期性回调
def set_hold_func(self, func, *args):
    ...
```

状态机内部不断使用`asyncio.sleep`来进行消抖，因此必须使用异步模式。
