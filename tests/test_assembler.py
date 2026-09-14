import subprocess
import pytest
from pathlib import Path
from PIL import Image
import numpy as np
from minesweeper_video.assembler import frames_to_video, concat_videos

pytestmark = pytest.mark.integration  # requires ffmpeg/ffprobe


def make_frames(frames_dir: Path, count: int, w=640, h=480):
    for i in range(count):
        img = Image.fromarray(np.zeros((h, w, 3), dtype=np.uint8))
        img.save(frames_dir / f"frame_{i:04d}.png")


def probe_duration(path: Path) -> float:
    r = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(path)],
        capture_output=True, text=True
    )
    return float(r.stdout.strip())


def test_frames_to_video_creates_mp4(tmp_path):
    fd = tmp_path / "frames"; fd.mkdir()
    make_frames(fd, 8)
    out = tmp_path / "test.mp4"
    result = frames_to_video(fd, fps=4, output_path=out)
    assert result.exists()
    assert result.stat().st_size > 0


def test_frames_to_video_duration(tmp_path):
    fd = tmp_path / "frames"; fd.mkdir()
    make_frames(fd, 8)
    out = tmp_path / "test.mp4"
    frames_to_video(fd, fps=4, output_path=out)
    dur = probe_duration(out)
    assert abs(dur - 2.0) < 0.5  # 8 frames / 4fps = 2s


def test_frames_to_video_has_no_audio_stream(tmp_path):
    fd = tmp_path / "frames"; fd.mkdir()
    make_frames(fd, 8)
    out = tmp_path / "test.mp4"
    frames_to_video(fd, fps=4, output_path=out)
    r = subprocess.run(
        ['ffprobe', '-v', 'error', '-select_streams', 'a',
         '-show_entries', 'stream=index', '-of', 'csv=p=0', str(out)],
        capture_output=True, text=True)
    assert r.stdout.strip() == ""


def test_concat_videos(tmp_path):
    clips = []
    for i in range(3):
        fd = tmp_path / f"frames{i}"; fd.mkdir()
        make_frames(fd, 4)
        clip = tmp_path / f"c{i}.mp4"
        frames_to_video(fd, fps=4, output_path=clip)
        clips.append(clip)
    out = tmp_path / "joined.mp4"
    result = concat_videos(clips, out)
    assert result.exists()
    assert abs(probe_duration(out) - 3.0) < 0.5  # 3 clips x 1s


def test_frames_to_video_raises_on_missing_frames(tmp_path):
    fd = tmp_path / "empty"; fd.mkdir()
    with pytest.raises(RuntimeError, match="frames_to_video"):
        frames_to_video(fd, fps=4, output_path=tmp_path / "x.mp4")
