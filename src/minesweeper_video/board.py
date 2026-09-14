import numpy as np
import random
from dataclasses import dataclass
from typing import Optional

UNOPENED = -1
FLAG = -2
MINE = -3
EMPTY = 0


@dataclass
class RevealResult:
    revealed: list  # list of (row, col, value) tuples
    hit_mine: bool


class Board:
    def __init__(self, rows: int, cols: int, mines: int,
                 first_click_safe: bool = True, seed: Optional[int] = None):
        safe_zone = 9 if first_click_safe else 1
        max_mines = rows * cols - safe_zone
        if mines >= max_mines:
            raise ValueError(f"Too many mines: {mines} for {rows}x{cols} (max {max_mines})")
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.first_click_safe = first_click_safe
        self._rng = random.Random(seed)
        self._mine_positions: frozenset = frozenset()
        self._mine_counts = np.zeros((rows, cols), dtype=int)
        self.game_state = np.full((rows, cols), UNOPENED, dtype=int)
        self._mines_placed = False
        self._flags: set = set()
        self._revealed: set = set()

    def _place_mines(self, exclude: set) -> None:
        candidates = [
            (r, c) for r in range(self.rows) for c in range(self.cols)
            if (r, c) not in exclude
        ]
        positions = self._rng.sample(candidates, self.mines)
        self._mine_positions = frozenset(positions)
        for mr, mc in positions:
            for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                nr, nc = mr + dr, mc + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    self._mine_counts[nr][nc] += 1
        self._mines_placed = True

    def _neighbors(self, r: int, c: int) -> list:
        return [
            (r + dr, c + dc)
            for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
            if 0 <= r + dr < self.rows and 0 <= c + dc < self.cols
        ]

    def _flood_fill(self, r: int, c: int, revealed: list) -> None:
        if (r, c) in self._revealed or self.game_state[r][c] != UNOPENED:
            return
        self._revealed.add((r, c))
        value = int(self._mine_counts[r][c])
        self.game_state[r][c] = value
        revealed.append((r, c, value))
        if value == EMPTY:
            for nr, nc in self._neighbors(r, c):
                self._flood_fill(nr, nc, revealed)

    def reveal(self, row: int, col: int) -> RevealResult:
        if self.game_state[row][col] == FLAG or (row, col) in self._revealed:
            return RevealResult(revealed=[], hit_mine=False)

        if not self._mines_placed:
            if self.first_click_safe:
                exclude = {(row, col)} | set(self._neighbors(row, col))
            else:
                exclude = set()
            self._place_mines(exclude)

        if (row, col) in self._mine_positions:
            self.game_state[row][col] = MINE
            return RevealResult(revealed=[(row, col, MINE)], hit_mine=True)

        revealed = []
        self._flood_fill(row, col, revealed)
        return RevealResult(revealed=revealed, hit_mine=False)

    def flag(self, row: int, col: int) -> None:
        if (row, col) in self._revealed:
            return
        if self.game_state[row][col] == FLAG:
            self.game_state[row][col] = UNOPENED
            self._flags.discard((row, col))
        else:
            self.game_state[row][col] = FLAG
            self._flags.add((row, col))

    @property
    def mine_positions(self) -> frozenset:
        return self._mine_positions

    @property
    def remaining_mines(self) -> int:
        return self.mines - len(self._flags)

    @property
    def is_won(self) -> bool:
        return len(self._revealed) == self.rows * self.cols - self.mines

    @property
    def is_lost(self) -> bool:
        return bool(np.any(self.game_state == MINE))
