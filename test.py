# -*- coding: utf-8 -*-
# Time    : 2023/1/3 13:43
# Author  : Yichen Lu


import minesweeper
from solver import *
from resolver import *

first_step = Engine.first_step()
context = minesweeper.initialize(first_step)
# context.load()
# context.draw(hide_back_side=False)

resolver = Resolver(context.front_side)

engine = Engine(context)
resolver.resolve()
context.front_side.update_from_board()
ops = engine.what_next(mode="most")
pass
