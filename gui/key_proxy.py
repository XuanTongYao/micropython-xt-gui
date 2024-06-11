# 这是一个处理物理按键输入的模块
from time import sleep_ms
from array import array
from machine import Pin
from machine import Timer
import micropython


def _NullFunc(_):
    pass


RELEASED = const(0)
DEBOUNCE = const(1)
PRESSED = const(2)
HOLDED = const(3)

# 最短长按时间
HOLDTIME = const(1200)
# 长按后触发间隔
HOLDINTERVAL = const(200)
# 扫描速度(毫秒)
SCANSPEED = const(10)
# 长按时间系数
HOLDK = const(HOLDTIME // SCANSPEED)


class KeyProxy:
    """物理按键代理模块，自带消抖，自定义按下触发、释放触发、长按触发

    按键为0时表示按下
    """

    def __init__(self, keys: list) -> None:
        init_len = len(keys)
        self.__fsms = array("B", [RELEASED] * init_len)
        self.__pressed_time = array("H", [0] * init_len)
        self.press_callbacks: list = [_NullFunc] * init_len
        self.release_callbacks: list = [_NullFunc] * init_len
        self.hold_callbacks: list = [_NullFunc] * init_len
        self.press_args: list = [None] * init_len
        self.release_args: list = [None] * init_len
        self.hold_args: list = [None] * init_len
        self.__keys = list(keys)
        interval_timer = Timer()
        interval_timer.init(
            mode=Timer.PERIODIC, period=HOLDINTERVAL, callback=self.hold_interval
        )

    def scan(self):
        """按键扫描"""
        fsms = self.__fsms
        pressed_time = self.__pressed_time
        press_callbacks = self.press_callbacks
        release_callbacks = self.release_callbacks
        press_args = self.press_args
        release_args = self.release_args
        for i, key in enumerate(self.__keys):
            if key() == 0:
                if fsms[i] == RELEASED:
                    fsms[i] = DEBOUNCE
                elif fsms[i] == DEBOUNCE:
                    fsms[i] = PRESSED
                    micropython.schedule(press_callbacks[i], press_args[i])
                elif fsms[i] == PRESSED:
                    pressed_time[i] += 1
                    if HOLDK == pressed_time[i]:
                        fsms[i] = HOLDED
            else:
                if fsms[i] == HOLDED or fsms[i] == PRESSED:
                    micropython.schedule(release_callbacks[i], release_args[i])
                fsms[i] = RELEASED
                pressed_time[i] = 0
        sleep_ms(SCANSPEED)

    def hold_interval(self, _):
        for CALLBACK, State, Args in zip(
            self.hold_callbacks, self.__fsms, self.hold_args
        ):
            if State == HOLDED:
                micropython.schedule(CALLBACK, Args)

    def append_key(
        self,
        key,
        press_callback=_NullFunc,
        release_callback=_NullFunc,
        hold_callback=_NullFunc,
    ):
        self.__fsms.append(RELEASED)
        self.__pressed_time.append(0)
        self.press_callbacks.append(press_callback)
        self.release_callbacks.append(release_callback)
        self.hold_callbacks.append(hold_callback)
        self.__keys.append(key)


class KeyProxySimplified:
    """物理按键代理模块简化版，自带消抖，只支持自定义按下触发

    按键为0时表示按下"""

    def __init__(self, keys: list) -> None:
        init_len = len(keys)
        self.__fsms = array("B", [RELEASED] * init_len)
        self.press_callbacks: list = [_NullFunc] * init_len
        self.press_args: list = [None] * init_len
        self.__keys = list(keys)

    def scan(self):
        """按键扫描"""
        fsms = self.__fsms
        press_callbacks = self.press_callbacks
        press_args = self.press_args
        for i, key in enumerate(self.__keys):
            if key() == 0:
                if fsms[i] == RELEASED:
                    fsms[i] = DEBOUNCE
                elif fsms[i] == DEBOUNCE:
                    fsms[i] = PRESSED
                    micropython.schedule(press_callbacks[i], press_args[i])
            else:
                fsms[i] = RELEASED
        sleep_ms(SCANSPEED)

    def append_key(
        self,
        key,
        press_callback=_NullFunc,
    ):
        self.__fsms.append(RELEASED)
        self.press_callbacks.append(press_callback)
        self.__keys.append(key)
