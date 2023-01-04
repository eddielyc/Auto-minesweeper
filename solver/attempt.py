# -*- coding: utf-8 -*-
# Time    : 2023/1/3 10:58
# Author  : Yichen Lu


class Attempt(object):
    def __init__(self, h, w, pseudo_flags, pseudo_hints):
        self.h, self.w = h, w
        self.pseudo_flags = pseudo_flags
        self.pseudo_hints = pseudo_hints
