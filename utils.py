# -*- coding: utf-8 -*-
# Time    : 2022/12/31 17:53
# Author  : Yichen Lu

from typing import Dict, Union, List, Tuple
import itertools
import math
from collections import defaultdict
from global_variables import *
import unicodedata
from pathlib import Path
import pickle
import time

biases = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]]


def iter_around(h, w, height=HEIGHT, width=WIDTH, around_type=None, context=None):
    """
    iter around single point
    :param h: h
    :param w: w
    :param height: height of minesweeper
    :param width: width of minesweeper
    :param around_type: limit type of points around
    :param context: interact.Context
    :return: positions around
    """
    for bias_h, bias_w in biases:
        around_h, around_w = h + bias_h, w + bias_w
        if 0 <= around_h < height and 0 <= around_w < width:
            if around_type is None or \
                    context.front_side.type(around_h, around_w) == around_type or \
                    context.back_side.type(around_h, around_w) == around_type:
                yield around_h, around_w


def iter_arounds(positions, height=HEIGHT, width=WIDTH, around_type=None, context=None, blocks=None):
    """
    iter around a group of points
    :param positions: position of such group of points
    :param height: height of minesweeper
    :param width: width of minesweeper
    :param around_type: type of around points
    :param context: interact.Context
    :param blocks: blocks
    :return: iter around a group of points
    """
    blocks = blocks if blocks else set()

    visited = set(positions)
    for h, w in positions:
        for bias_h, bias_w in biases:
            around_h, around_w = h + bias_h, w + bias_w
            if 0 <= around_h < height and 0 <= around_w < width and (around_h, around_w) not in visited:
                # check type of around points and whether is in blocks
                if (around_type is None or context.front_side.type(around_h, around_w) == around_type) \
                        and (around_h, around_w) not in blocks:
                    visited.add((around_h, around_w))
                    yield around_h, around_w


def is_mine(h, w, board):
    return board[h][w] == MINE


def get_ch_width(ch):
    return 2 if unicodedata.east_asian_width(ch) in ["A", "F", "W"] else 1


def fill_till_width(word, width, fill_ch=" "):
    word_width = sum([get_ch_width(ch) for ch in word])
    return fill_ch * (width - word_width) + word


def assign_probability(unseens, mines):
    if mines == 0:
        return 0.
    return math.comb(unseens - 1, mines - 1) / math.comb(unseens, mines)


def look_around(h, w, context, pseudo_context=None) -> Dict:
    """
    generate 1 hop tree
    :return: hop tree:
    #       "flags" -> positions of flags around
    #       "unseens" -> positions of unseens around
    #       "hints" -> hints of flags around
    #       "self" -> value of self (hint)
    #       "remains" -> number of remain mines
    """

    # if context.front_side.get(h, w) in [UNSEEN, FLAG]:
    #     raise RuntimeError

    around = defaultdict(list)
    for around_h, around_w in iter_around(h, w):
        element = context.front_side.get(around_h, around_w)
        if element == FLAG:
            around['flags'].append((around_h, around_w))
        elif element == UNSEEN:
            if pseudo_context and (around_h, around_w) in pseudo_context.pseudo_flags:
                around['flags'].append((around_h, around_w))
            elif pseudo_context and (around_h, around_w) in pseudo_context.pseudo_hints:
                around['hints'].append((around_h, around_w))
            else:
                around['unseens'].append((around_h, around_w))
        elif isinstance(element, int):
            around['hints'].append((around_h, around_w))
    around["self"] = context.front_side.get(h, w)
    if context.front_side.type(h, w) == "HINT":
        around["remains"] = context.front_side.get(h, w) - len(around['flags'])

    return around


def iter_incomplete_hints(context):
    for hint_h, hint_w in context.front_side.hints:
        around = look_around(hint_h, hint_w, context)
        if around["unseens"]:
            yield hint_h, hint_w


def entropy(distribution: Union[int, List]):
    if isinstance(distribution, int):
        assert distribution >= 1
        return math.log(distribution, base=math.e)
    assert 0.999 <= sum(distribution) <= 1.001
    return sum([-math.log(p, base=math.e) for p in distribution]) / len(distribution)


def information_gain(distribution_a: Union[int, List], distribution_b: Union[int, List]):
    """
    :param distribution_a: current distribution
    :param distribution_b: original distribution
    :return: information gain
    """
    return entropy(distribution_b) - entropy(distribution_a)
