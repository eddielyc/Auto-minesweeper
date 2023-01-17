# -*- coding: utf-8 -*-
# Time    : 2022/12/31 18:02
# Author  : Yichen Lu


HEIGHT, WIDTH = 16, 30
MINES = 99
# HEIGHT, WIDTH = 4, 7
# MINES = 9

UNSEEN = "🟦"
FLAG = "🚩"
MINE = "💀"
TAB_SIZE = 3
# In old version, first step is safe for sure, but it may not be "0".
# And in new version, first step is safe for sure and it must be "0".
VERSION = "new"

# When remaining mines are less than LEVEL3_THESHOLD, level 3 (multiple hop and consider remaining mines) is on.
# LEVEL3_THESHOLD = 10
# The longest time (10 seconds for default) allowed in dfs function in LEVEL3 inference, when time runs out, dfs will be terminated.
LEVEL3_THESHOLD = 10
# The longest time (10 seconds for default) allowed in dfs function in LEVEL4 inference, when time runs out, dfs will be terminated.
LEVEL4_THESHOLD = 10
