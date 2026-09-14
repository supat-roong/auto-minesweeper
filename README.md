# minesweeper-video-generator

Generates MP4 videos of an AI solver playing Minesweeper on a configurable
board. The board is rendered with a classic Windows-XP look, complete with an
animated cursor moving between cells. Output videos are silent — there is no
audio stream of any kind.

## Pipeline

```
config.toml + CLI flags
        │
        ▼
    config.py ──► board.py ──► solver_bridge.py ──► vendor/minesweeper_solver
                     │               │
                     └───────┬───────┘
                             ▼
                      recorder.py (Playwright drives web/board.html)
                             │ PNG frames per game
                             ▼
                      assembler.py (ffmpeg)
                             │
                             ▼
                  output/<name>.mp4   (silent)
```

`generator.py` orchestrates the above: for each of `games`, it records frames
and encodes a per-game MP4 in `tmp/`; if more than one game was requested, the
per-game clips are concatenated; the result is moved to `output/<name>.mp4`.

## Requirements

| Requirement | Notes |
|---|---|
| Python ≥ 3.10 | 3.10 uses the `tomli` TOML parser fallback; 3.11+ uses stdlib `tomllib`. |
| `ffmpeg` / `ffprobe` on `PATH` | `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Debian/Ubuntu). |
| Playwright Chromium | `playwright install chromium`, once, after installing Python deps. |
| `minesweeper_solver` submodule | Vendored under `vendor/minesweeper_solver`; see Setup below. |

## Setup

```bash
git clone --recurse-submodules https://github.com/supat-roong/minesweeper-video-generator.git
cd minesweeper-video-generator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

If you already have a clone without the submodule populated (or cloned it
without `--recurse-submodules`), run:

```bash
git submodule update --init
```

## Usage

```bash
python main.py                                          # config.toml defaults
python main.py --rows 16 --cols 30 --mines 99           # expert board
python main.py --games 5 --output compilation           # 5 games concatenated
python main.py --fps 12 --resolution 1920x1080
python main.py --headless false --seed 42               # watch it, reproducibly
```

`--output` sets the output file's *name*; `--output-dir` sets the directory.
The finished video always lands at `<output_dir>/<name>.mp4`.

## Configuration

Settings come from `config.toml`, with CLI flags overriding whatever the file
specifies. The full default file:

```toml
[board]
rows = 16
cols = 16
mines = 40
first_click_safe = true

[video]
fps = 8
resolution = "1280x720"
output_dir = "output"
headless = true

[overlays]
move_counter = true
game_info_banner = true
probability_heatmap = false

[output]
games = 1
name = "minesweeper"
seed = 0
```

- `board.rows`, `board.cols`, `board.mines` — board dimensions and mine count.
- `board.first_click_safe` — if true, the first reveal never hits a mine (a 3x3
  zone around it is reserved as safe).
- `video.fps` — frames per second of the encoded video.
- `video.resolution` — browser viewport size as `WIDTHxHEIGHT`; also the
  output video's dimensions.
- `video.output_dir` — directory the finished MP4 is written to.
- `video.headless` — whether Playwright runs Chromium headless.
- `overlays.move_counter` — show a move counter overlay on the board.
- `overlays.game_info_banner` — show a banner with game info (e.g. game number).
- `overlays.probability_heatmap` — tint cells by the solver's mine probability.
- `output.games` — number of games to record; if more than one, the resulting
  clips are concatenated into a single video.
- `output.name` — output file name, without the `.mp4` extension.
- `output.seed` — base RNG seed; game *i* uses `seed + i`.

Every one of these has a corresponding CLI flag (`--rows`, `--cols`, `--mines`,
`--first-click-safe`, `--fps`, `--resolution`, `--output-dir`, `--headless`,
`--move-counter`, `--game-info-banner`, `--probability-heatmap`, `--games`,
`--output`, `--seed`), plus `--config PATH` to point at a different TOML file.
Run `python main.py --help` for the full list.

## Testing

```bash
pytest -m "not integration" -v   # fast suite — what CI runs; needs the solver submodule, but not ffmpeg or Playwright
pytest                            # full suite — needs ffmpeg, Playwright Chromium, and the submodule checked out
```

## Project layout

```
minesweeper-video-generator/
├── .github/workflows/ci.yml
├── .gitmodules
├── .gitignore
├── LICENSE                          MIT
├── README.md
├── config.toml
├── main.py                          CLI entry point
├── pyproject.toml                   pytest config
├── requirements.txt
├── vendor/
│   └── minesweeper_solver/          git submodule (see Setup)
├── web/
│   ├── board.html                   WinXP-styled board page
│   └── assets/minesweeper/*.png     30 sprite files
├── src/
│   └── minesweeper_video/
│       ├── __init__.py
│       ├── config.py
│       ├── board.py
│       ├── solver_bridge.py
│       ├── recorder.py
│       ├── assembler.py
│       ├── types.py
│       └── generator.py
└── tests/
    ├── __init__.py
    ├── conftest.py                  skips solver-dependent modules if submodule absent
    ├── test_board.py
    ├── test_board_html.py
    ├── test_config.py
    ├── test_assembler.py
    ├── test_generator.py
    ├── test_main.py
    ├── test_recorder.py
    ├── test_recorder_types.py
    └── test_solver_bridge.py
```

## Credits

The Minesweeper-solving logic is vendored as the
[`minesweeper_solver`](https://github.com/supat-roong/minesweeper_solver) git
submodule (MIT, same author). The Windows-XP-styled sprite assets in
`web/assets/minesweeper/` come from
[`ShizukuIchi/winXP`](https://github.com/ShizukuIchi/winXP) (MIT).

## License

MIT — see [`LICENSE`](LICENSE).
