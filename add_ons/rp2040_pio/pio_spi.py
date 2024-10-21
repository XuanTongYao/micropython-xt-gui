from rp2 import *
from machine import Pin, SPI
import utime


def spi_program_generator(phase, polarity, mosi, miso):
    side_default = PIO.OUT_LOW if polarity == 0 else PIO.OUT_HIGH
    autopull = False if mosi is None else True
    if phase == 0:

        @asm_pio(
            sideset_init=side_default,
            out_init=PIO.OUT_LOW,
            autopull=autopull,
            autopush=False,
        )
        def spi_cpha0():
            out(pins, 1).side(polarity)
            in_(pins, 1).side(not polarity)

        return spi_cpha0

    else:

        @asm_pio(
            sideset_init=side_default,
            out_init=PIO.OUT_LOW,
            autopull=autopull,
            autopush=False,
        )
        def spi_cpha1():
            out(x, 1).side(polarity)
            mov(pins, x).side(not polarity)[1]
            in_(pins, 1).side(polarity)

        return spi_cpha1


class PIO_SPI:
    MSB = 1
    LSB = 0

    def __init__(
        self,
        sck: Pin,
        mosi: Pin | None = None,
        miso: Pin | None = None,
        baudrate=2_000,
        phase=0,
        polarity=0,
        firstbit=MSB,
        sm_id=0,
    ) -> None:
        """
        sm_id: 指定状态机的ID
        """
        self._sm = StateMachine(sm_id)
        self._sm.init(
            spi_program_generator(phase, polarity, mosi, miso),
            baudrate * 2 if phase == 0 else baudrate * 4,
            out_base=mosi,
            in_base=miso,
            sideset_base=sck,
            pull_thresh=8,
            out_shiftdir=PIO.SHIFT_LEFT if firstbit == PIO_SPI.MSB else PIO.SHIFT_RIGHT,
        )
        self._sm.active(1)

    def write(self, data: bytes) -> None:
        self._sm.put(data, 24)

    def read(self, length: int, write=0x00) -> bytes:
        tmp = bytearray()

        # 清空RX FIFO
        self._sm.exec("push(noblock)")
        self._sm.get()
        for _ in range(length):
            self._sm.put(write)
            self._sm.exec("push(noblock)")
            tmp.append(self._sm.get())

        return tmp

    def readinto(self, buf: bytearray, write=0x00) -> None:
        # 清空RX FIFO
        self._sm.exec("push(noblock)")
        self._sm.get()
        for i in range(len(buf)):
            self._sm.put(write)
            self._sm.exec("push(noblock)")
            buf[i] = self._sm.get()
