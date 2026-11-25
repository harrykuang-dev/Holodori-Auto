"""Read a solo match, choose moves, and verify each click against the next frame."""

from collections import Counter
import time

from solver import BLUE, ORANGE, NAMES, full_inventory, moves, recommend, solve, square, table_code, terminal
from stages import CHALLENGES, CLICK, classify_screen
from vision import (VisionError, hand_read, highlighted, is_ready, match_position,
                    our_turn, point, read_position, selected_piece, source_arrow)


class StopPlay(RuntimeError):
    pass


def hands_match(frame, pos):
    return all(Counter(p for _, _, p in hand_read(frame, side)) == Counter(pos.hand(side))
               for side in (BLUE, ORANGE))


def next_player_position(frame, pos, move):
    if not is_ready(frame):
        raise VisionError("等待我方回合")
    after = pos.next(move)
    candidates = [after.next(reply) for reply in moves(after)]
    candidates = [candidate for candidate in candidates
                  if terminal(candidate) is None and hands_match(frame, candidate)]
    return match_position(frame, candidates)


def source_point(frame, pos, move):
    if move.source >= 0:
        return point(move.source)
    capture_icons = hand_read(frame, BLUE)
    candidates = [(x, y) for x, y, p in capture_icons if p == -move.source]
    if not hands_match(frame, pos) or not candidates:
        raise StopPlay("无法确认部署用的候补图标")
    return candidates[0]


def selection_ready(frame, pos, move):
    piece = abs(pos.board[move.source]) if move.source >= 0 else -move.source
    return (our_turn(frame) and not is_ready(frame) and selected_piece(frame, piece)
            and (move.source < 0 or source_arrow(frame, move.source))
            and highlighted(frame, move.target))


def choose(pos, history, notify):
    if full_inventory(pos):
        try:
            result, depth, ties, _ = recommend(pos, history, seconds=.5, online=True)
        except (OSError, TypeError, ValueError, KeyError):
            result, depth, ties = solve(pos, history, seconds=4)
    else:
        result, depth, ties = solve(pos, history, seconds=4)
    if not ties:
        raise StopPlay(f"尚無可證明的最佳走法，已停止落子 ({table_code(pos)})")
    labels = "、".join(m.label() for m in ties)
    notify("move", labels, result, depth)
    return ties[0]


def wait_for(game, read, seconds):
    start = time.monotonic()
    last = None
    error = "画面尚未就绪"
    while time.monotonic() - start < seconds:
        frame = game.capture()
        try:
            answer = read(frame)
            if answer is not None and answer == last:
                return frame, answer
            last = answer
        except VisionError as reason:
            last = None
            error = str(reason)
        time.sleep(.14)
    raise StopPlay(error)


def wait_menu(game, allowed, seconds=30):
    def read(frame):
        state = classify_screen(frame)
        if state in allowed:
            return state
        if state == "non_win":
            raise StopPlay("游戏结算为未获胜，停止推进")
        raise VisionError(f"等待下一界面，当前为 {state or '未识别'}")

    return wait_for(game, read, seconds)[1]


def prepare(game, notify):
    entries = {"hub", "level_next", *CHALLENGES}
    allowed = {"tutorial", "board", "team_auto", "team_start", *entries}
    while True:
        state = wait_menu(game, allowed, 50)
        if state == "board":
            return wait_for(game, read_position, 8)
        game.click(*CLICK[state])
        allowed.remove(state)
        if state in (*CHALLENGES, 'tutorial', 'team_auto', 'team_start'):
            allowed -= entries
        if state == 'team_start':
            allowed.discard('team_auto')
        if state in CHALLENGES:
            notify("challenge")


def settle(game, outcome):
    menus = {"level_menu", "level_next", "hub", *CHALLENGES}
    allowed = {"tutorial", "win", "win_details", "reward", *menus}
    actual_win = False
    state = outcome
    while True:
        if state in menus:
            if not actual_win:
                raise StopPlay("离开对局前未观察到胜利结算")
            return
        if state in {"win", "win_details"}:
            actual_win = True
        game.click(*CLICK[state])
        allowed.remove(state)
        state = wait_menu(game, allowed)


def play_match(game, frame, pos, notify):
    history = []
    for _ in range(90):
        move = choose(pos, history, notify)
        # Revalidate after solving. The game may have lost focus or changed in the meantime.
        def unchanged(new_frame):
            if read_position(new_frame) != pos:
                raise StopPlay("求解期间棋盘已变化")
            return pos

        frame, _ = wait_for(game, unchanged, 4)
        game.click(*source_point(frame, pos, move))
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            frame = game.capture()
            if selection_ready(frame, pos, move):
                break
            time.sleep(.10)
        else:
            raise StopPlay(f"无法确认 {move.label()} 的选中标记和合法落点")
        game.click(*point(move.target, selected=True))
        after = pos.next(move)
        history.extend((pos, after))

        def read_next(new_frame):
            scene = classify_screen(new_frame)
            if scene in {"win", "win_details", "tutorial"}:
                return scene
            if scene == "non_win":
                raise StopPlay("游戏结算为未获胜，停止推进")
            # Do not accept the old board or end-of-turn animation as the opponent's response.
            if after.turn not in after.board:
                return None
            return next_player_position(new_frame, pos, move)

        frame, reply = wait_for(game, read_next, 32)
        if isinstance(reply, str):
            return reply
        old = pos
        pos = reply
        changes = [f"{square(i)}={NAMES[abs(p)] or '空'}" for i, p in enumerate(pos.board)
                   if p != after.board[i]]
        notify("reply", move.label(), "，".join(changes))
        if pos == old and history.count(pos) >= 2:
            raise StopPlay("局面已重复，等待游戏结算")
    raise StopPlay("达到本次运行的回合上限")


def run(game, rounds, notify):
    for number in range(1, rounds + 1):
        frame, pos = prepare(game, notify)
        result = play_match(game, frame, pos, notify)
        settle(game, result)
        notify("completed", number, rounds)
