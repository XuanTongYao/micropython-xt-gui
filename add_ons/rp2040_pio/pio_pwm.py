# type: ignore
from rp2 import *
from machine import Pin


@asm_pio(sideset_init=PIO.OUT_LOW)
def pwm_program():
    """
    isr: 高电平重装载寄存器
    x: 低电平重装载寄存器
    y: 高电平倒计数寄存器
    Tr = 2+(x+1)+(y+1)
    Tr 的可能值为: [4,5,6,7...] 个周期
    低电平可能周期: [2,3,4...] 个周期
    高电平可能周期: [2,3,4...] 个周期
    默认输出的波形的周期分辨率就为 1 个周期
    如果还要更加理想的话，时钟可以翻倍
    如果控制x,y为偶数，则:
    Tr 可能周期: [2,3,4...]
    高/低电平可能周期: [1,2,3,4...]
    如果只是时钟频率翻倍，则:
    Tr 可能周期: [2,2.5,3,3.5,4...]
    高/低电平可能周期: [1,1.5,2,2.5,3...]
    周期精度0.5
    """
    mov(y, x).side(0)  # 低电平周期重装载
    label("low level loop")
    jmp(y_dec, "low level loop")

    mov(y, isr).side(1)  # 高电平周期重装载
    label("high level loop")
    jmp(y_dec, "high level loop")


class PIO_PWM:

    def __init__(self, pin: Pin, clock_freq=2_000, period=2, sm_id=0) -> None:
        """
        sm_id: 指定状态机的ID
        clock_freq: 时钟频率(最小为2*sys_clk/65535,最大sys_clk/2)
        period: 周期[2,2^32-1]
        """
        self._sm = StateMachine(sm_id)
        self._sm.init(pwm_program, clock_freq * 2, sideset_base=pin)
        if period < 2:
            raise ValueError("period must >=2")
        self._period = period
        self._high_period = period // 2
        self._low_period = period - self._high_period
        self.high_level_period(self._high_period)
        self.low_level_period(self._low_period)
        self._sm.active(1)

    def duty_u16(self, value: int | None = None) -> int:
        """仅仅是为了兼容machine.PWM的接口，实际可控制占空比取决于period的设置"""
        if value is None:
            return (65535 * self._high_period) // self._period
        value = self._period * value // 65535
        self.duty(value)
        return (65535 * self._high_period) // self._period

    def duty(self, value: int | None = None) -> int:
        """设置 获取 脉宽周期(占空比)
        value: 脉宽周期 [1, period-1]
        """
        if value is None:
            return self._high_period
        period = self._period
        self._high_period = max(1, min(value, period - 1))
        self._sm.put((self._high_period - 1) * 2)
        self._sm.exec("pull()")
        self._sm.exec("mov(isr, osr)")

        self._low_period = period - self._high_period
        self._sm.put((self._low_period - 1) * 2)
        self._sm.exec("pull()")
        self._sm.exec("mov(x, osr)")
        return self._high_period

    def high_level_period(self, value: int | None = None):
        if value is None:
            return self._high_period
        if value < 1:
            raise ValueError("value must >=1")
        self._high_period = value
        self._period = self._high_period + self._low_period
        self._sm.put((self._high_period - 1) * 2)
        self._sm.exec("pull()")
        self._sm.exec("mov(isr, osr)")

    def low_level_period(self, value: int | None = None):
        if value is None:
            return self._low_period
        if value < 1:
            raise ValueError("value must >=1")
        self._low_period = value
        self._period = self._high_period + self._low_period
        self._sm.put((self._low_period - 1) * 2)
        self._sm.exec("pull()")
        self._sm.exec("mov(x, osr)")

    def freq(self):
        return 0


@asm_pio(sideset_init=PIO.OUT_LOW)
def pwm_prog_example():
    """
    这是官方的例程:
    isr: 周期寄存器
    osr: 占空比影子寄存器
    x: 占空比寄存器
    y: 倒计数寄存器

    pwmloop部分等价于下面的C语言代码
    int x = 5, y = 10;
    do {
        if (x != y) continue;
        nop();
    } while (y--);
    首先循环本身消耗y+1个周期
    循环内部if (x != y)消耗y+1个周期
    nop();1个周期
    可见最后得到的信号周期为Tr=3+2*(y+1)+1
    Tr 的可能值为: [6,8,10,...] 偶数个周期
    最终输出的波形的周期分辨率为 2个周期
    要精确到1个周期的控制，需要时钟频率翻倍，但是最短周期也为3个周期
    周期[3,2^32-1]
    脉宽周期 [1, period-2]
    性能比较受限，好处是从外部更改占空比不占用正常周期，可以DMA驱动
    """
    pull(noblock).side(0)  # 周期结束拉取TX FIFO 到 osr
    mov(x, osr)  # 更新占空比
    mov(y, isr)  # 倒计数重装载

    label("pwmloop")
    jmp(x_not_y, "skip")
    nop().side(1)
    label("skip")
    jmp(y_dec, "pwmloop")


class PIO_PWM_Official_Program:

    def __init__(self, pin: Pin, sm_id=0, clock_freq=2000, period=2000) -> None:
        """
        sm_id: 指定状态机的ID
        clock_freq: 时钟频率(最小为2*sys_clk/65535)
        period: 周期[3,2^32-1]
        """
        self._sm = StateMachine(sm_id)
        self._sm.init(pwm_prog_example, clock_freq * 2, sideset_base=pin)
        if period < 3:
            raise ValueError("period must >=3")
        self._period = period
        self._duty = period // 2
        self._sm.put(period - 3)
        self._sm.exec("pull()")
        self._sm.exec("mov(isr, osr)")
        self._sm.put(self._duty - 2)
        self._sm.active(1)

    def duty_u16(self, value: int | None = None) -> int:
        """仅仅是为了兼容machine.PWM的接口，实际可控制占空比取决于period的设置"""
        if value is None:
            return self._duty
        value = self._period * value / 65535
        return self.duty(value)

    def duty(self, value: int | None = None) -> int:
        """设置 获取 脉宽周期(占空比)
        value: 脉宽周期 [1, period-2]
        """
        if value is None:
            return self._duty
        self._duty = max(1, min(value, self._period - 2))
        self._sm.put(self._duty - 2)
        return self._duty

    def freq(self):
        return 0
