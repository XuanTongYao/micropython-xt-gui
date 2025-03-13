import cv2
import numpy as np
import os
import struct


DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 240
ROW_SIZE = DISPLAY_WIDTH * 2


def separate_rgb565(rgb565: int, big_endian=False) -> tuple[int, int, int]:
    if big_endian:
        rgb565 = (rgb565 & 0xFF00) >> 8 | (rgb565 & 0x00FF) << 8
    r5 = rgb565 >> 11
    g6 = (rgb565 & 0x07E0) >> 5
    b5 = rgb565 & 0x001F
    return (r5, g6, b5)


def rgb565_to_bgr888(rgb565: int) -> tuple[int, int, int]:
    r5, g6, b5 = separate_rgb565(rgb565)
    # 将5/6位扩展到8位（保留精度）
    r8 = (r5 << 3) | (r5 >> 2)  # R5 -> R8
    g8 = (g6 << 2) | (g6 >> 4)  # G6 -> G8
    b8 = (b5 << 3) | (b5 >> 2)  # B5 -> B8
    # OpenCV使用BGR格式，因此返回 (B, G, R)
    return (b8, g8, r8)


def rgb565trans_to_bgr888mat(data: bytearray):
    tmp = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8)
    for row in range(DISPLAY_HEIGHT):
        row_data = data[row * ROW_SIZE : row * ROW_SIZE + ROW_SIZE]
        px_data = struct.unpack(f">{DISPLAY_WIDTH}H", row_data)
        for col, px in enumerate(px_data):
            tmp[row, col] = rgb565_to_bgr888(px)
    return tmp


# snapshots will be saved to ./snapshots_png in PNG format
snapshots = os.listdir("./snapshots")
for snapshot in snapshots:
    with open(f"./snapshots/{snapshot}", "rb") as f:
        data = f.read()
        img = rgb565trans_to_bgr888mat(bytearray(data))
        cv2.imwrite(f"./snapshots_png/{snapshot}.png", img)


cv2.imshow(snapshot, img)
cv2.waitKey(0)
