import asyncio
import pytest
from pathlib import Path
from minesweeper_video.config import Config, VideoConfig, OutputConfig
from minesweeper_video.generator import generate
from minesweeper_video.types import RecordResult


def _cfg(tmp_path, games=1, name="out", seed=0):
    return Config(
        video=VideoConfig(output_dir=str(tmp_path / "output")),
        output=OutputConfig(games=games, name=name, seed=seed),
    )


def _fakes(fail_on=()):
    """record_fn/encode_fn/concat_fn that touch files instead of shelling out.
    `fail_on` is a set of game indices whose recording raises."""
    calls = {'record': [], 'encode': [], 'concat': []}

    async def record_fn(config, seed, frames_dir):
        idx = len(calls['record'])
        calls['record'].append(seed)
        if idx in fail_on:
            raise RuntimeError(f"boom on game {idx}")
        return RecordResult(frames=[], won=True, lost=False, moves=1)

    def encode_fn(frames_dir, fps, out_path):
        calls['encode'].append(out_path)
        Path(out_path).write_bytes(b"clip")
        return Path(out_path)

    def concat_fn(clips, out_path):
        calls['concat'].append(list(clips))
        Path(out_path).write_bytes(b"joined")
        return Path(out_path)

    return record_fn, encode_fn, concat_fn, calls


def test_single_game_skips_concat(tmp_path):
    r, e, c, calls = _fakes()
    out = asyncio.run(generate(_cfg(tmp_path, games=1),
                               record_fn=r, encode_fn=e, concat_fn=c))
    assert out.name == "out.mp4"
    assert out.exists()
    assert calls['concat'] == []
    assert len(calls['record']) == 1


def test_multiple_games_are_concatenated(tmp_path):
    r, e, c, calls = _fakes()
    out = asyncio.run(generate(_cfg(tmp_path, games=3),
                               record_fn=r, encode_fn=e, concat_fn=c))
    assert out.exists()
    assert len(calls['record']) == 3
    assert len(calls['concat']) == 1
    assert len(calls['concat'][0]) == 3


def test_seeds_increment_from_base(tmp_path):
    r, e, c, calls = _fakes()
    asyncio.run(generate(_cfg(tmp_path, games=3, seed=100),
                         record_fn=r, encode_fn=e, concat_fn=c))
    assert calls['record'] == [100, 101, 102]


def test_failing_game_is_skipped(tmp_path):
    r, e, c, calls = _fakes(fail_on={1})
    out = asyncio.run(generate(_cfg(tmp_path, games=3),
                               record_fn=r, encode_fn=e, concat_fn=c))
    assert out.exists()
    assert len(calls['record']) == 3      # all attempted
    assert len(calls['encode']) == 2      # only successes encoded
    assert len(calls['concat'][0]) == 2


def test_all_games_failing_raises(tmp_path):
    r, e, c, _ = _fakes(fail_on={0, 1})
    with pytest.raises(RuntimeError, match="No games recorded"):
        asyncio.run(generate(_cfg(tmp_path, games=2),
                             record_fn=r, encode_fn=e, concat_fn=c))


def test_output_directory_is_created(tmp_path):
    r, e, c, _ = _fakes()
    target = tmp_path / "deep" / "nested"
    cfg = Config(video=VideoConfig(output_dir=str(target)),
                 output=OutputConfig(games=1, name="v"))
    out = asyncio.run(generate(cfg, record_fn=r, encode_fn=e, concat_fn=c))
    assert out == target / "v.mp4"
    assert out.exists()


def test_single_game_clip_not_left_behind(tmp_path):
    r, e, c, calls = _fakes()
    out = asyncio.run(generate(_cfg(tmp_path, games=1),
                               record_fn=r, encode_fn=e, concat_fn=c))
    assert out.exists()
    assert not Path(calls['encode'][0]).exists()


def test_multi_game_clips_not_left_behind_after_concat(tmp_path):
    r, e, c, calls = _fakes()
    out = asyncio.run(generate(_cfg(tmp_path, games=3),
                               record_fn=r, encode_fn=e, concat_fn=c))
    assert out.exists()
    for clip_path in calls['encode']:
        assert not Path(clip_path).exists()


def test_rerun_overwrites_previous_output(tmp_path):
    r, e, c, _ = _fakes()
    cfg = _cfg(tmp_path, games=1)
    first = asyncio.run(generate(cfg, record_fn=r, encode_fn=e, concat_fn=c))
    r2, e2, c2, _ = _fakes()
    second = asyncio.run(generate(cfg, record_fn=r2, encode_fn=e2, concat_fn=c2))
    assert first == second
    assert second.exists()
