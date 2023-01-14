# -*- coding: utf-8 -*-
# Time    : 2023/1/5 23:24
# Author  : Yichen Lu

import time

import minesweeper
from bot import Bot
from solver import Engine
from resolver import Resolver

from pynput.keyboard import Key, Controller as KController

keyboard = KController()

first_step = Engine.first_step()
context = minesweeper.initialize(first_step)
engine = Engine(context)
resolver = Resolver(context.front_side)

bot = Bot(context=context, resolver=resolver, engine=engine)

with keyboard.pressed(Key.alt):
    keyboard.press(Key.tab)

time.sleep(0.5)
try:
    bot.play_a_complete_game()
except:
    s = context.front_side.draw_board()
    print(s)

# while True:
#     try:
#         time.sleep(2)
#         bot.play_a_complete_game()
#     except KeyboardInterrupt:
#         break
#     except:
#         keyboard.press(Key.esc)
