# -*- coding: utf-8 -*-
# Time    : 2023/1/3 13:32
# Author  : Yichen Lu


class Counter(object):
    """
    counter: position -> [times of flag, times of relevant]
    """
    def __init__(self):
        self.cnt = 0
        self.position_cnt = dict()

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
                if times_flag == 0:
                    hints.append(position)
                elif times_flag == self.cnt:
                    flags.append(position)
        return {"probs": probs, "flags": flags, "hints": hints}
