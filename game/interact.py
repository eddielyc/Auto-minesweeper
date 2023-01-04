# -*- coding: utf-8 -*-
# Time    : 2023/1/1 10:34
# Author  : Yichen Lu

import os
import time
import pickle
from pathlib import Path
import utils
from typing import Union, List
from game import FrontSide, BackSide
from global_variables import *
from collections import deque


class Operation(object):
    def __init__(self, h, w, op):
        self.h = h
        self.w = w
        self.op = op


class Context(object):
    def __init__(self, front_side: FrontSide, back_side: BackSide, is_draw=True):
        self.front_side = front_side
        self.back_side = back_side
        self.is_over = False
        self.is_win = False
        self.is_draw = is_draw

    def draw(self, hide_back_side=True, prefix=None):
        front_side_s = self.front_side.draw_board()
        back_side_s = self.back_side.draw_board()

        os.system('cls' if os.name == 'nt' else 'clear')
        if prefix:
            print(prefix)
        if not self.is_draw:
            return

        print(f"Front Side:  REMAINS: {self.front_side.remains}")
        print(front_side_s)
        if not hide_back_side:
            print()
            print("Back Side: ")
            print(back_side_s)
        if self.is_over:
            print("BOOM")
        elif self.is_win:
            print("Congratulations!")

    def interact(self, ops: Union[Operation, List]):
        ops = ops if isinstance(ops, list) else [ops]
        for op in ops:
            if op.op == "step":
                signal = self.step(op.h, op.w)
            elif op.op == "flag":
                signal = self.flag(op.h, op.w)
            else:
                raise ValueError(f"Invalid op type: {op.op}.")

            if signal == "BOOM":
                self.is_over = True
                return "BOOM"
            elif signal == "WIN":
                self.is_win = True
                return "WIN"

    def uncover(self, h, w):
        self.front_side.set(h, w, self.back_side.get(h, w))
        self.front_side.unseens.discard((h, w))
        self.front_side.hints.add((h, w))

    def step(self, h, w):
        if self.front_side.get(h, w) != UNSEEN:
            return "OK"
        elif self.back_side.get(h, w) == MINE:
            self.uncover(h, w)
            return "BOOM"
        else:
            self.step_bfs(h, w)
            if self.front_side.remains == len(self.front_side.unseens) or self.front_side.remains == 0:
                return "WIN"
            return "OK"

    def step_bfs(self, h, w):
        queue = deque([(h, w)])
        while queue:
            h, w = queue.popleft()
            if self.back_side.get(h, w) == MINE:
                raise RuntimeError
            elif self.back_side.get(h, w) == 0:
                self.uncover(h, w)
                for around_h, around_w in utils.iter_around(h, w, self.back_side.height, self.back_side.width):
                    if self.front_side.get(around_h, around_w) == UNSEEN:
                        queue.append((around_h, around_w))
            else:
                self.uncover(h, w)

    def flag(self, h, w):
        if self.front_side.get(h, w) == UNSEEN:
            self.front_side.set(h, w, FLAG)
            self.front_side.unseens.remove((h, w))
            self.front_side.flags.add((h, w))

            return "OK"
        elif self.front_side.get(h, w) == FLAG:
            self.front_side.set(h, w, UNSEEN)
            self.front_side.unseens.add((h, w))
            self.front_side.flags.remove((h, w))
            return "OK"
        else:
            return "OK"

    def save(self):
        y, m, d, h, M, s, *_ = time.localtime(time.time())
        now = '-'.join([f"{y}", f"{m:02d}", f"{d:02d}", f"{h:02d}", f"{M:02d}", f"{s:02d}"])
        path = Path("checkpoints") / (now + ".pkl")
        with open(path, 'wb') as file:
            pickle.dump(
                {
                    "front_side": self.front_side,
                    "back_side": self.back_side,
                    "is_over": self.is_over,
                    "is_win": self.is_win,
                    "is_draw": self.is_draw,
                }, file
            )
        print(f"Save context to {path}.")

    def load(self, path=None):
        if path is None:
            # latest
            path = sorted(list(Path("checkpoints").iterdir()))[-1]
        with open(path, 'rb') as file:
            ckpt = pickle.load(file)
        self.front_side = ckpt["front_side"]
        self.back_side = ckpt["back_side"]
        self.is_over = ckpt["is_over"]
        self.is_win = ckpt["is_win"]
        self.is_draw = ckpt["is_draw"]
        print(f"Load ckpt from {path}.")
