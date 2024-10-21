import gc
import io
import winsound
from math import ceil
import time


# PC专用
def const(x):
    return x


# PC专用


def genarate_note_freq():
    standard_frequency = 440.0
    noteFrequency = [
        round((standard_frequency / 32.0) * pow(2, (i - 9) / 12)) for i in range(128)
    ]
    return tuple(noteFrequency)


NOTE_FREQ_TABLE = (
    8,
    9,
    9,
    10,
    10,
    11,
    12,
    12,
    13,
    14,
    15,
    15,
    16,
    17,
    18,
    19,
    21,
    22,
    23,
    24,
    26,
    28,
    29,
    31,
    33,
    35,
    37,
    39,
    41,
    44,
    46,
    49,
    52,
    55,
    58,
    62,
    65,
    69,
    73,
    78,
    82,
    87,
    92,
    98,
    104,
    110,
    117,
    123,
    131,
    139,
    147,
    156,
    165,
    175,
    185,
    196,
    208,
    220,
    233,
    247,
    262,
    277,
    294,
    311,
    330,
    349,
    370,
    392,
    415,
    440,
    466,
    494,
    523,
    554,
    587,
    622,
    659,
    698,
    740,
    784,
    831,
    880,
    932,
    988,
    1047,
    1109,
    1175,
    1245,
    1319,
    1397,
    1480,
    1568,
    1661,
    1760,
    1865,
    1976,
    2093,
    2217,
    2349,
    2489,
    2637,
    2794,
    2960,
    3136,
    3322,
    3520,
    3729,
    3951,
    4186,
    4435,
    4699,
    4978,
    5274,
    5588,
    5920,
    6272,
    6645,
    7040,
    7459,
    7902,
    8372,
    8870,
    9397,
    9956,
    10548,
    11175,
    11840,
    12544,
)


def variable_length_quantity(stream: io.BytesIO | io.BufferedReader):
    vlq = 0
    while True:
        byte = stream.read(1)[0]
        vlq = (vlq << 7) | (byte & 0x7F)
        if byte & 0x80 == 0:
            break
    return vlq


class MIDI:

    SINGLE_TRACK = const(0)
    MULTI_TRACK = const(1)
    SEQUENTIAL_MULTI_TRACK = const(2)

    def __init__(self, data_file: bytes | str) -> None:
        gc.collect()
        if isinstance(data_file, str):
            self.midi = midi = open(data_file, "rb")
        else:
            self.midi = midi = io.BytesIO(data_file)
        del data_file
        gc.collect()
        if midi.read(8) != b"MThd\x00\x00\x00\x06":
            raise ValueError("Invalid MIDI file")
        self.type = int.from_bytes(midi.read(2), "big")
        self.ntrks = int.from_bytes(midi.read(2), "big")
        if self.type == MIDI.SINGLE_TRACK and self.ntrks != 1:
            raise ValueError("Invalid ntrks")
        self.division = int.from_bytes(midi.read(2), "big")
        if self.division & 0x8000:
            self.time_format = 1
        else:
            self.time_format = 0
            self.ticks_per_quarter = self.division & 0x7FFF

        # 读取轨道数据
        # self._decode_track()

    def _decode_track(self):
        midi = self.midi
        midi.seek(14, 0)
        while True:
            chunk_type = midi.read(4)
            if chunk_type == b"":
                break

            chunk_len = int.from_bytes(midi.read(4), "big")
            if chunk_type != b"MTrk":
                midi.seek(chunk_len, 1)
                continue

            # 解析多个MTrk事件
            chunk_data = io.BytesIO(midi.read(chunk_len))
            while True:
                test = chunk_data.read(1)
                if test == b"":
                    break
                else:
                    chunk_data.seek(-1, 1)
                delta_time = variable_length_quantity(chunk_data)
                self._parse_event(delta_time, chunk_data)

    def _parse_event(self, delta_time, stream: io.BytesIO | io.BufferedReader):
        """返回读取的字节数"""
        midi = stream
        event_type = midi.read(1)
        if event_type == b"\xFF":
            midi.read(1)
            len_ = variable_length_quantity(midi)
            midi.seek(len_, 1)
        elif event_type == b"\xF0" or event_type == b"\xF7":
            len_ = variable_length_quantity(midi)
            midi.seek(len_, 1)
        else:
            midi.seek(-1, 1)
            self._parse_midi_message(stream)

    def _parse_midi_message(self, stream: io.BytesIO | io.BufferedReader):
        midi = stream
        status_or_data = midi.read(1)[0]
        if status_or_data & 0x80:
            self.runing_status = status = status_or_data
            data_0 = midi.read(1)
        else:
            status = self.runing_status
            data_0 = bytes((status_or_data))

        if status & 0xF0 == 0xF0:
            # 系统消息
            pass
        else:
            # 通道消息
            if status & 0xF0 in (0b1100_0000, 0b1101_0000):
                self._channel_message(status, data_0)
            else:
                self._channel_message(status, data_0 + midi.read(1))

    def _channel_message(self, status: int, data: bytes):
        ch = status & 0x0F
        message_type = status & 0xF0
        match (message_type):
            case 0b1000_0000:
                pass
            case 0b1001_0000:
                pitch = data[0]
                velocity = data[1]
                self.note_on(pitch, velocity)
            case 0b1010_0000:
                pass
            case 0b1011_0000:
                pass
            case 0b1100_0000:
                # 更改乐器类型
                self.instrument = data[0]
            case 0b1101_0000:
                pass
            case 0b1110_0000:
                pass

    def _system_message(self, status: int, data: bytes):
        pass

    def note_on(self, key, velocity):
        winsound.Beep(NOTE_FREQ_TABLE[key], 50)

    def note_off(self, key, velocity):
        pass

    def play_sync(self):
        """阻塞播放"""
        self._decode_track()

    def play_async(self):
        """异步(非阻塞)播放"""
        pass

    def stop(self):
        pass


gc.collect()


K = MIDI("./add_ons/Wiz Khalifa ft. Charlie Puth - See You Again.mid.mid")
K.play_sync()
