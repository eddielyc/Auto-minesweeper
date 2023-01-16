# Ref: https://github.com/ztxz16/Mine

import minesweeper
from bot import Bot
from solver import Engine
from global_variables import *

from typing import Iterable
import numpy as np
from PIL import ImageGrab
import win32api as api
import win32gui as gui
import win32con as con
import time
import os

cell = 16
map = {
    147: UNSEEN,
    215: "0",
    527: "1",
    722: "2",
    125: "3",
    452: "4",
    730: "5",
    377: "6",
    758: "7",
    346: "8",
    990: FLAG,
    668: MINE,
    749: MINE,
}


def getBoard(x0, y0, x1, y1):
    img = np.array(ImageGrab.grab((x0, y0, x1, y1)))
    m, n = (x1 - x0) // 16, (y1 - y0) // 16
    mine = 99
    if m == 9 and n == 9:
        mine = 10
    if m == 16 and n == 16:
        mine = 40
    board = [[-1 for i in range(m)] for j in range(n)]

    for i in range(n):
        for j in range(m):
            cur = img[i * cell: (i + 1) * cell, j * cell: (j + 1) * cell, 0: 1]
            s = np.sum(cur) % 999
            if s not in map:
                print(i, j, s)
                exit(0)
            else:
                board[i][j] = map[s]
    return board


def main():
    def execute_ops(ops):
        gui.SetForegroundWindow(handle)
        ops = ops if isinstance(ops, Iterable) else [ops]
        for op in ops:
            if op.op == "step":
                api.SetCursorPos((x0 + op.w * cell + 5, y0 + op.h * cell + 5))
                api.mouse_event(con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                api.mouse_event(con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                api.SetCursorPos((0, 0))
            elif op.op == "flag":
                api.SetCursorPos((x0 + op.w * cell + 5, y0 + op.h * cell + 5))
                api.mouse_event(con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                api.mouse_event(con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                api.SetCursorPos((0, 0))

    def restart():
        api.keybd_event(113, 0, 0, 0)
        api.keybd_event(113, 0, con.KEYEVENTF_KEYUP, 0)
        time.sleep(0.5)

    first_step = Engine.first_step()
    context = minesweeper.initialize(first_step)
    engine = Engine(context)

    handle = gui.FindWindow(None, "扫雷")
    gui.SetForegroundWindow(handle)

    x0, y0, x1, y1 = gui.GetWindowRect(handle)
    x0, y0 = x0 + 15, y0 + 101
    # x1, y1 = x1 - 10, y1 - 40

    cnt, win_cnt = 0, 0

    while True:
        cnt += 1
        first_step = Engine.first_step()
        execute_ops(first_step)
        while True:
            board = getBoard(x0, y0, x1, y1)
            context.front_side.board = board
            try:
                context.front_side.update_from_board()
            except RuntimeError:
                # appear mines and fail
                restart()
                print(f"CNT: {cnt}, WIN CNT: {win_cnt}, chance of winning: {(win_cnt / cnt):.4f}")
                break

            # no unseens remain and win
            if len(context.front_side.unseens) == 0:
                win_cnt += 1
                restart()
                print(f"CNT: {cnt}, WIN CNT: {win_cnt}, chance of winning: {(win_cnt / cnt):.4f}")
                break

            ops = engine.what_next(mode="most")
            execute_ops(ops)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
