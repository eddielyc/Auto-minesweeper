# -*- coding: utf-8 -*-
# Time    : 2023/1/3 21:45
# Author  : Yichen Lu


# -*- coding: utf-8 -*-
# Time    : 2022/12/31 16:44
# Author  : Yichen Lu

import minesweeper
from solver import *


import minesweeper
from solver import *


cnt, win_cnt = 10000, 0

first_step = Engine.first_step()

for i in range(1, cnt + 1):
    context = minesweeper.initialize(first_step)
    engine = Engine(context)

    chance_of_winning = (win_cnt / (i - 1)) if i > 1 else 0.
    print(f"TOTAL: {cnt}, CNT: {i}, WIN CNT: {win_cnt}, chance of winning: {chance_of_winning:.4f}")

    # TODO
    ops_cnt = 0
    while not context.is_over and not context.is_win:
        try:
            ops = engine.what_next()
        except:
            engine.hold_on()

        ops_cnt += len(ops) if isinstance(ops, list) else 1
        if ops_cnt > 480:
            engine.hold_on()
        context.interact(ops)

    if context.is_win:
        win_cnt += 1


print(f"CNT: {cnt}, WIN CNT: {win_cnt}, chance of winning: {(win_cnt / cnt):.4f}")
