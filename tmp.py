# -*- coding: utf-8 -*-
# Time    : 2022/12/31 16:44
# Author  : Yichen Lu

import msvcrt

# while True:
#     command = msvcrt.getch()

#     print(type(command), command)

from PIL import Image, ImageGrab
from pathlib import Path
import numpy as np
from resolver.key_points import *
from minesweeper import *


# image = Image.open("src/1.png").convert("RGB")
# image.save("tmp.png")
#
# image = Image.fromarray(np.array(Image.open("src/1.png"), dtype=np.uint8)[..., : 3])
# image.save("tmp.png")

# image = Image.fromarray(np.array(Image.open("src/backup/unseen.png"), dtype=np.uint8)).resize((48, 48))
# image.save("tmp.png")

a = Operation(1, 1, "flag")
print(hash(a))
b = Operation(1, 1, "flag")
print(hash(b))

s = set([a])
s.add(b)
print(s)
