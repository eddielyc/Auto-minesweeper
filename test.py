# -*- coding: utf-8 -*-
# Time    : 2023/1/3 13:43
# Author  : Yichen Lu
import time

import minesweeper
from solver import *
from resolver import *

from pynput.keyboard import Key, Controller as KController
from pynput.mouse import Button, Controller as MController


first_step = Engine.first_step()
context = minesweeper.initialize(first_step)

# context.front_side.board = [
#     [UNSEEN, UNSEEN, UNSEEN, UNSEEN, UNSEEN, UNSEEN, UNSEEN],
#     [UNSEEN, FLAG, "3", "2", FLAG, FLAG, FLAG],
#     [UNSEEN, FLAG, "3", "2", "3", "4", UNSEEN],
#     [UNSEEN, UNSEEN, UNSEEN, UNSEEN, UNSEEN, UNSEEN, UNSEEN]
# ]
#
# context.front_side.update_from_board()
# s = context.front_side.draw_board(lambda x: {UNSEEN: "[ ]", FLAG: "P"}.get(x, x))
# print(s)

# context.load(path="checkpoints/2023-01-17-16-53-51.pkl")
context.load()
s = context.front_side.draw_board(lambda x: {UNSEEN: "[ ]", FLAG: "P"}.get(x, x))
# s = context.front_side.draw_board()
print(s)

# resolver = Resolver(context.front_side)
engine = Engine(context)

# mouse = MController()
# keyboard = KController()

# mouse.position = (0, 0)
# with keyboard.pressed(Key.alt):
#     keyboard.press(Key.tab)

# time.sleep(1)

# resolver.resolve()

ops = engine.what_next(mode="least")
print(ops)


# num_clear_tiles = engine.num_clear_tiles_if_hw_is_safe(14, 16)
# print(num_clear_tiles)
pass
