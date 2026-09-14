from pathlib import Path

BOARD_HTML = Path(__file__).resolve().parents[1] / 'web' / 'board.html'


def _html():
    return BOARD_HTML.read_text()


def test_board_html_exists():
    assert BOARD_HTML.exists()


def test_dashboard_is_fully_removed():
    html = _html()
    for needle in ('DASHBOARD', 'id="dashboard"', 'dash-block', 'dash-label',
                   'dash-row', 'dash-head', 'd-mine', 'd-ov-games'):
        assert needle not in html, f"leftover dashboard markup: {needle}"


def test_board_api_is_intact():
    html = _html()
    for fn in ('init', 'setCounter', 'setTimer', 'setGameInfo', 'setOverlay',
               'setCursorAt', 'setCursor', 'flag', 'pressMouse', 'releaseMouse',
               'reveal', 'explode', 'showAllMines', 'autoFlagMines',
               'win', 'lose', 'setProbability'):
        assert f"{fn}(" in html, f"missing BOARD.{fn}"
    assert 'window.BOARD' in html
    assert 'id="stage"' in html


def test_sprites_present():
    sprites = (BOARD_HTML.parent / 'assets' / 'minesweeper').glob('*.png')
    names = {p.name for p in sprites}
    for required in ('smile.png', 'flag.png', 'mine-icon.png', 'mine-death.png',
                     'misflagged.png', 'dead.png', 'win.png', 'ohh.png',
                     'checked.png', 'question.png', 'digit-.png'):
        assert required in names
    for i in range(1, 9):
        assert f'open{i}.png' in names
    for i in range(10):
        assert f'digit{i}.png' in names
