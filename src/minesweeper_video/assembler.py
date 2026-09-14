import subprocess
import tempfile
from pathlib import Path


def frames_to_video(frames_dir: Path, fps: int, output_path: Path) -> Path:
    """Encode a directory of frame_%04d.png files into a silent MP4."""
    cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', str(frames_dir / 'frame_%04d.png'),
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'fast',
        str(output_path),
    ]
    _run(cmd, "frames_to_video")
    return output_path


def concat_videos(video_paths: list, output_path: Path) -> Path:
    """Concatenate MP4 files using the ffmpeg concat demuxer (stream copy)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for p in video_paths:
            f.write(f"file '{Path(p).absolute()}'\n")
        filelist = Path(f.name)
    try:
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', str(filelist),
            '-c', 'copy',
            str(output_path),
        ]
        _run(cmd, "concat_videos")
    finally:
        filelist.unlink(missing_ok=True)
    return output_path


def _run(cmd: list, label: str) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg [{label}] failed:\n{result.stderr[-2000:]}")
