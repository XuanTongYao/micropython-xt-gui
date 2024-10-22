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


def rgb565trans_to_gbr565mat(data: bytearray):
    tmp = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3))
    for row in range(DISPLAY_HEIGHT):
        row_data = data[row * ROW_SIZE : row * ROW_SIZE + ROW_SIZE]
        px_data = struct.unpack(">" + "H" * DISPLAY_WIDTH, row_data)
        for col, px in enumerate(px_data):
            r, g, b = separate_rgb565(px)
            tmp[row, col] = b, g, r
    return tmp


# snapshots will be saved to ./snapshots_png in PNG format
snapshots = os.listdir("./snapshots")
for snapshot in snapshots:
    with open(f"./snapshots/{snapshot}", "rb") as f:
        data = f.read()
        img = rgb565trans_to_gbr565mat(bytearray(data))
        cv2.imwrite(f"./snapshots_png/{snapshot}.png", img * 255)


cv2.imshow(snapshot, img)
cv2.waitKey(0)
