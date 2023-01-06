# -*- coding: utf-8 -*-
# Time    : 2023/1/1 10:34
# Author  : Yichen Lu


from minesweeper.board import *
from minesweeper.interact import *
from global_variables import *


def initialize(first_step) -> interact.Context:
    front_side = board.FrontSide(HEIGHT, WIDTH)
    front_side.initialize()
    back_side = board.BackSide(HEIGHT, WIDTH, MINES)
    back_side.initialize(version=VERSION, first_step=first_step)
    context = interact.Context(front_side, back_side)
    context.interact(first_step)
    return context

