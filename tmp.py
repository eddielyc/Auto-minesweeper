# -*- coding: utf-8 -*-
# Time    : 2022/12/31 16:44
# Author  : Yichen Lu

import msvcrt

# while True:
#     command = msvcrt.getch()

#     print(type(command), command)


import time
tmp = 2
y, m, d, h, m, s, *_ = time.localtime(time.time())
