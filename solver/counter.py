# -*- coding: utf-8 -*-
# Time    : 2023/1/3 13:32
# Author  : Yichen Lu

import math
from itertools import chain
from collections import defaultdict


class Counter(object):
    """
    counter: position -> [times of flag, times of relevant]
    """
    def __init__(self, mode="shallow"):
        assert mode in ["shallow", "deep"]
        self.mode = mode
        self.cnt = 0
        self.position_cnt = dict()
        self.pseudo_contexts = dict()

    def update(self, pseudo_context, consider_remains=False, context=None):
        """
        update the valid assumption
        :param pseudo_context: could be an attempt or pseudo context
        :param consider_remains: whether considering number of remaining mines
        :param context: context if consider_remains is True
        :return: None
        """
        assert not consider_remains or (consider_remains and context)

        self.cnt += 1
        if self.mode == "shallow":
            self.shallow_update(pseudo_context, consider_remains, context)
        else:
            self.deep_update(pseudo_context)

    def conclude(self):
        probs = dict()
        flags, hints = [], []
        minimum, maximum = 1, 0
        for position, cnt in self.position_cnt.items():
            times_flag, times_relevant = cnt
            if times_relevant != self.cnt:
                # invalid if times of relevant is not equal to total times
                probs[position] = None
            else:
                probs[position] = times_flag / self.cnt
                if math.isclose(times_flag, 0):
                    hints.append(position)
                elif math.isclose(times_flag, self.cnt):
                    flags.append(position)
        return {"probs": probs, "flags": flags, "hints": hints}

    def shallow_update(self, pseudo_context, consider_remains=False, context=None):
        for candidate_flag in pseudo_context.pseudo_flags:
            if candidate_flag not in self.position_cnt:
                self.position_cnt[candidate_flag] = [0, 0]
            self.position_cnt[candidate_flag][0] += 1
            self.position_cnt[candidate_flag][1] += 1

        for candidate_hint in pseudo_context.pseudo_hints:
            if candidate_hint not in self.position_cnt:
                self.position_cnt[candidate_hint] = [0, 0]
            self.position_cnt[candidate_hint][1] += 1

        if consider_remains:
            remains = context.front_side.remains - len(pseudo_context.pseudo_flags)
            inland_unseens = [unseen for unseen in context.front_side.unseens
                              if unseen not in pseudo_context.pseudo_flags and unseen not in pseudo_context.pseudo_hints]

            for unseen in inland_unseens:
                if unseen not in self.position_cnt:
                    self.position_cnt[unseen] = [0, 0]
                if remains > 0:
                    self.position_cnt[unseen][0] += remains / len(inland_unseens)
                self.position_cnt[unseen][1] += 1

    def deep_update(self, pseudo_context):
        if len(pseudo_context.pseudo_flags) not in self.pseudo_contexts:
            flag_cnts = {
                **{pseudo_flag: 1. for pseudo_flag in pseudo_context.pseudo_flags},
                **{pseudo_hint: 0. for pseudo_hint in pseudo_context.pseudo_hints},
            }
            self.pseudo_contexts[len(pseudo_context.pseudo_flags)] = {"flag_cnts": flag_cnts, "cnt": 1}
        else:
            flag_cnts = self.pseudo_contexts[len(pseudo_context.pseudo_flags)]["flag_cnts"]
            cnt = self.pseudo_contexts[len(pseudo_context.pseudo_flags)]["cnt"]
            for pseudo_flag in pseudo_context.pseudo_flags:
                flag_cnts[pseudo_flag] += 1
            self.pseudo_contexts[len(pseudo_context.pseudo_flags)] = {"flag_cnts": flag_cnts, "cnt": cnt + 1}

    @staticmethod
    def merge_conclusions(conclusions):
        probs = dict()
        flags, hints = set(), set()
        for conclusion in conclusions:
            flags.update(conclusion["flags"])
            hints.update(conclusion["hints"])
            for pos, prob in conclusion["probs"].items():
                probs[pos] = max(prob, probs.get(pos, 0.))
        return {"probs": probs, "flags": list(flags), "hints": list(hints)}

    @staticmethod
    def joint_counters(counters, inland_unseens, remains):
        # UGLY IMPLEMENT
        def dp(counters):
            statistics = defaultdict(int)
            statistics[0] = 1
            for i, counter in enumerate(counters, start=1):
                assert counter.mode == "deep"
                updated = defaultdict(int)
                for mines, info_dict in counter.pseudo_contexts.items():
                    cnt = info_dict["cnt"]
                    for prev_mines, prev_cnt in statistics.items():
                        if prev_mines + mines <= remains:
                            updated[prev_mines + mines] += prev_cnt * cnt
                statistics = updated
            return statistics

        # total and inland unseens probs
        statistics = dp(counters)
        total = 0
        for mines, cnt in statistics.items():
            if remains - len(inland_unseens) <= mines <= remains:
                total += cnt * math.comb(len(inland_unseens), remains - mines)
        if total == 0:
            raise ValueError("No valid solution.")

        inland_cnts = defaultdict(int)
        for mines, cnt in statistics.items():
            for inland_unseen in inland_unseens:
                if mines < remains:
                    inland_cnts[inland_unseen] += cnt * math.comb(len(inland_unseens) - 1, remains - mines - 1)
                else:
                    inland_cnts[inland_unseen] += 0
        inland_probs = {inland_unseen: cnt / total for inland_unseen, cnt in inland_cnts.items()}

        cnts = defaultdict(int)
        for i, counter in enumerate(counters):
            around_cnts = defaultdict(int)
            statistics = dp(counters[:i] + counters[i + 1:])
            for mines, info_dict in counter.pseudo_contexts.items():
                cnt = info_dict["cnt"]
                for prev_mines, prev_cnt in statistics.items():
                    if remains - len(inland_unseens) <= mines + prev_mines <= remains:
                        for unseen, flag_cnt in info_dict["flag_cnts"].items():
                            around_cnts[unseen] += flag_cnt * prev_cnt * math.comb(len(inland_unseens), remains - mines - prev_mines)
            assert set(cnts.keys()).isdisjoint(set(around_cnts.keys()))
            cnts.update(around_cnts)

        probs = {unseen: cnt / total for unseen, cnt in cnts.items()}
        probs.update(inland_probs)
        return probs
