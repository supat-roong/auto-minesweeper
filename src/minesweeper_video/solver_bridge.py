import contextlib
import io
import math
import sys
from pathlib import Path
from typing import Optional, Tuple

import numpy as np

from minesweeper_video.config import REPO_ROOT

_SOLVER_SRC = REPO_ROOT / 'vendor' / 'minesweeper_solver' / 'src'

if not _SOLVER_SRC.exists():
    raise ImportError(
        f"minesweeper_solver not found at {_SOLVER_SRC}. "
        "It is a git submodule — run: git submodule update --init"
    )
if str(_SOLVER_SRC) not in sys.path:
    sys.path.insert(0, str(_SOLVER_SRC))

from solver import MinesweeperSolver            # noqa: E402  (needs the path above)
from custom_dataclass import CellData, CellPosition   # noqa: E402


class SolverBridge:
    def __init__(self, board):
        self._board = board
        self._mine_probabilities: Optional[np.ndarray] = None

    def _build_cell_data(self) -> dict:
        cell_data = {}
        for r in range(self._board.rows):
            for c in range(self._board.cols):
                cell_data[(r, c)] = CellData(
                    state=int(self._board.game_state[r][c]),
                    position=CellPosition(
                        letter='A',
                        screen_x_range=(0, 0),
                        screen_y_range=(0, 0),
                        screen_x=0,
                        screen_y=0,
                        grid_row=r,
                        grid_col=c,
                    )
                )
        return cell_data

    def get_next_move(self, cursor_cell: Optional[Tuple[float, float]] = None):
        """Return the best move, preferring the candidate closest to cursor_cell=(row, col)
        when multiple cells tie on flag-certain (prob=1) or safe-certain (prob=0) moves."""
        cell_data = self._build_cell_data()
        solver = MinesweeperSolver(
            self._board.game_state.copy(),
            cell_data,
            self._board.mines,
        )
        with contextlib.redirect_stdout(io.StringIO()):
            move = solver.get_best_move()
        self._mine_probabilities = solver.mine_probabilities.copy()

        if cursor_cell is not None and move.action in ('flag', 'click'):
            move = self._closest_tied(solver.mine_probabilities, move, cursor_cell)

        return move

    def _closest_tied(self, probs, move, cursor_cell):
        """Among all unopened cells tied at move.probability, return the one nearest cursor."""
        UNOPENED = -1
        candidates = np.argwhere(
            (self._board.game_state == UNOPENED) &
            (np.abs(probs - move.probability) < 1e-6)
        )
        if len(candidates) <= 1:
            return move
        cr, cc = cursor_cell
        best = min(candidates, key=lambda rc: math.sqrt((rc[0] - cr) ** 2 + (rc[1] - cc) ** 2))
        return move.__class__(int(best[0]), int(best[1]), move.action, move.probability)

    @property
    def mine_probabilities(self) -> Optional[np.ndarray]:
        return self._mine_probabilities
