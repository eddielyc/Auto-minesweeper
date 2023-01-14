# -*- coding: utf-8 -*-
# Time    : 2023/1/4 20:59
# Author  : Yichen Lu

import time
from resolver import *
from pynput.keyboard import Key, Controller as KController
from pynput.mouse import Button, Controller as MController

from minesweeper.board import FrontSide

mouse = MController()
keyboard = KController()

mouse.position = (0, 0)
with keyboard.pressed(Key.alt):
    keyboard.press(Key.tab)

time.sleep(1)

front_side = FrontSide(HEIGHT, WIDTH)
front_side.initialize()
resolver = Resolver(front_side)

resolver.resolve()


s = front_side.draw_board()
print(s)
