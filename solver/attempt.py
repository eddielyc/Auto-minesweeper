# -*- coding: utf-8 -*-
# Time    : 2023/1/3 10:58
# Author  : Yichen Lu


class Attempt(object):
    def __init__(self, h, w, pseudo_flags, pseudo_hints):
        self.h, self.w = h, w
        self.pseudo_flags = pseudo_flags
        self.pseudo_hints = pseudo_hints

    def __hash__(self):
        info = (self.h, self.w) + \
               tuple(sorted(list(self.pseudo_flags))) + \
               tuple(sorted(list(self.pseudo_hints)))
        return hash(info)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return RuntimeError
        return hash(self) == hash(other)
