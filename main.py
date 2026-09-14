#!/usr/bin/env python3
"""Generate a video of an AI solver playing Minesweeper."""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))

from minesweeper_video.config import build_config    # noqa: E402
from minesweeper_video.generator import run as _run  # noqa: E402


def main(argv: list = None) -> int:
    try:
        config = build_config(argv)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
    result = _run(config)
    print(f"Done: {result}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
