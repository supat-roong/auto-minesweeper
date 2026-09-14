from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class RecordResult:
    """Outcome of recording a single game."""
    frames: List[Path]
    won: bool
    lost: bool
    moves: int
    move_frames: List[int] = field(default_factory=list)
