import argparse
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python 3.10
    import tomli as tomllib

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class BoardConfig:
    rows: int = 16
    cols: int = 16
    mines: int = 40
    first_click_safe: bool = True


@dataclass
class VideoConfig:
    fps: int = 8
    resolution: str = "1280x720"
    output_dir: str = "output"
    headless: bool = True


@dataclass
class OverlayConfig:
    move_counter: bool = True
    game_info_banner: bool = True
    probability_heatmap: bool = False


@dataclass
class OutputConfig:
    games: int = 1
    name: str = "minesweeper"
    seed: int = 0


@dataclass
class Config:
    board: BoardConfig = field(default_factory=BoardConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    overlays: OverlayConfig = field(default_factory=OverlayConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


def load_config(path: Path = None) -> Config:
    if path is None:
        path = REPO_ROOT / 'config.toml'
    if not Path(path).exists():
        return Config()
    with open(path, 'rb') as f:
        data = tomllib.load(f)
    return Config(
        board=BoardConfig(**data.get('board', {})),
        video=VideoConfig(**data.get('video', {})),
        overlays=OverlayConfig(**data.get('overlays', {})),
        output=OutputConfig(**data.get('output', {})),
    )


def parse_resolution(resolution: str) -> tuple:
    """Parse "WIDTHxHEIGHT" into (width, height). Raises ValueError if malformed."""
    parts = str(resolution).lower().split('x')
    if len(parts) != 2:
        raise ValueError(f"video.resolution must look like WIDTHxHEIGHT, got {resolution!r}")
    try:
        w, h = int(parts[0]), int(parts[1])
    except ValueError:
        raise ValueError(f"video.resolution must look like WIDTHxHEIGHT, got {resolution!r}")
    if w <= 0 or h <= 0:
        raise ValueError(f"video.resolution must be positive, got {resolution!r}")
    return w, h


def validate(config: Config) -> None:
    """Reject impossible settings before anything expensive (browser, ffmpeg) starts."""
    parse_resolution(config.video.resolution)
    if config.video.fps <= 0:
        raise ValueError(f"video.fps must be positive, got {config.video.fps}")
    if config.output.games <= 0:
        raise ValueError(f"output.games must be positive, got {config.output.games}")
    if config.board.rows <= 0:
        raise ValueError(f"board.rows must be positive, got {config.board.rows}")
    if config.board.cols <= 0:
        raise ValueError(f"board.cols must be positive, got {config.board.cols}")
    safe_zone = 9 if config.board.first_click_safe else 1
    max_mines = config.board.rows * config.board.cols - safe_zone
    if config.board.mines <= 0:
        raise ValueError(f"board.mines must be positive, got {config.board.mines}")
    if config.board.mines >= max_mines:
        raise ValueError(
            f"board.mines too high: {config.board.mines} for "
            f"{config.board.rows}x{config.board.cols} (max {max_mines})")


def _bool(value: str) -> bool:
    return value == 'true'


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='auto-minesweeper',
        description='Generate a video of an AI solver playing Minesweeper')
    p.add_argument('--config', type=Path, default=None, help='path to a TOML config')

    b = p.add_argument_group('board')
    b.add_argument('--rows', type=int)
    b.add_argument('--cols', type=int)
    b.add_argument('--mines', type=int)
    b.add_argument('--first-click-safe', choices=['true', 'false'])

    v = p.add_argument_group('video')
    v.add_argument('--fps', type=int)
    v.add_argument('--resolution', help='browser viewport, WIDTHxHEIGHT')
    v.add_argument('--output-dir')
    v.add_argument('--headless', choices=['true', 'false'])

    o = p.add_argument_group('overlays')
    o.add_argument('--move-counter', choices=['true', 'false'])
    o.add_argument('--game-info-banner', choices=['true', 'false'])
    o.add_argument('--probability-heatmap', choices=['true', 'false'])

    out = p.add_argument_group('output')
    out.add_argument('--games', type=int, help='number of games to record and concatenate')
    out.add_argument('--output', dest='name', help='output file name (without .mp4)')
    out.add_argument('--seed', type=int, help='base RNG seed; game i uses seed + i')
    return p


# (section, dataclass field, argparse dest, coercion)
_OVERRIDES = [
    ('board', 'rows', 'rows', None),
    ('board', 'cols', 'cols', None),
    ('board', 'mines', 'mines', None),
    ('board', 'first_click_safe', 'first_click_safe', _bool),
    ('video', 'fps', 'fps', None),
    ('video', 'resolution', 'resolution', None),
    ('video', 'output_dir', 'output_dir', None),
    ('video', 'headless', 'headless', _bool),
    ('overlays', 'move_counter', 'move_counter', _bool),
    ('overlays', 'game_info_banner', 'game_info_banner', _bool),
    ('overlays', 'probability_heatmap', 'probability_heatmap', _bool),
    ('output', 'games', 'games', None),
    ('output', 'name', 'name', None),
    ('output', 'seed', 'seed', None),
]


def apply_overrides(config: Config, args: argparse.Namespace) -> Config:
    """Apply any CLI flag that was actually supplied. Absent flags are None and
    leave the TOML/default value alone."""
    for section, attr, dest, coerce in _OVERRIDES:
        value = getattr(args, dest, None)
        if value is None:
            continue
        setattr(getattr(config, section), attr, coerce(value) if coerce else value)
    return config


def build_config(argv: list = None) -> Config:
    args = build_parser().parse_args(argv)
    config = apply_overrides(load_config(args.config), args)
    validate(config)
    return config
