import asyncio
import json
import math
import random
from pathlib import Path
from playwright.async_api import async_playwright
from minesweeper_video.board import Board
from minesweeper_video.solver_bridge import SolverBridge
from minesweeper_video.config import Config, REPO_ROOT, parse_resolution
from minesweeper_video.types import RecordResult


def _cell_target(row, col, cs):
    """Cell centre with a small random human-like offset (within ±28 % of cell size)."""
    off = cs * 0.28
    return (
        (col + 0.5) * cs + random.uniform(-off, off),
        (row + 0.5) * cs + random.uniform(-off, off),
    )


def _bezier_pts(p0, p2, n):
    """Quadratic bezier from p0→p2 with a random perpendicular control point, n steps,
    smoothstep easing — gives a natural curved arc."""
    mx, my = (p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2
    dx, dy = p2[0] - p0[0], p2[1] - p0[1]
    dist = math.sqrt(dx * dx + dy * dy) or 1
    px, py = -dy / dist, dx / dist          # perpendicular unit vector
    cp_off = random.uniform(-dist * 0.3, dist * 0.3)
    cp = (mx + px * cp_off, my + py * cp_off)
    pts = []
    for i in range(1, n + 1):
        t = i / n
        te = t * t * (3 - 2 * t)            # smoothstep
        bx = (1-te)**2*p0[0] + 2*(1-te)*te*cp[0] + te**2*p2[0]
        by = (1-te)**2*p0[1] + 2*(1-te)*te*cp[1] + te**2*p2[1]
        pts.append((bx, by))
    return pts



async def record_game(config: Config, seed: int = None, frames_dir: Path = None) -> RecordResult:
    """Record one full Minesweeper game, board only (no dashboard). Returns a RecordResult
    with frames, won, lost, moves and move_frames (the frame index where each move shows)."""
    bc = config.board
    vc = config.video
    oc = config.overlays

    board = Board(bc.rows, bc.cols, bc.mines, bc.first_click_safe, seed)
    bridge = SolverBridge(board)

    w, h = parse_resolution(vc.resolution)
    frame_delay = 1.0 / vc.fps
    frame_paths = []
    idx = 0
    board_html = (REPO_ROOT / 'web' / 'board.html').resolve()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=vc.headless)
        page = await browser.new_page(viewport={'width': w, 'height': h})
        await page.goto(board_html.as_uri())

        await page.evaluate(f"window.BOARD.init({bc.rows},{bc.cols})")
        await page.evaluate(f"window.BOARD.setCounter({bc.mines})")
        await page.evaluate(f"window.BOARD.setGameInfo({{rows:{bc.rows},cols:{bc.cols},mines:{bc.mines}}})")
        overlay_js = json.dumps({
            'move_counter': oc.move_counter,
            'game_info_banner': oc.game_info_banner,
            'probability_heatmap': oc.probability_heatmap,
        })
        await page.evaluate(f"window.BOARD.setOverlay({overlay_js})")

        board_moves = 0
        move_frames = []

        # Capture initial state
        frame_paths.append(await _snap(page, frames_dir, idx)); idx += 1

        timer_start_idx = None
        cs_val = await page.evaluate("CS")
        # Start cursor slightly above the centre of the board (enters from off-screen)
        cursor_pos = [bc.cols * cs_val * 0.5, -cs_val * 0.8]

        anim_delay = max(0.03, frame_delay * 0.45)

        while not board.is_won and not board.is_lost:
            cursor_cell = (cursor_pos[1] / cs_val, cursor_pos[0] / cs_val)
            move = bridge.get_next_move(cursor_cell=cursor_cell)
            if not move or move.action == 'none':
                break

            if timer_start_idx is None:
                timer_start_idx = idx

            # Animate cursor from current position to target cell via bezier arc.
            # Number of steps scales with travel distance: ~1 frame per cell-width.
            target = _cell_target(move.row, move.col, cs_val)
            dist = math.sqrt(
                (target[0] - cursor_pos[0]) ** 2 + (target[1] - cursor_pos[1]) ** 2
            )
            anim_n = max(1, min(8, round(dist / cs_val)))
            pts = _bezier_pts(tuple(cursor_pos), target, anim_n)

            # Intermediate frames — cursor moving, timer ticks every frame
            for pt in pts[:-1]:
                await page.evaluate(
                    f"window.BOARD.setCursorAt({pt[0]:.1f},{pt[1]:.1f},false)"
                )
                await asyncio.sleep(anim_delay)
                await page.evaluate(
                    f"window.BOARD.setTimer({min(999,(idx-timer_start_idx)//vc.fps)})"
                )
                frame_paths.append(await _snap(page, frames_dir, idx)); idx += 1

            # Cursor arrives at destination
            dest = pts[-1]
            await page.evaluate(
                f"window.BOARD.setCursorAt({dest[0]:.1f},{dest[1]:.1f},false)"
            )
            cursor_pos = list(dest)

            # Execute action with deliberate press → wait → show → wait rhythm
            if move.action == 'flag':
                board.flag(move.row, move.col)
                await page.evaluate(f"window.BOARD.flag({move.row},{move.col})")
                await page.evaluate(f"window.BOARD.setCounter({board.remaining_mines})")
                board_moves += 1
                move_frames.append(idx)
                await asyncio.sleep(frame_delay)
                await page.evaluate(
                    f"window.BOARD.setTimer({min(999,(idx-timer_start_idx)//vc.fps)})"
                )
                frame_paths.append(await _snap(page, frames_dir, idx)); idx += 1

            elif move.action == 'click':
                # Press — show ohh face + sunken cell
                await page.evaluate(f"window.BOARD.pressMouse({move.row},{move.col})")
                await asyncio.sleep(frame_delay * 0.6)
                await page.evaluate(
                    f"window.BOARD.setTimer({min(999,(idx-timer_start_idx)//vc.fps)})"
                )
                frame_paths.append(await _snap(page, frames_dir, idx)); idx += 1

                # Reveal — show the result
                result = board.reveal(move.row, move.col)
                if result.hit_mine:
                    await page.evaluate(f"window.BOARD.explode({move.row},{move.col})")
                    mine_list = [[r, c] for r, c in board.mine_positions]
                    await page.evaluate(f"window.BOARD.showAllMines({json.dumps(mine_list)})")
                else:
                    await page.evaluate("window.BOARD.releaseMouse()")
                    for r, c, v in result.revealed:
                        await page.evaluate(f"window.BOARD.reveal({r},{c},{v})")

                board_moves += 1
                move_frames.append(idx)

                # Wait to show what was revealed before starting next move
                await asyncio.sleep(frame_delay * 1.2)
                await page.evaluate(
                    f"window.BOARD.setTimer({min(999,(idx-timer_start_idx)//vc.fps)})"
                )
                frame_paths.append(await _snap(page, frames_dir, idx)); idx += 1

            if oc.probability_heatmap and bridge.mine_probabilities is not None:
                prob = bridge.mine_probabilities.tolist()
                await page.evaluate(f"window.BOARD.setProbability({json.dumps(prob)})")

        # Final state — match WinXP behaviour
        if board.is_won:
            mine_list = [[r, c] for r, c in board.mine_positions]
            await page.evaluate(f"window.BOARD.autoFlagMines({json.dumps(mine_list)})")
            await page.evaluate("window.BOARD.win()")
            await page.evaluate("window.BOARD.setCounter(0)")
            if timer_start_idx is not None:
                timer_val = min(999, (idx - timer_start_idx) // vc.fps)
                await page.evaluate(f"window.BOARD.setTimer({timer_val})")
            await page.evaluate("window.BOARD.setCursor(null, null)")
        elif board.is_lost:
            await page.evaluate("window.BOARD.lose()")
            await page.evaluate("window.BOARD.setCursor(null, null)")
        # else: solver gave up without win or loss

        await asyncio.sleep(frame_delay * 2)
        for _ in range(3):
            frame_paths.append(await _snap(page, frames_dir, idx)); idx += 1

        await browser.close()

    return RecordResult(
        frames=frame_paths,
        won=board.is_won,
        lost=board.is_lost,
        moves=board_moves,
        move_frames=move_frames,
    )


async def _snap(page, frames_dir: Path, idx: int) -> Path:
    path = frames_dir / f"frame_{idx:04d}.png"
    await page.screenshot(path=str(path))
    return path
