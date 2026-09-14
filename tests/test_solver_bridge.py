from minesweeper_video.board import Board
from minesweeper_video.solver_bridge import SolverBridge


def test_solver_bridge_returns_valid_move():
    board = Board(9, 9, 10, first_click_safe=True, seed=42)
    bridge = SolverBridge(board)
    move = bridge.get_next_move()
    assert move is not None
    assert move.action in ('click', 'flag', 'none')
    assert 0 <= move.row < 9
    assert 0 <= move.col < 9


def test_mine_probabilities_shape():
    board = Board(9, 9, 10, seed=42)
    bridge = SolverBridge(board)
    bridge.get_next_move()
    assert bridge.mine_probabilities is not None
    assert bridge.mine_probabilities.shape == (9, 9)


def test_mine_probabilities_are_none_before_first_move():
    board = Board(9, 9, 10, seed=42)
    bridge = SolverBridge(board)
    assert bridge.mine_probabilities is None


def test_solver_bridge_reflects_board_state():
    board = Board(9, 9, 10, first_click_safe=True, seed=42)
    bridge = SolverBridge(board)
    move = bridge.get_next_move()
    board.reveal(move.row, move.col)
    move2 = bridge.get_next_move()
    assert move2 is not None


def test_solver_suppresses_stdout(capsys):
    board = Board(9, 9, 10, seed=42)
    bridge = SolverBridge(board)
    bridge.get_next_move()
    captured = capsys.readouterr()
    assert captured.out == ""


def test_our_config_module_survives_the_solver_import():
    """The vendored solver has its own top-level `config`. Importing it must not
    shadow or break ours."""
    from minesweeper_video.config import Config
    Board(9, 9, 10, seed=1)
    SolverBridge(Board(9, 9, 10, seed=1)).get_next_move()
    assert Config().board.rows == 16
