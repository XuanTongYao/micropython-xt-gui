# 这是一个处理物理按键输入的模块
from time import sleep_ms
from array import array
from machine import Pin
from machine import Timer
import micropython


def NullFunc(_):
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
    def __init__(self, Keys: list) -> None:
        InitLen = len(Keys)
        self.__FSMs = array("B", [RELEASED for _ in range(InitLen)])
        self.__PressedTime = array("H", [0 for _ in range(InitLen)])
        self.PressCALLBACKs: list = [NullFunc for _ in range(InitLen)]
        self.ReleaseCALLBACKs: list = [NullFunc for _ in range(InitLen)]
        self.HoldCALLBACKs: list = [NullFunc for _ in range(InitLen)]
        self.PressArgs: list = [None for _ in range(InitLen)]
        self.ReleaseArgs: list = [None for _ in range(InitLen)]
        self.HoldArgs: list = [None for _ in range(InitLen)]
        self.__Keys = list(Keys)
        IntervalTimer = Timer()
        IntervalTimer.init(
            mode=Timer.PERIODIC, period=HOLDINTERVAL, callback=self.HoldInterval
        )

    def Scan(self):
        """按键扫描"""
        FSMs = self.__FSMs
        PressedTime = self.__PressedTime
        PressCALLBACKs = self.PressCALLBACKs
        ReleaseCALLBACKs = self.ReleaseCALLBACKs
        PressArgs = self.PressArgs
        ReleaseArgs = self.ReleaseArgs
        for i, Key in enumerate(self.__Keys):
            if Key() == 0:
                if FSMs[i] == RELEASED:
                    FSMs[i] = DEBOUNCE
                elif FSMs[i] == DEBOUNCE:
                    FSMs[i] = PRESSED
                    micropython.schedule(PressCALLBACKs[i], PressArgs[i])
                elif FSMs[i] == PRESSED:
                    PressedTime[i] += 1
                    if HOLDK == PressedTime[i]:
                        FSMs[i] = HOLDED
            else:
                if FSMs[i] == HOLDED or FSMs[i] == PRESSED:
                    micropython.schedule(ReleaseCALLBACKs[i], ReleaseArgs[i])
                FSMs[i] = RELEASED
                PressedTime[i] = 0
        sleep_ms(SCANSPEED)

    def HoldInterval(self, _):
        for CALLBACK, State, Args in zip(
            self.HoldCALLBACKs, self.__FSMs, self.HoldArgs
        ):
            if State == HOLDED:
                micropython.schedule(CALLBACK, Args)

    def AppendKey(
        self,
        Key,
        PressCALLBACK=NullFunc,
        ReleaseCALLBACK=NullFunc,
        HoldCALLBACK=NullFunc,
    ):
        self.__FSMs.append(RELEASED)
        self.__PressedTime.append(0)
        self.PressCALLBACKs.append(PressCALLBACK)
        self.ReleaseCALLBACKs.append(ReleaseCALLBACK)
        self.HoldCALLBACKs.append(HoldCALLBACK)
        self.__Keys.append(Key)
