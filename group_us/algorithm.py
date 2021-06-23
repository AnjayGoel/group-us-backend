import math
import os
import random
from subprocess import call
from typing import *

import numpy as np


def clear():
    _ = call('clear' if os.name == 'posix' else 'cls')


class Game:
    def __init__(self, prefs: np.ndarray, r: int = 4, iter1: int = 2, iter2: int = 4):
        self.r = r
        self.prefs = prefs
        self.iter1 = iter1
        self.iter2 = iter2
        self.n = self.prefs.shape[0]
        self.ng = math.ceil(self.n / r)
        self.ungrouped = [i for i in range(self.n)]
        self.unfilled = []
        self.filled = []

        for i in random.sample(range(0, self.n), self.ng):
            self.unfilled.append(Group(self, [i]))
            self.ungrouped.remove(i)
        super().__init__()

    @staticmethod
    def from_csv(file_path, r: int = 4):
        prefs = np.genfromtxt(file_path, delimiter=',')
        return Game(prefs, r)

    def get_mem_pref_for_group(self, mem: int, grp: List[int]) -> int:
        pref: int = 0
        for i in grp:
            pref += self.prefs[mem][i]
        pref = pref * (1.0 / len(grp))
        return pref

    def get_group_pref_for_mem(self, mem: int, grp: List[int]) -> int:
        pref: int = 0
        for i in grp:
            pref += self.prefs[i][mem]
        pref = pref * (1.0 / len(grp))
        return pref

    def get_group_score(self, y: List[int]) -> int:
        if len(y) <= 1:
            return 0
        score: int = 0
        for i in y:
            for j in y:
                if not (i == j):
                    score += self.prefs[i][j]
        score = score * (1.0 / (len(y) ** 2 - len(y)))
        return score

    def get_net_score(self) -> float:
        score = 0
        for i in self.filled:
            score += self.get_group_score(i.members)
        return score / self.ng

    def solve(self):
        while len(self.ungrouped) != 0:
            self.add_one_member()

        self.filled.extend(self.unfilled)
        self.unfilled = []
        self.optimize(use_filled=True)
        groups = []
        for i in self.filled:
            groups.append(i.members)
        return self.get_net_score(), groups

    def optimize(self, use_filled: bool = True):
        if use_filled:
            grps = self.filled
        else:
            grps = self.unfilled

        iterator = self.iter2 if use_filled else self.iter1

        for a in range(iterator):
            for grp_one in grps:
                for mem_one in grp_one.members:
                    for grp_two in grps:
                        if mem_one == -1:
                            break
                        if grp_two == grp_one:
                            continue
                        for mem2 in grp_two.members:
                            if mem_one == -1:
                                break
                            if mem2 == mem_one:
                                continue
                            grp_two_mem_one = grp_two.members.copy()
                            grp_two_mem_one.remove(mem2)
                            grp_two_mem_one.append(mem_one)
                            grp_one_mem_two = grp_one.members.copy()
                            grp_one_mem_two.remove(mem_one)
                            grp_one_mem_two.append(mem2)

                            grp_one_new_score = self.get_group_score(grp_one_mem_two)
                            grp_two_new_score = self.get_group_score(grp_two_mem_one)

                            if (grp_one_new_score + grp_two_new_score > self.get_group_score(grp_one.members)
                                    + self.get_group_score(grp_two.members)):
                                grp_one.add_member(mem2)
                                grp_one.remove_member(mem_one)
                                grp_two.add_member(mem_one)
                                grp_two.remove_member(mem2)
                                mem_one = -1

    def add_one_member(self):

        proposed = np.zeros(
            shape=(len(self.ungrouped), len(self.unfilled)), dtype=bool)

        is_temp_grouped = [False for i in range(len(self.ungrouped))]

        temp_pref = np.zeros(
            shape=(len(self.ungrouped), len(self.unfilled)))

        temp_pref_order = np.zeros(
            shape=(len(self.ungrouped), len(self.unfilled)), dtype=int)

        for i, mem in enumerate(self.ungrouped):
            for j, grp in enumerate(self.unfilled):
                temp_pref[i][j] = self.get_mem_pref_for_group(mem, grp.members)

        for i, mem in enumerate(self.ungrouped):
            temp_pref_order[i] = np.argsort(temp_pref[i])[::-1]

        while is_temp_grouped.count(False) != 0:
            for i, mem in enumerate(self.ungrouped):

                if is_temp_grouped[i]:
                    continue

                if np.count_nonzero(proposed[i] == False) == 0:
                    is_temp_grouped[i] = True
                    continue
                for j in temp_pref_order[i]:
                    if proposed[i][j]:
                        continue

                    grp = self.unfilled[j]
                    proposed[i][j] = True
                    pref = self.get_group_pref_for_mem(mem, grp.members)
                    if pref > grp.temp_score:
                        if grp.temp_member >= 0:
                            is_temp_grouped[self.ungrouped.index(
                                grp.temp_member)] = False
                        grp.add_temp(mem)
                        is_temp_grouped[i] = True
                        break

        for grp in self.unfilled:
            if grp.temp_member < 0:
                continue
            self.ungrouped.remove(grp.temp_member)
            grp.add_permanently()

        self.optimize(use_filled=False)

        for grp in self.unfilled:
            if grp.size() >= self.r or len(self.ungrouped) == 0:
                self.filled.append(grp)

        for grp in self.filled:
            self.unfilled.remove(grp)


class Group:
    def __init__(self, game: Game, members: List[int] = []):
        super().__init__()
        self.game = game
        self.members = members
        self.temp_member = -1
        self.temp_score = -1

    def add_member(self, x: int):
        self.members.append(x)

    def remove_member(self, x: int):
        self.members.remove(x)

    def add_temp(self, x: int) -> int:
        self.temp_member = x
        self.temp_score = self.game.get_group_pref_for_mem(x, self.members)
        return self.temp_score

    def add_permanently(self):
        if self.temp_member == -1:
            return
        self.add_member(self.temp_member)
        self.temp_member = -1
        self.temp_score = -1

    def size(self) -> int:
        return len(self.members)
