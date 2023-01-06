# -*- coding: utf-8 -*-
# Time    : 2023/1/1 10:37
# Author  : Yichen Lu

import os
import random
import utils
from global_variables import *


class Board(object):
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.board = [[None for _ in range(self.width)] for _ in range(self.height)]

    def initialize(self):
        raise NotImplementedError

    def get(self, h, w):
        return self.board[h][w] if self.board[h][w] in [UNSEEN, MINE, FLAG] else int(self.board[h][w])

    def type(self, h, w):
        return self.get(h, w) if self.get(h, w) in [UNSEEN, MINE, FLAG] else "HINT"

    def draw_board(self, ch_mapping=lambda x: x) -> str:
        head = [" " * TAB_SIZE, "|", *[utils.fill_till_width(str(w), TAB_SIZE) for w in range(WIDTH)]]
        line = ["-" * TAB_SIZE, "|", *["-" * TAB_SIZE for _ in range(WIDTH)]]

        rows = [head, line]
        for h, row in enumerate(self.board):
            rows.append([" " * (TAB_SIZE - len(str(h))) + str(h), "|",
                         *[utils.fill_till_width(ch_mapping(ele), TAB_SIZE) for ele in row]])
        rows = ["".join(row) for row in rows]
        s = "\n".join(rows)

        return s


class FrontSide(Board):
    def __init__(self, height, width):
        super().__init__(height, width)

        self.hints = None
        self.unseens = None
        self.flags = None

    def initialize(self):
        self.board = [[UNSEEN for w in range(self.width)] for h in range(self.height)]
        self.hints = set()
        self.unseens = set([(h, w) for h in range(self.height) for w in range(self.width)])
        self.flags = set()

    def set(self, h, w, value):
        self.board[h][w] = str(value)

    @property
    def remains(self):
        return MINES - len(self.flags)

    def update_from_board(self):
        """
        In context, front side is updated by context instance, and in bot environment, back side is unknown. Thus,
        front side information must be updated with its board by itself.
        """
        self.hints, self.unseens, self.flags = set(), set(), set()

        for h in range(self.height):
            for w in range(self.width):
                if self.type(h, w) == "HINT":
                    self.hints.add((h, w))
                elif self.type(h, w) == FLAG:
                    self.flags.add((h, w))
                elif self.type(h, w) == UNSEEN:
                    self.unseens.add((h, w))
                else:
                    raise RuntimeError


class BackSide(Board):
    def __init__(self, height, width, mines):
        super().__init__(height, width)

        self.mines = mines
        self.mine_positions = None

    def init_mines(self, mines=None, first_step=None, version="old"):
        assert version in ["old", "new"]
        mines = mines or self.mines
        possible_positions = {(h, w) for h in range(self.height) for w in range(self.width)}
        possible_positions.remove((first_step.h, first_step.w))
        if version == "new":
            for step_around in utils.iter_around(first_step.h, first_step.w):
                possible_positions.remove(step_around)
        assert len(possible_positions) >= mines, f"Board is too small to contain {mines} mines."
        mine_positions = random.sample(possible_positions, mines)
        for h, w in mine_positions:
            self.board[h][w] = MINE
        return mine_positions

    def init_hints(self):
        for h in range(self.height):
            for w in range(self.width):
                if self.board[h][w] != MINE:
                    self.board[h][w] = str(sum(utils.is_mine(around_h, around_w, self.board)
                                           for around_h, around_w in utils.iter_around(h, w, self.height, self.width)))
        return self.board

    def initialize(self, version="old", first_step=None):
        assert version in ["old", "new"]
        self.board = [[None for w in range(self.width)] for h in range(self.height)]

        self.mine_positions = self.init_mines(first_step=first_step, version=version)
        self.board = self.init_hints()
