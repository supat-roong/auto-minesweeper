import asyncio
import pytest
from PIL import Image
from minesweeper_video.config import Config, BoardConfig, VideoConfig, OverlayConfig
from minesweeper_video.recorder import record_game

pytestmark = pytest.mark.integration  # requires Playwright browsers + the solver submodule


def _cfg(overlays=None):
    return Config(
        board=BoardConfig(rows=9, cols=9, mines=10, first_click_safe=True),
        video=VideoConfig(fps=4, resolution="640x480", headless=True),
        overlays=overlays or OverlayConfig(move_counter=False, game_info_banner=False,
                                           probability_heatmap=False),
    )


def test_record_game_produces_png_frames(tmp_path):
    frames_dir = tmp_path / "frames"; frames_dir.mkdir()
    result = asyncio.run(record_game(_cfg(), seed=42, frames_dir=frames_dir))
    assert len(result.frames) > 1
    assert all(f.exists() for f in result.frames)
    assert all(f.suffix == '.png' for f in result.frames)
    assert result.won or result.lost


def test_frames_match_configured_resolution(tmp_path):
    frames_dir = tmp_path / "frames"; frames_dir.mkdir()
    result = asyncio.run(record_game(_cfg(), seed=42, frames_dir=frames_dir))
    assert Image.open(result.frames[0]).size == (640, 480)


def test_record_game_with_overlays(tmp_path):
    cfg = _cfg(overlays=OverlayConfig(move_counter=True, game_info_banner=True,
                                      probability_heatmap=False))
    frames_dir = tmp_path / "frames"; frames_dir.mkdir()
    result = asyncio.run(record_game(cfg, seed=42, frames_dir=frames_dir))
    assert len(result.frames) > 0


def test_record_game_with_probability_heatmap(tmp_path):
    cfg = _cfg(overlays=OverlayConfig(move_counter=False, game_info_banner=False,
                                      probability_heatmap=True))
    frames_dir = tmp_path / "frames"; frames_dir.mkdir()
    result = asyncio.run(record_game(cfg, seed=42, frames_dir=frames_dir))
    assert len(result.frames) > 0


def test_record_game_records_move_frames(tmp_path):
    frames_dir = tmp_path / "frames"; frames_dir.mkdir()
    result = asyncio.run(record_game(_cfg(), seed=42, frames_dir=frames_dir))
    assert result.moves == len(result.move_frames)
    assert result.moves >= 1
    assert result.move_frames == sorted(result.move_frames)
    assert result.move_frames[-1] < len(result.frames)


def test_same_seed_gives_same_outcome(tmp_path):
    a_dir = tmp_path / "a"; a_dir.mkdir()
    b_dir = tmp_path / "b"; b_dir.mkdir()
    a = asyncio.run(record_game(_cfg(), seed=7, frames_dir=a_dir))
    b = asyncio.run(record_game(_cfg(), seed=7, frames_dir=b_dir))
    assert a.won == b.won and a.lost == b.lost
