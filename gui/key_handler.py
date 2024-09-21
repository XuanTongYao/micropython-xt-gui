# 这是一个处理物理按键输入的模块
import micropython
import asyncio

# 状态机常量
_RELEASED = const(0)
_DEBOUNCED = const(1)
_PRESSED = const(2)
_HOLDED = const(3)

# 去抖动时间
DEBOUNCE_MS = const(50)
# 长按时间阈值
HOLD_MS = const(1200)
# 长按后触发间隔
HOLD_INTERVAL_MS = const(200)


# 单个物理按键处理
class KeyHandler:

    def __init__(self, key, active=0) -> None:
        """
        Args:
            key: 按键对象，可以是Pin或其他，必须实现__call__方法用于获取按键值.
            active: 按键按下有效值. 默认0表示按下.
        """
        if not callable(key):
            raise TypeError("key must be callable to get value")
        self.key = key
        self.active = active

        self.set_press_func(None)
        self.set_release_func(None)
        self.set_hold_func(None)

        self.__fsm = _RELEASED
        self.__reach_hold = False

    def __call__(self):
        self.__hold_sleep_task = asyncio.create_task(self.__hold_check(HOLD_MS / 1000))
        self.__scan_loop_task = asyncio.create_task(self.__do_scan_loop())

    def set_press_func(self, func, arg=()) -> None:
        self.__press_callback = func
        self.__press_arg = arg

    def set_release_func(self, func, arg=()) -> None:
        self.__release_callback = func
        self.__release_arg = arg

    def set_hold_func(self, func, arg=()) -> None:
        self.__hold_callback = func
        self.__hold_arg = arg

    async def __do_scan_loop(self):
        while True:
            hold_sleep_task = self.__hold_sleep_task
            # 状态机
            if self.key() == self.active:
                if self.__fsm == _RELEASED:
                    self.__fsm = _DEBOUNCED
                elif self.__fsm == _DEBOUNCED:
                    self.__fsm = _PRESSED
                    hold_sleep_task.cancel()
                    self.__hold_sleep_task = asyncio.create_task(
                        self.__hold_check(HOLD_MS / 1000)
                    )
                    if self.__press_callback is not None:
                        micropython.schedule(self.__press_callback, self.__press_arg)
                elif (
                    self.__fsm == _PRESSED or self.__fsm == _HOLDED
                ) and self.__reach_hold:
                    self.__fsm = _HOLDED
                    self.__reach_hold = False
                    hold_sleep_task.cancel()
                    self.__hold_sleep_task = asyncio.create_task(
                        self.__hold_check(HOLD_INTERVAL_MS / 1000)
                    )
                    if self.__hold_callback is not None:
                        micropython.schedule(self.__hold_callback, self.__hold_arg)
            else:
                if (
                    self.__fsm == _PRESSED or self.__fsm == _HOLDED
                ) and self.__release_callback is not None:
                    micropython.schedule(self.__release_callback, self.__release_arg)
                self.__fsm = _RELEASED
            await asyncio.sleep(DEBOUNCE_MS / 1000)

    async def __hold_check(self, time_sec):
        try:
            await asyncio.sleep(time_sec)
            self.__reach_hold = self.__fsm == _PRESSED
        finally:
            pass

    def stop_scan(self):
        """释放资源前必须手动调用此方法"""
        self.__hold_sleep_task.cancel()
        self.__scan_loop_task.cancel()
