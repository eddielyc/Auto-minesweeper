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
VERSION = "new"

LEVEL4_THESHOLD = 10
# LEVEL6 is always on
LEVEL6_THESHOLD1 = 10
LEVEL6_THESHOLD2 = 15

# LEVEL3 and LEVEL 5 are rubbish, DO NOT set them on.
LEVEL3_THESHOLD = -1
LEVEL5_THESHOLD = -1

CH_MAP = {
    "0": "0️⃣",
    "1": "1️⃣",
    "2": "2️⃣",
    "3": "3️⃣",
    "4": "4️⃣",
    "5": "5️⃣",
    "6": "6️⃣",
    "7": "7️⃣",
    "8": "8️⃣",
}
