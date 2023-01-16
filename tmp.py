# -*- coding: utf-8 -*-
# Time    : 2022/12/31 16:44
# Author  : Yichen Lu

from time import time

start = time()
for i in range(10000000):
    time()
print(f"{time() - start}")
