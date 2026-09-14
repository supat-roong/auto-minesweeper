import asyncio
import logging
import shutil
from pathlib import Path

from minesweeper_video.assembler import concat_videos, frames_to_video
from minesweeper_video.config import Config, REPO_ROOT, load_config

log = logging.getLogger(__name__)


def _fresh(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


async def generate(config: Config, *, record_fn=None, encode_fn=None, concat_fn=None) -> Path:
    """Record `config.output.games` games and produce one silent MP4.

    The *_fn hooks default to the real recorder/ffmpeg implementations; tests
    inject fakes so the orchestration can be checked without a browser.
    """
    if record_fn is None:
        from minesweeper_video.recorder import record_game   # lazy: Playwright + solver
        record_fn = record_game
    encode_fn = encode_fn or frames_to_video
    concat_fn = concat_fn or concat_videos

    output_dir = Path(config.video.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    tmp_dir = REPO_ROOT / 'tmp'
    tmp_dir.mkdir(parents=True, exist_ok=True)
    final = output_dir / f"{config.output.name}.mp4"

    clips = []
    for i in range(config.output.games):
        log.info("Recording game %d/%d ...", i + 1, config.output.games)
        frames_dir = _fresh(tmp_dir / f'frames_{i}')
        try:
            await record_fn(config, config.output.seed + i, frames_dir)
        except Exception as e:
            log.warning("Game %d failed, skipping: %s", i + 1, e)
            shutil.rmtree(frames_dir, ignore_errors=True)
            continue
        clips.append(encode_fn(frames_dir, config.video.fps, tmp_dir / f'game_{i}.mp4'))
        shutil.rmtree(frames_dir, ignore_errors=True)

    if not clips:
        raise RuntimeError("No games recorded successfully")

    if len(clips) == 1:
        shutil.move(str(clips[0]), str(final))
    else:
        concat_fn(clips, final)

    log.info("Output: %s", final)
    return final


def run(config: Config = None) -> Path:
    if config is None:
        config = load_config()
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    return asyncio.run(generate(config))
