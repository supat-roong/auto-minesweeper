from pathlib import Path
from minesweeper_video.types import RecordResult


def test_record_result_fields():
    r = RecordResult(frames=[Path('a.png')], won=True, lost=False, moves=12,
                     move_frames=[2, 5, 9])
    assert r.frames == [Path('a.png')]
    assert r.won is True
    assert r.lost is False
    assert r.moves == 12
    assert r.move_frames == [2, 5, 9]


def test_record_result_move_frames_defaults_empty():
    r = RecordResult(frames=[], won=False, lost=True, moves=0)
    assert r.move_frames == []


def test_record_result_move_frames_not_shared_between_instances():
    a = RecordResult(frames=[], won=False, lost=False, moves=0)
    b = RecordResult(frames=[], won=False, lost=False, moves=0)
    a.move_frames.append(1)
    assert b.move_frames == []
