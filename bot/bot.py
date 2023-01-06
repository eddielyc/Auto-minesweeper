# -*- coding: utf-8 -*-
# Time    : 2023/1/5 22:06
# Author  : Yichen Lu

import time
from typing import Iterable, Union

from minesweeper import Context
from resolver import Resolver
from solver import Engine

from global_variables import *
from resolver.key_points import *
from minesweeper.board import FrontSide

from pynput.keyboard import Key, Controller as KController
from pynput.mouse import Button, Controller as MController


class Bot(object):
    def __init__(self, context: Context, resolver: Resolver, engine: Engine):
        self.context = context
        self.resolver = resolver
        self.engine = engine

        self.mouse = MController()
        self.keyboard = KController()

        self.front_side = FrontSide(HEIGHT, WIDTH)
        self.front_side.initialize()

        self.wait_time_between_ops = 0.05

    def play_a_complete_game(self):
        first_step = Engine.first_step()
        self.execute_ops(first_step)
        self.move_mouse_to_corner()

        signal = "OK"
        while signal == "OK":
            signal = self.interact()
        self.press_escape()

    def interact(self):
        self.move_mouse_to_corner()
        self.resolver.resolve()
        self.context.front_side.update_from_board()

        ops = self.engine.what_next(mode="most")
        signal = self.execute_ops(ops)

        if signal in ["WIN", "OVER"]:
            return signal

        return signal

    def execute_ops(self, ops):
        ops = ops if isinstance(ops, Iterable) else [ops]
        for op in ops:
            time.sleep(self.wait_time_between_ops)
            if op.op == "step":
                self.step(op.h, op.w)
            elif op.op == "flag":
                self.flag(op.h, op.w)
            else:
                raise ValueError(f"Invalid op type: {op.op}.")

        # Typically, guessing op would appear individually, so is_win_or_over() is called after all ops executed.
        signal = self.resolver.is_win_or_over()
        if signal in ["WIN", "OVER"]:
            return signal
        return "OK"

    def move_mouse_to_corner(self):
        self.mouse.position = (0, 0)

    def press_escape(self):
        self.keyboard.press(Key.esc)

    def switch_window(self):
        with self.keyboard.pressed(Key.alt):
            self.keyboard.press(Key.tab)

    def step(self, h, w):
        self.mouse.position = self.get_position(h, w)
        self.mouse.click(Button.left)

    def flag(self, h, w):
        self.mouse.position = self.get_position(h, w)
        self.mouse.click(Button.right)

    def get_position(self, h, w):
        x = round(LEFT + GRID_W * (w + 0.5))
        y = round(TOP + GRID_H * (h + 0.5))
        return x, y
