import gc
from machine import ADC

# 硬件参数调教(Hardware parameter tuning)
# 参数设置都是按照16位精度设置的
# 请根据自身硬件的情况调整
_DEADZONE = const(100)
_CENTER_X = const(32795)
_CENTER_Y = const(31950)
_MAX_X = const(65270)
_MAX_Y = const(63950)
_MIN_X = const(230)
_MIN_Y = const(210)

_TOTAL_SPACE_MAX_X = const(_MAX_X - _CENTER_X)
_TOTAL_SPACE_MAX_Y = const(_MAX_Y - _CENTER_Y)
_TOTAL_SPACE_MIN_X = const(_CENTER_X - _MIN_X)
_TOTAL_SPACE_MIN_Y = const(_CENTER_Y - _MIN_Y)


class FJ08K:

    class _SimulateKey:
        def __init__(self, GetAXIS_Func, Precent, Zoom=1.0) -> None:
            self.__AXIS = GetAXIS_Func
            self.__Precent = Precent
            self.__Zoom = Zoom

        def __call__(self) -> int:
            return int(self.__AXIS() * self.__Zoom < self.__Precent)

    def __init__(
        self, X_AXIS: ADC, Y_AXIS: ADC, X_AXIS_ZOOM=1.0, Y_AXIS_ZOOM=1.0
    ) -> None:
        """X_AXIS为ADC类对象"""
        self.X_AXIS = X_AXIS
        self.Y_AXIS = Y_AXIS
        self.X_AXIS_ZOOM = X_AXIS_ZOOM
        self.Y_AXIS_ZOOM = Y_AXIS_ZOOM

    def x_hp(self) -> float:
        """硬件参数调教输出"""
        X = self.X_AXIS.read_u16()
        X_TO_CEN = X - _CENTER_X
        if X >= _MAX_X:
            return 1
        elif X <= _MIN_X:
            return -1

        if -50 <= X_TO_CEN <= 50:
            return 0
        elif 50 < X_TO_CEN:
            return X_TO_CEN / _TOTAL_SPACE_MAX_X
        else:
            return X_TO_CEN / _TOTAL_SPACE_MIN_X

    def y_hp(self) -> float:
        """硬件参数调教输出"""
        Y = self.Y_AXIS.read_u16()
        Y_TO_CEN = Y - _CENTER_Y
        if Y >= _MAX_Y:
            return 1
        elif Y <= _MIN_Y:
            return -1

        if -50 <= Y_TO_CEN <= 50:
            return 0
        elif 50 < Y_TO_CEN:
            return Y_TO_CEN / _TOTAL_SPACE_MAX_Y
        else:
            return Y_TO_CEN / _TOTAL_SPACE_MIN_Y

    def x(self) -> float:
        """软件参数调教输出"""
        return self.x_hp() * self.X_AXIS_ZOOM

    def y(self) -> float:
        """软件参数调教输出"""
        return self.y_hp() * self.Y_AXIS_ZOOM

    def get_simulate_key(self, which) -> _SimulateKey:
        """模拟按键，将摇杆作为按键输入

        Args:
            Which:
                0 - 左
                1 - 上
                2 - 右
                3 - 下

        Returns:
            一个对象,实现了类似machine.Pin的__call__方法，用于查询按键是否按下
        """
        if which == 0:
            return self._SimulateKey(self.x, 0.5, -1.0)
        elif which == 1:
            return self._SimulateKey(self.y, 0.5, -1.0)
        elif which == 2:
            return self._SimulateKey(self.x, 0.5)
        else:
            return self._SimulateKey(self.y, 0.5)


gc.collect()
