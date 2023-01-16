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

        # "most" mode or no solution in all first hops
        # --------- inference with level 2 (double hop) ---------

        for hint_h, hint_w in utils.iter_incomplete_hints(self.context):
            conclusion = self.inference(level=2, h=hint_h, w=hint_w)
            ops.update({interact.Operation(h, w, "step") for h, w in conclusion["hints"]})
            ops.update({interact.Operation(h, w, "flag") for h, w in conclusion["flags"]})
            if ops and mode == "least":
                return ops

        if mode == "most" and ops:
            return ops

        # level 4 first
        # --------- inference with level 4 (multiple hop and consider remaining mines) ---------
        if self.context.front_side.remains <= LEVEL4_THESHOLD:
            print("Inference with level 4")
            conclusion = self.inference(level=4)
            ops.update({interact.Operation(h, w, "step") for h, w in conclusion["hints"]})
            ops.update({interact.Operation(h, w, "flag") for h, w in conclusion["flags"]})
            if ops:
                return ops

        # --------- inference with level 6 (global inference) ---------
        print("Inference with level 6")
        conclusion = self.inference(level=6)

        # self.context.save()
        return self.let_me_guess(conclusion["probs"])

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
            counter = Counter()
            pseudo_context = PseudoContext()
            incomplete_hints = list(utils.iter_incomplete_hints(context=self.context))
            self.dfs(incomplete_hints, self.context, pseudo_context, counter, consider_remains=False)
            conclusion = counter.conclude()
        elif level == 4:
            counter = Counter()
            pseudo_context = PseudoContext()
            incomplete_hints = list(utils.iter_incomplete_hints(context=self.context))
            self.dfs(incomplete_hints, self.context, pseudo_context, counter, consider_remains=True)
            conclusion = counter.conclude()
        elif level == 5:
            incomplete_hint_groups = self.joint_unseen_grouping()
            conclusions = []
            for group in incomplete_hint_groups:
                counter = Counter()
                pseudo_context = PseudoContext()
                self.dfs(list(group), self.context, pseudo_context, counter, consider_remains=False)
                conclusions.append(counter.conclude())
            conclusion = Counter.merge_conclusions(conclusions)

            inland_unseens = list(utils.iter_inland_unseens(self.context))
            n_mines_around = self.n_mines_around(incomplete_hint_groups)
            remains = self.context.front_side.remains
            probs = {unseen: (remains - n_mines_around) / len(inland_unseens) for unseen in inland_unseens}
            conclusion = Counter.merge_conclusions([conclusion, {"probs": probs, "flags": [], "hints": []}])
            # conclusion = {"probs": probs, "flags": [], "hints": []}
        elif level == 6:
            incomplete_hint_groups = self.joint_unseen_grouping()
            counters = self.deep_inference(incomplete_hint_groups, force_dfs=False)
            inland_unseens = list(utils.iter_inland_unseens(self.context))
            try:
                probs = Counter.joint_counters(counters, inland_unseens, self.context.front_side.remains)
            except ValueError:
                counters = self.deep_inference(incomplete_hint_groups, force_dfs=True)
                probs = Counter.joint_counters(counters, inland_unseens, self.context.front_side.remains)
            conclusion = {"probs": probs, "flags": [], "hints": []}
        else:
            raise ValueError(f"Invalid level inference level: {level}, expect level in [1, 2, 3, 4, 5].")
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
            return

        hint_h, hint_w = hints.pop()

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
            if terminate_func and terminate_func():
                hints.append((hint_h, hint_w))
                return
        hints.append((hint_h, hint_w))

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

    def joint_unseen_grouping(self):
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

    def n_mines_around(self, incomplete_hint_groups):
        """
        number of mines around at most for sure.
        :return: mines
        """
        def dfs(incomplete_hints, visited_unseens: Set, mines=0, maximum=0):
            if not incomplete_hints:
                maximum = mines if mines > maximum else maximum
                return maximum

            hint_h, hint_w = incomplete_hints.pop()
            around = utils.look_around(hint_h, hint_w, self.context)
            around_unseens = set(around["unseens"])
            if visited_unseens.intersection(around_unseens):
                maximum = dfs(incomplete_hints, visited_unseens, mines, maximum)
            else:
                # join dfs
                visited_unseens.update(around_unseens)
                mines += around["remains"]
                maximum = dfs(incomplete_hints, visited_unseens, mines, maximum)
                visited_unseens.difference_update(around_unseens)
                mines -= around["remains"]
                # not join dfs
                maximum = dfs(incomplete_hints, visited_unseens, mines, maximum)

            incomplete_hints.append((hint_h, hint_w))
            return maximum

        n_mines_around = sum([dfs(list(group), set()) for group in incomplete_hint_groups])
        return n_mines_around

    def let_me_guess(self, probs: Dict):
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
            self.hold_on(f"Min prob position {(h, w)}: {min_prob}  {probs}")
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
            if force_dfs or (len(group) <= LEVEL6_THESHOLD1):
                counter = Counter(mode="deep")
                pseudo_context = PseudoContext()
                self.dfs(list(group), self.context, pseudo_context, counter)
            elif LEVEL6_THESHOLD1 < len(group) <= LEVEL6_THESHOLD2:
                n_mines_around = self.n_mines_around([group])
                around_unseens = list(utils.iter_arounds(group, around_type=UNSEEN, context=self.context))
                counter = Counter(mode="deep")
                counter.pseudo_contexts = {
                    n_mines_around: {
                        "flag_cnts": {pos: n_mines_around / len(around_unseens) for pos in around_unseens},
                        "cnt": 1,
                    }
                }
                counter.cnt = 1
            else:
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
