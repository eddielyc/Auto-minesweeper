# -*- coding: utf-8 -*-
# Time    : 2023/1/2 10:40
# Author  : Yichen Lu


from typing import Dict, Set
import random
from collections import deque
from game import board, interact
from global_variables import *
import itertools
import utils
from solver.counter import Counter
from solver.attempt import Attempt


class PseudoContext(object):
    def __init__(self):
        self.visited = set()
        self.pseudo_flags = set()
        self.pseudo_hints = set()

    def update(self, attempt: Attempt):
        assert self.pseudo_flags.isdisjoint(attempt.pseudo_flags) and \
               self.pseudo_hints.isdisjoint(attempt.pseudo_hints) and \
               (attempt.h, attempt.w) not in self.visited

        self.visited.add((attempt.h, attempt.w))
        self.pseudo_flags.update(attempt.pseudo_flags)
        self.pseudo_hints.update(attempt.pseudo_hints)

    def undo(self, attempt: Attempt):
        assert self.pseudo_flags.issuperset(attempt.pseudo_flags) and \
               self.pseudo_hints.issuperset(attempt.pseudo_hints) and \
               (attempt.h, attempt.w) in self.visited

        self.visited.remove((attempt.h, attempt.w))
        self.pseudo_flags.difference_update(attempt.pseudo_flags)
        self.pseudo_hints.difference_update(attempt.pseudo_hints)


class Engine(object):
    def __init__(self, context):
        self.context = context

    def what_next(self):
        if len(self.context.front_side.hints) == 0:
            return self.random_step()
        ops = []

        # --------- inference with level 1 (single hop) ---------
        for hint_h, hint_w in self.context.front_side.hints:
            conclusion = self.inference(level=1, h=hint_h, w=hint_w)
            ops.extend([interact.Operation(h, w, "step") for h, w in conclusion["hints"]])
            ops.extend([interact.Operation(h, w, "flag") for h, w in conclusion["flags"]])
            if ops:
                return ops

        # no solution in all first hops
        # --------- inference with level 2 (double hop) ---------
        probs = dict()
        for hint_h, hint_w in self.context.front_side.hints:
            conclusion = self.inference(level=2, h=hint_h, w=hint_w)
            ops.extend([interact.Operation(h, w, "step") for h, w in conclusion["hints"]])
            ops.extend([interact.Operation(h, w, "flag") for h, w in conclusion["flags"]])
            if ops:
                return ops
            else:
                for position, prob in conclusion["probs"].items():
                    if prob is not None:
                        if position in probs:
                            probs[position] = max(prob, probs[position])
                        else:
                            probs[position] = prob

        # no solution in all double hops
        # --------- inference with level 3 (multiple hop) ---------
        if self.context.front_side.remains <= 10:
            conclusion = self.inference(level=3)
            ops.extend([interact.Operation(h, w, "step") for h, w in conclusion["hints"]])
            ops.extend([interact.Operation(h, w, "flag") for h, w in conclusion["flags"]])
            if ops:
                return ops
            else:
                for position, prob in conclusion["probs"].items():
                    if prob is not None:
                        if prob in probs:
                            probs[position] = max(prob, probs[position])
                        else:
                            probs[position] = prob

        # --------- inference with level 4 (multiple hop and consider remaining mines) ---------
        if self.context.front_side.remains <= 10:
            conclusion = self.inference(level=4)
            ops.extend([interact.Operation(h, w, "step") for h, w in conclusion["hints"]])
            ops.extend([interact.Operation(h, w, "flag") for h, w in conclusion["flags"]])
            if ops:
                # input()
                return ops
            else:
                for position, prob in conclusion["probs"].items():
                    if prob is not None:
                        if prob in probs:
                            probs[position] = max(prob, probs[position])
                        else:
                            probs[position] = prob
            # self.context.save()

        # self.context.save()
        # input()

        # four corners first
        if self.context.front_side.type(0, 0) == UNSEEN and (0, 0) not in probs:
            return interact.Operation(0, 0, "step")
        elif self.context.front_side.type(0, WIDTH - 1) == UNSEEN and (0, WIDTH - 1) not in probs:
            return interact.Operation(0, WIDTH - 1, "step")
        elif self.context.front_side.type(HEIGHT - 1, 0) == UNSEEN and (HEIGHT - 1, 0) not in probs:
            return interact.Operation(HEIGHT - 1, 0, "step")
        elif self.context.front_side.type(HEIGHT - 1, WIDTH - 1) == UNSEEN and (HEIGHT - 1, WIDTH - 1) not in probs:
            return interact.Operation(HEIGHT - 1, WIDTH - 1, "step")
        # greedy strategy
        elif probs:
            max_prob, max_position = 0, None
            min_prob, min_position = 1, None
            for position, prob in probs.items():
                if prob > max_prob:
                    max_prob, max_position = prob, position
                if prob < min_prob:
                    min_prob, min_position = prob, position

            if 1 - max_prob < min_prob:
                h, w = max_position
                return interact.Operation(h, w, "flag")
            else:
                h, w = min_position
                return interact.Operation(h, w, "step")
        else:
            return self.random_step()

    def inference(
            self,
            level=1,
            h=None,
            w=None,
    ):
        """
        dfs possible attempts
        :param level:
            level 1: inference with single point
            level 2: inference with single point and hints around
            level 3: inference with multiple hints
            level 4: inference with multiple hints and number of remaining mines
        :param h: h
        :param w: w
        :return: probability table
        """

        pseudo_context = PseudoContext()
        counter = Counter()

        # inference with level 1 or 2
        if level <= 2:
            assert h is not None and w is not None
            first_hop = utils.look_around(h, w, self.context)
            for attempt in self.iter_attempts(h, w, first_hop):
                pseudo_context.update(attempt)
                if self.is_valid_attempt(self.context, pseudo_context):
                    if level == 1:
                        counter.update(attempt)
                    else:
                        around_hints = list(
                            utils.iter_arounds(
                                first_hop["unseens"],
                                around_type="HINT",
                                context=self.context,
                                blocks={(h, w)},
                            )
                        )
                        self.dfs(around_hints, self.context, pseudo_context, counter)
                pseudo_context.undo(attempt)
        elif level == 3:
            incomplete_hints = list(utils.iter_incomplete_hints(context=self.context))
            self.dfs(incomplete_hints, self.context, pseudo_context, counter, consider_remains=False)
        elif level == 4:
            incomplete_hints = list(utils.iter_incomplete_hints(context=self.context))
            self.dfs(incomplete_hints, self.context, pseudo_context, counter, consider_remains=True)
        else:
            raise ValueError(f"Invalid level inference level: {level}, expect level in [1, 2, 3, 4].")
        conclusion = counter.conclude()
        return conclusion

    def dfs(
            self,
            hints,
            context: interact.Context,
            pseudo_context: PseudoContext = None,
            counter=None,
            consider_remains=False,
    ):
        if len(hints) == 0:
            counter.update(pseudo_context, consider_remains, context)
            return
        # try:
        hint_h, hint_w = hints.pop()
        # except:
        #     pass

        around = utils.look_around(hint_h, hint_w, context, pseudo_context)
        attempts = list(self.iter_attempts(hint_h, hint_w, around))
        if len(attempts) == 0:
            self.dfs(hints, context, pseudo_context, counter, consider_remains)
            hints.append((hint_h, hint_w))
            return

        for attempt in attempts:
            pseudo_context.update(attempt)
            if self.is_valid_attempt(context, pseudo_context):
                self.dfs(hints, context, pseudo_context, counter, consider_remains)
            pseudo_context.undo(attempt)
        hints.append((hint_h, hint_w))

    def is_valid_attempt(self, context: interact.Context, pseudo_context: PseudoContext):
        if len(pseudo_context.pseudo_flags) > context.front_side.remains:
            return False
        # iter hint positions which are affected by attempt(s)
        attempt_points = pseudo_context.pseudo_hints.union(pseudo_context.pseudo_flags)
        for around_h, around_w in utils.iter_arounds(attempt_points, around_type="HINT", context=context):
            if not self.is_valid_hint(around_h, around_w, context, pseudo_context):
                return False
        return True

    def is_valid_hint(self, h, w, context, pseudo_context):
        """
        is valid hint in front side.
        """
        # if it is a pseudo hint, just return True
        if (h, w) in pseudo_context.pseudo_hints:
            return True
        elif context.front_side.type(h, w) == "HINT":
            around = utils.look_around(h, w, context, pseudo_context)
            return 0 <= around["remains"] <= len(around["unseens"])
        else:
            raise RuntimeError

    @staticmethod
    def first_step():
        h, w = random.choice(list(range(HEIGHT))), random.choice(list(range(WIDTH)))
        return interact.Operation(h, w, "step")

    def random_step(self):
        h, w = random.choice(list(self.context.front_side.unseens))
        return interact.Operation(h, w, "step")

    def iter_attempts(self, h, w, around):
        unseens, num_mines = around["unseens"], around["remains"]
        if len(unseens) == 0:
            return

        for flag_indices in itertools.combinations(list(range(len(around["unseens"]))), num_mines):
            flag_indices = set(flag_indices)
            pseudo_flags, pseudo_hints = set(), set()
            for i in range(len(unseens)):
                if i in flag_indices:
                    pseudo_flags.add(unseens[i])
                else:
                    pseudo_hints.add(unseens[i])
            yield Attempt(h, w, pseudo_flags, pseudo_hints)
