import pytest
import numpy as np
from minesweeper_video.board import Board, UNOPENED, FLAG, MINE, EMPTY


def test_too_many_mines_raises():
    with pytest.raises(ValueError, match="Too many mines"):
        Board(9, 9, 73)  # max safe = 9*9 - 9 = 72


def test_mine_count_matches_config():
    board = Board(9, 9, 10, seed=42)
    board.reveal(4, 4)
    assert len(board.mine_positions) == 10


def test_first_click_safe():
    board = Board(9, 9, 10, first_click_safe=True, seed=42)
    board.reveal(4, 4)
    assert (4, 4) not in board.mine_positions
    for dr, dc in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
        assert (4+dr, 4+dc) not in board.mine_positions


def test_seed_reproducibility():
    b1 = Board(9, 9, 10, seed=1)
    b2 = Board(9, 9, 10, seed=1)
    b1.reveal(4, 4)
    b2.reveal(4, 4)
    assert b1.mine_positions == b2.mine_positions


def test_flag_toggles():
    board = Board(9, 9, 10, seed=42)
    board.flag(0, 0)
    assert board.game_state[0][0] == FLAG
    board.flag(0, 0)
    assert board.game_state[0][0] == UNOPENED


def test_remaining_mines_decrements_on_flag():
    board = Board(9, 9, 10, seed=42)
    assert board.remaining_mines == 10
    board.flag(0, 0)
    assert board.remaining_mines == 9


def test_is_won_when_all_safe_cells_revealed():
    for seed in range(20):
        board = Board(2, 2, 1, first_click_safe=False, seed=seed)
        result = board.reveal(0, 0)
        if result.hit_mine:
            continue
        for r in range(2):
            for c in range(2):
                if (r, c) not in board.mine_positions:
                    board.reveal(r, c)
        assert board.is_won
        break


def test_reveal_returns_flood_fill_cells():
    board = Board(9, 9, 10, first_click_safe=True, seed=42)
    result = board.reveal(4, 4)
    assert len(result.revealed) >= 1
    assert not result.hit_mine


def test_game_state_values_in_valid_range():
    board = Board(9, 9, 10, seed=42)
    board.reveal(4, 4)
    valid = {-4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8}
    for r in range(9):
        for c in range(9):
            assert board.game_state[r][c] in valid


def test_is_lost_after_hitting_mine():
    for seed in range(100):
        board = Board(9, 9, 10, first_click_safe=False, seed=seed)
        board._place_mines(set())
        if (0, 0) in board.mine_positions:
            result = board.reveal(0, 0)
            assert result.hit_mine
            assert board.is_lost
            break
