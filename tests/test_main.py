import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main as cli


def test_invalid_config_exits_nonzero_without_traceback(capsys):
    code = cli.main(["--rows", "9", "--cols", "9", "--mines", "500"])
    assert code == 2
    err = capsys.readouterr().err
    assert "mines" in err
    assert "Traceback" not in err


def test_bad_resolution_exits_nonzero(capsys):
    code = cli.main(["--resolution", "wide"])
    assert code == 2
    assert "resolution" in capsys.readouterr().err


def test_main_invokes_generate_with_overridden_config(monkeypatch, tmp_path):
    seen = {}

    def fake_run(config):
        seen['config'] = config
        return tmp_path / "fake.mp4"

    monkeypatch.setattr(cli, '_run', fake_run)
    code = cli.main(["--rows", "16", "--cols", "30", "--mines", "99",
                     "--games", "2", "--output", "expert",
                     "--output-dir", str(tmp_path)])
    assert code == 0
    cfg = seen['config']
    assert (cfg.board.rows, cfg.board.cols, cfg.board.mines) == (16, 30, 99)
    assert cfg.output.games == 2
    assert cfg.output.name == "expert"


def test_help_lists_every_flag(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    out = capsys.readouterr().out
    for flag in ('--rows', '--cols', '--mines', '--first-click-safe',
                 '--fps', '--resolution', '--output-dir', '--headless',
                 '--move-counter', '--game-info-banner', '--probability-heatmap',
                 '--games', '--output', '--seed', '--config'):
        assert flag in out
