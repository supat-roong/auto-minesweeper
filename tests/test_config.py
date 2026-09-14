import pytest
from minesweeper_video.config import (
    Config, BoardConfig, VideoConfig, OverlayConfig, OutputConfig,
    load_config, build_config, validate,
)

TOML = """
[board]
rows = 10
cols = 12
mines = 15
first_click_safe = false

[video]
fps = 20
resolution = "800x600"
output_dir = "vids"
headless = false

[overlays]
move_counter = false
game_info_banner = false
probability_heatmap = true

[output]
games = 4
name = "custom"
seed = 7
"""


def _toml(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text(TOML)
    return p


def test_defaults_when_no_file(tmp_path):
    cfg = load_config(tmp_path / "missing.toml")
    assert cfg.board.rows == 16
    assert cfg.board.cols == 16
    assert cfg.board.mines == 40
    assert cfg.board.first_click_safe is True
    assert cfg.video.fps == 8
    assert cfg.video.resolution == "1280x720"
    assert cfg.video.output_dir == "output"
    assert cfg.video.headless is True
    assert cfg.output.games == 1
    assert cfg.output.name == "minesweeper"
    assert cfg.output.seed == 0


def test_toml_overrides_defaults(tmp_path):
    cfg = load_config(_toml(tmp_path))
    assert cfg.board.rows == 10
    assert cfg.board.mines == 15
    assert cfg.board.first_click_safe is False
    assert cfg.video.fps == 20
    assert cfg.video.headless is False
    assert cfg.overlays.probability_heatmap is True
    assert cfg.output.games == 4
    assert cfg.output.name == "custom"
    assert cfg.output.seed == 7


def test_cli_overrides_toml(tmp_path):
    cfg = build_config([
        "--config", str(_toml(tmp_path)),
        "--rows", "16", "--cols", "30", "--mines", "99",
        "--fps", "12", "--games", "2", "--output", "cli", "--seed", "99",
    ])
    assert (cfg.board.rows, cfg.board.cols, cfg.board.mines) == (16, 30, 99)
    assert cfg.video.fps == 12
    assert cfg.output.games == 2
    assert cfg.output.name == "cli"
    assert cfg.output.seed == 99
    # untouched keys still come from the TOML
    assert cfg.video.resolution == "800x600"
    assert cfg.video.output_dir == "vids"


def test_cli_boolean_flags(tmp_path):
    cfg = build_config(["--config", str(_toml(tmp_path)),
                        "--headless", "true", "--first-click-safe", "true",
                        "--probability-heatmap", "false"])
    assert cfg.video.headless is True
    assert cfg.board.first_click_safe is True
    assert cfg.overlays.probability_heatmap is False


def test_cli_absent_leaves_toml_untouched(tmp_path):
    cfg = build_config(["--config", str(_toml(tmp_path))])
    assert cfg.video.headless is False
    assert cfg.board.rows == 10


@pytest.mark.parametrize("resolution", ["1280", "1280*720", "axb", "1280x", ""])
def test_validate_rejects_bad_resolution(resolution):
    cfg = Config(video=VideoConfig(resolution=resolution))
    with pytest.raises(ValueError, match="resolution"):
        validate(cfg)


def test_validate_accepts_good_resolution():
    validate(Config(video=VideoConfig(resolution="1920x1080")))


@pytest.mark.parametrize("field,value", [
    ("fps", 0), ("fps", -1),
])
def test_validate_rejects_nonpositive_video_fields(field, value):
    cfg = Config(video=VideoConfig(**{field: value}))
    with pytest.raises(ValueError, match=field):
        validate(cfg)


def test_validate_rejects_nonpositive_games():
    with pytest.raises(ValueError, match="games"):
        validate(Config(output=OutputConfig(games=0)))


@pytest.mark.parametrize("field", ["rows", "cols"])
def test_validate_rejects_nonpositive_board_dims(field):
    cfg = Config(board=BoardConfig(**{field: 0}))
    with pytest.raises(ValueError, match=field):
        validate(cfg)


def test_validate_rejects_impossible_mine_count():
    # 9x9 with first_click_safe reserves 9 cells -> max 71 mines
    cfg = Config(board=BoardConfig(rows=9, cols=9, mines=72))
    with pytest.raises(ValueError, match="mines"):
        validate(cfg)


def test_validate_allows_dense_board_without_first_click_safe():
    validate(Config(board=BoardConfig(rows=9, cols=9, mines=72, first_click_safe=False)))


def test_build_config_validates():
    with pytest.raises(ValueError, match="mines"):
        build_config(["--rows", "9", "--cols", "9", "--mines", "500"])
