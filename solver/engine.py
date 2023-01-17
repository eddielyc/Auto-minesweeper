# -*- coding: utf-8 -*-
# Time    : 2023/1/2 10:40
# Author  : Yichen Lu

import pdb

import math
import time
from typing import Dict, Set
import random
from collections import deque, defaultdict
from minesweeper import board, interact
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
        self.attempts_chain = []

    def update(self, attempt: Attempt):
        assert self.pseudo_flags.isdisjoint(attempt.pseudo_flags) and \
               self.pseudo_hints.isdisjoint(attempt.pseudo_hints) and \
               (attempt.h, attempt.w) not in self.visited

        self.visited.add((attempt.h, attempt.w))
        self.pseudo_flags.update(attempt.pseudo_flags)
        self.pseudo_hints.update(attempt.pseudo_hints)
        self.attempts_chain.append(hash(attempt))

    def undo(self, attempt: Attempt):
        assert self.pseudo_flags.issuperset(attempt.pseudo_flags) and \
               self.pseudo_hints.issuperset(attempt.pseudo_hints) and \
               (attempt.h, attempt.w) in self.visited

        self.visited.remove((attempt.h, attempt.w))
        self.pseudo_flags.difference_update(attempt.pseudo_flags)
        self.pseudo_hints.difference_update(attempt.pseudo_hints)
        assert self.attempts_chain and self.attempts_chain[-1] == hash(attempt)
        self.attempts_chain.pop()


class Engine(object):
    def __init__(self, context, debug=False):
        self.context = context
        self.debug = debug

    def what_next(self, mode="least"):
        """
        :param mode: "least" mode for context play and "most" mode for win7 play
        :return: ops
        """
        assert mode in ["least", "most"]
        if len(self.context.front_side.hints) == 0:
            return self.random_step()
        ops = set()

        # --------- inference with level 1 (single hop) ---------
        for hint_h, hint_w in utils.iter_incomplete_hints(self.context):
            conclusion = self.inference(level=1, h=hint_h, w=hint_w)
            ops.update({interact.Operation(h, w, "step") for h, w in conclusion["hints"]})
            ops.update({interact.Operation(h, w, "flag") for h, w in conclusion["flags"]})
            if ops and mode == "least":
                return ops

        # "most" mode or no solution in level 1
        # --------- inference with level 2 (double hop) ---------
        for hint_h, hint_w in utils.iter_incomplete_hints(self.context):
            conclusion = self.inference(level=2, h=hint_h, w=hint_w)
            ops.update({interact.Operation(h, w, "step") for h, w in conclusion["hints"]})
            ops.update({interact.Operation(h, w, "flag") for h, w in conclusion["flags"]})
            if ops and mode == "least":
                return ops

        if mode == "most" and ops:
            return ops

        # no solution in level 1 and level 2
        # --------- inference with level 3 (global inference) ---------
        conclusion = self.inference(level=3)
        ops.update({interact.Operation(h, w, "step") for h, w in conclusion["hints"]})
        ops.update({interact.Operation(h, w, "flag") for h, w in conclusion["flags"]})
        if ops:
            return ops

        return self.let_me_guess(conclusion["probs"])

    def inference(
            self,
            level=1,
            h=None,
            w=None,
    ):
        """
        :param level:
            level 1: inference with single point
            level 2: inference with single point and hints around
            level 3: global inference with multiple hints and number of remaining mines
            level 4: global inference to get precise probability
        :param h: h
        :param w: w
        :return: probability table
        """

        # inference with level 1 or 2
        if level <= 2:
            counter = Counter()
            pseudo_context = PseudoContext()
            assert h is not None and w is not None
            first_hop = utils.look_around(h, w, self.context)
            for attempt in self.iter_attempts(h, w, first_hop):
                pseudo_context.update(attempt)
                if self.is_valid_attempt(self.context, pseudo_context):
                    if level == 1:
                        counter.update(pseudo_context)
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
            conclusion = counter.conclude()
        elif level == 3:
            incomplete_hint_groups = self.group_unseens_into_disjoint_sets()
            counters = self.deep_inference(incomplete_hint_groups, force_dfs=False)
            inland_unseens = list(utils.iter_inland_unseens(self.context))
            try:
                conclusion = Counter.conclude_with_disjoint_counters(counters, inland_unseens, self.context.front_side.remains)
            except ValueError:
                conclusion = {"probs": dict(), "flags": [], "hints": []}
                # counters = self.deep_inference(incomplete_hint_groups, force_dfs=True)
                # conclusion = Counter.conclude_with_disjoint_counters(counters, inland_unseens, self.context.front_side.remains)
        else:
            raise ValueError(f"Invalid level inference level: {level}, expect level in [1, 2, 3, 4].")
        return conclusion

    def dfs(
            self,
            hints,
            context: interact.Context,
            pseudo_context: PseudoContext = None,
            counter=None,
            consider_remains=False,
            terminate_func=None,
    ):
        if len(hints) == 0:
            counter.update(pseudo_context, consider_remains, context)
            return True

        hint_h, hint_w = hints.pop()

        around = utils.look_around(hint_h, hint_w, context, pseudo_context)
        attempts = list(self.iter_attempts(hint_h, hint_w, around))
        if len(attempts) == 0:
            finished = self.dfs(hints, context, pseudo_context, counter, consider_remains, terminate_func)
            hints.append((hint_h, hint_w))
            return finished

        for attempt in attempts:
            pseudo_context.update(attempt)
            if self.is_valid_attempt(context, pseudo_context):
                finished = self.dfs(hints, context, pseudo_context, counter, consider_remains, terminate_func)
                if not finished:
                    pseudo_context.undo(attempt)
                    return finished
                elif terminate_func and terminate_func():
                    pseudo_context.undo(attempt)
                    hints.append((hint_h, hint_w))
                    return False
            pseudo_context.undo(attempt)

        hints.append((hint_h, hint_w))
        return True

    def is_valid_attempt(self, context: interact.Context, pseudo_context: PseudoContext):
        if len(pseudo_context.pseudo_flags) > context.front_side.remains or \
                len(context.front_side.unseens) - len(pseudo_context.pseudo_hints) < context.front_side.remains:
            return False
        # iter hint positions which are affected by attempt(s)
        attempt_points = pseudo_context.pseudo_hints.union(pseudo_context.pseudo_flags)
        for around_h, around_w in utils.iter_arounds(attempt_points, around_type="HINT", context=context):
            if not self.is_valid_hint(around_h, around_w, context, pseudo_context):
                return False
        return True

    @staticmethod
    def is_valid_hint(h, w, context, pseudo_context):
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
        if VERSION == "new":
            return interact.Operation(2, 2, "step")
        else:
            return interact.Operation(0, 0, "step")

    def random_step(self):
        h, w = random.choice(list(self.context.front_side.unseens))
        return interact.Operation(h, w, "step")

    @staticmethod
    def iter_attempts(h, w, around):
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

    def group_unseens_into_disjoint_sets(self):
        """
        Divide incomplete hints into groups. In each group, any hint share joint unseen tile with
        some other tiles in the group.
        :return: group list
        """
        incomplete_hints = set(utils.iter_incomplete_hints(self.context))

        uf = utils.UnionFind(incomplete_hints)

        for h, w in incomplete_hints:
            around = utils.look_around(h, w, self.context)
            for unseen_h, unseen_w in around["unseens"]:
                unseen_around = utils.look_around(unseen_h, unseen_w, self.context)
                # hints around unseen must in incomplete_hints
                for hint_h, hint_w in unseen_around["hints"]:
                    if (hint_h, hint_w) != (h, w):
                        uf.union((hint_h, hint_w), (h, w))

        groups = defaultdict(set)
        for incomplete_hint in incomplete_hints:
            groups[uf.find(incomplete_hint)].add(incomplete_hint)
        return list(groups.values())

    def let_me_guess(self, probs: Dict):
        if not probs:
            return self.random_step()

        # only step, no flag
        # 1. sort by probs
        sorted_probs = sorted(list(probs.items()), key=lambda pos_prob: pos_prob[1])
        min_prob_positions = []
        min_prob = sorted_probs[0][1]
        for position, prob in sorted_probs:
            if math.isclose(prob, min_prob):
                min_prob_positions.append(position)

        for h, w in min_prob_positions:
            if (h, w) in [(0, 0), (0, WIDTH - 1), (HEIGHT - 1, 0), (HEIGHT - 1, WIDTH - 1)]:
                return interact.Operation(h, w, "step")

        # 2. sort by number of unseen tiles around, less is better
        min_prob_positions = sorted(
            min_prob_positions,
            key=lambda h_w: len(utils.look_around(h_w[0], h_w[1], self.context)["unseens"])
        )

        h, w = min_prob_positions[0]
        if self.debug:
            self.hold_on(f"Min prob position {(h, w)}: {min_prob}")
        return interact.Operation(h, w, "step")

    def hold_on(self, prefix=None):
        print(prefix)
        msg = input('Input: (Press "save" to save the context, press "debug" to debug with pdb)')
        if msg.strip() == "save":
            self.context.save()
        elif msg.strip() == "debug":
            pdb.set_trace()

    def deep_inference(self, incomplete_hint_groups, force_dfs=False):
        counters = []
        for group in incomplete_hint_groups:
            if force_dfs:
                counter = Counter(mode="deep")
                pseudo_context = PseudoContext()
                self.dfs(list(group), self.context, pseudo_context, counter)
            else:
                counter = Counter(mode="deep")
                pseudo_context = PseudoContext()
                start = time.time()
                finished = self.dfs(list(group), self.context, pseudo_context, counter,
                                    terminate_func=utils.create_timer_function(time.time(), LEVEL3_THRESHOLD))
                if not finished:
                    # simple estimate
                    counter = Counter(mode="deep")
                    pseudo_context = PseudoContext()
                    self.dfs(list(group), self.context, pseudo_context, counter, terminate_func=lambda: counter.cnt >= 1)
                    n_mines_around = min(counter.pseudo_contexts.keys())
                    around_unseens = list(utils.iter_arounds(group, around_type=UNSEEN, context=self.context))
                    counter.pseudo_contexts = {
                        n_mines_around: {
                            "flag_cnts": {pos: n_mines_around / len(around_unseens) for pos in around_unseens},
                            "cnt": 1
                        }
                    }
                    counter.cnt = 1
            counters.append(counter)
        return counters
