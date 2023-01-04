# -*- coding: utf-8 -*-
# Time    : 2023/1/3 13:43
# Author  : Yichen Lu


import game
from solver import *

first_step = Engine.first_step()
context = game.initialize(first_step)
context.load()
context.draw(hide_back_side=False)

engine = Engine(context)

while True:
    if context.is_over or context.is_win:
        break

    # h, w, op = input("\nCommand:").strip().split()
    # h, w = int(h), int(w)
    # ops = interact.Operation(h, w, op)

    conclusion = engine.inference(level=4)
    ops = engine.what_next()
    context.interact(ops)
    context.draw(hide_back_side=False)
    pass
