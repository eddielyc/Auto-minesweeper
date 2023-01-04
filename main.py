# -*- coding: utf-8 -*-
# Time    : 2022/12/31 16:44
# Author  : Yichen Lu

import game
from solver import *


cnt, win_cnt = 100, 0

first_step = Engine.first_step()

for i in range(1, cnt + 1):
    context = game.initialize(first_step)
    context.draw(hide_back_side=False)

    engine = Engine(context)

    while not context.is_over and not context.is_win:
        # h, w, op = input("\nCommand:").strip().split()
        # h, w = int(h), int(w)
        # ops = interact.Operation(h, w, op)

        ops = engine.what_next()
        context.interact(ops)
        chance_of_winning = (win_cnt / (i - 1)) if i > 1 else 0.
        context.draw(hide_back_side=False, prefix=f"TOTAL: {cnt}, CNT: {i}, WIN CNT: {win_cnt}, chance of winning: {chance_of_winning:.4f}")
    if context.is_win:
        win_cnt += 1

print(f"CNT: {cnt}, WIN CNT: {win_cnt}, chance of winning: {(win_cnt / cnt):.4f}")
