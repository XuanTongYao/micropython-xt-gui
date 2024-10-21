"""
蜂鸣器声卡驱动
"""

import machine
import asyncio
from math import ceil
import math
import array
from gui.key_handler import KeyHandler

# 状态机常量
_PAUSED = const(0)
_PLAYING = const(1)


class BuzzerMedia:
    """基于定时器的蜂鸣器驱动"""

    def __init__(
        self,
        pwm_device: machine.PWM,
        timer_id: int = 0,
        sample_rate=20_000,
        buffer_size=512,
        resolution: int = 8,
    ) -> None:
        """
        sample_rate: 音频采样率，同时也决定delta
        buffer_size: 缓冲区大小(样本数量)
        resolution: 样本分辨率(电平量化位深度) !!! 不满1字节的部分会被对齐到字节(填充0)
        """
        if sample_rate > 22_050:
            raise ValueError("sample_rate must be less than 22_050")
        self.pwm_device = pwm_device
        pwm_device.duty_u16(0)
        pwm_device.freq(2 * sample_rate)
        self.sample_rate(sample_rate)
        self._buffer_size = buffer_size
        if resolution > 32:
            raise ValueError("resolution must be less than 32")
        elif resolution > 16:
            self.buffer = array.array("L", [0 for _ in range(buffer_size)])
        elif resolution > 8:
            self.buffer = array.array("I", [0 for _ in range(buffer_size)])
        else:
            self.buffer = array.array("B", [0 for _ in range(buffer_size)])
        self.__buffer_empty = True

        self._sample_index = 0
        # self._sample_size = ceil(resolution / 8)
        self._resolution = resolution
        self._volume = 100
        self.__base_volume = (2**resolution) - 1
        self.__fsm = _PAUSED
        self._play_timer = machine.Timer(timer_id)
        self._play_timer.init(freq=sample_rate, callback=self.__play_callback)

    def sample_rate(self, sample_rate: int | None = None):
        if sample_rate is None:
            return self._sample_rate
        self._sample_rate = sample_rate
        self._play_timer.init(freq=sample_rate, callback=self.__play_callback)

    def volume(self, volume: int | None):
        if volume is None:
            return self._volume
        self._volume = min(100, max(0, volume))

    def freq(self, freq: int | None):
        if freq is None:
            return self.pwm_device.freq()
        self.pwm_device.freq(freq)

    def refresh_buffer(self, data: array.array):
        if len(data) > self._buffer_size:
            self.buffer[:] = data[: self._buffer_size]
        else:
            self.buffer[: len(data)] = data
        self.__buffer_empty = False

    def buffer_is_empty(self):
        return self.__buffer_empty

    def __play_callback(self, _):
        if self.__fsm != _PLAYING or self.__buffer_empty:
            return
        self._play_sample(self.buffer[self._sample_index])
        self._sample_index += 1
        if self._sample_index == len(self.buffer):
            self._sample_index = 0
            self.__buffer_empty = True

    def play(self):
        self.__fsm = _PLAYING

    def pause(self):
        self.__fsm = _PAUSED
        self.pwm_device.duty_u16(0)

    def play_pause(self):
        if self.__fsm == _PAUSED:
            self.play()
        else:
            self.pause()

    def stop_and_close(self):
        self.pwm_device.duty_u16(0)
        self._play_timer.deinit()

    def _play_sample(self, sample: int):
        inverse_normalized_volume = (self.__base_volume // sample) * (
            100 // self._volume
        )
        self.pwm_device.duty_u16(65535 // inverse_normalized_volume)


class BuzzerMediaAsync:
    """基于异步的蜂鸣器驱动(最大采样率1000hz)"""

    def __init__(
        self,
        pwm_device: machine.PWM,
        sample_rate=1000,
        buffer_size=512,
        resolution: int = 8,
    ) -> None:
        """
        sample_rate: 音频采样率，同时也决定delta
        buffer_size: 缓冲区大小(样本数量)
        resolution: 样本分辨率(电平量化位深度) !!! 不满1字节的部分会被对齐到字节(填充0)
        """
        if sample_rate > 1000:
            raise ValueError("sample_rate must be less than 1000")
        self.pwm_device = pwm_device
        pwm_device.duty_u16(0)
        pwm_device.freq(2 * sample_rate)
        self.sample_rate(sample_rate)
        self._buffer_size = buffer_size
        if resolution > 32:
            raise ValueError("resolution must be less than 32")
        elif resolution > 16:
            self.buffer = array.array("L", [0 for _ in range(buffer_size)])
        elif resolution > 8:
            self.buffer = array.array("I", [0 for _ in range(buffer_size)])
        else:
            self.buffer = array.array("B", [0 for _ in range(buffer_size)])
        self.__buffer_empty = True

        # self._sample_ptr = 0
        # self._sample_size = ceil(resolution / 8)
        self._resolution = resolution
        self._volume = 100
        self.__base_volume = (2**resolution) - 1
        self.__fsm = _PAUSED
        self._play_task = None

    def sample_rate(self, sample_rate: int | None = None):
        if sample_rate is None:
            return self._sample_rate
        self._sample_rate = sample_rate
        self._delta_ms = 1000 // sample_rate

    def volume(self, volume: int | None):
        if volume is None:
            return self._volume
        self._volume = min(100, max(0, volume))

    def freq(self, freq: int | None):
        if freq is None:
            return self.pwm_device.freq()
        self.pwm_device.freq(freq)

    def refresh_buffer(self, data: array.array):
        if len(data) > self._buffer_size:
            self.buffer[:] = data[: self._buffer_size]
        else:
            self.buffer[: len(data)] = data
        self.__buffer_empty = False

    def buffer_is_empty(self):
        return self.__buffer_empty

    async def __do_play_loop(self):
        while True:
            if self.__fsm != _PLAYING or self.__buffer_empty:
                await asyncio.sleep(0)
                continue
            for sample in self.buffer:
                self._play_sample(sample)
                await asyncio.sleep_ms(self._delta_ms)  # type: ignore
                if self.__fsm == _PAUSED:
                    while True:
                        if self.__fsm != _PAUSED:
                            break
                        await asyncio.sleep(0)
            self.__buffer_empty = True
            await asyncio.sleep(0)

    def play(self):
        self.__fsm = _PLAYING

    def pause(self):
        self.__fsm = _PAUSED
        self.pwm_device.duty_u16(0)

    def play_pause(self):
        if self.__fsm == _PAUSED:
            self.play()
        else:
            self.pause()

    def stop_and_close(self):
        self.pwm_device.duty_u16(0)
        if self._play_task is not None:
            self._play_task.cancel()

    def __call__(self):
        if self._play_task is None:
            self._play_task = asyncio.create_task(self.__do_play_loop())
            return self._play_task
        elif self._play_task.cancelled():
            self._play_task = asyncio.create_task(self.__do_play_loop())
            return self._play_task
        else:
            print("task already exists")

    def _play_sample(self, sample: int):
        inverse_normalized_volume = (self.__base_volume // sample) * (
            100 // self._volume
        )
        self.pwm_device.duty_u16(65535 // inverse_normalized_volume)


async def main():
    a = BuzzerMediaAsync(machine.PWM(machine.Pin(4)), sample_rate=50, buffer_size=500)
    sin_wave = array.array(
        "B", [math.ceil(255 * abs(math.sin(x / 10))) for x in range(500)]
    )
    zigzag_wave = array.array("B", [math.ceil((x * 2) % 255) for x in range(500)])
    tri_wave = array.array("B", [abs((x * 4 % (255 * 2)) - 255) for x in range(500)])
    a()
    a.play()
    print("启动")
    pause_key = KeyHandler(machine.Pin(5, machine.Pin.IN))
    pause_key.set_press_func(lambda _, x=a.play_pause: x())
    pause_key()
    while True:
        if a.buffer_is_empty():
            a.refresh_buffer(tri_wave)
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())
