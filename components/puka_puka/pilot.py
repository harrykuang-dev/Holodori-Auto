"""Read a solo match, choose moves, and verify each click against the next frame."""

from collections import Counter
import time

from solver import BLUE, ORANGE, NAMES, full_inventory, moves, recommend, solve, square, table_code, terminal
from stages import CHALLENGES, CLICK, MENU_STATES, RESULT_STATES, classify_screen
from vision import (VisionError, hand_read, highlighted, is_ready, match_position,
                    point, read_position, selected_piece, source_arrow)


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
    return (not is_ready(frame) and selected_piece(frame, piece)
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


def wait_for(game, read, seconds, *, stable_for=0):
    start = time.monotonic()
    last = None
    first_seen = start
    error = "画面尚未就绪"
    while time.monotonic() - start < seconds:
        frame = game.capture()
        try:
            answer = read(frame)
            now = time.monotonic()
            if answer is not None and answer == last:
                if now - first_seen >= stable_for:
                    return frame, answer
            else:
                first_seen = now
            last = answer
        except VisionError as reason:
            last = None
            error = str(reason)
        time.sleep(.14)
    raise StopPlay(error)


def wait_menu(game, allowed, seconds=30, *, stable_for=0):
    def read(frame):
        state = classify_screen(frame)
        if state in allowed:
            return state
        raise VisionError("未能確認下一個遊戲畫面。")

    return wait_for(game, read, seconds, stable_for=stable_for)[1]


def prepare(game, notify):
    entries = {"hub", "level_next", *CHALLENGES}
    allowed = {"tutorial", "board", "team_auto", "team_start", *entries}
    notify("waiting_entry")
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
            notify("waiting_board")


def settle(game, state, proven_win, notify):
    notify("waiting_result")
    if state == "tutorial":
        game.click(*CLICK[state])
        state = wait_menu(game, RESULT_STATES)
    if state == "result":
        game.click(*CLICK[state])
        state = wait_menu(game, {"result_details", "win_details"})
    if state == "result_details" and not proven_win:
        try:
            state = wait_menu(game, {"win_details"}, 4)
        except StopPlay as error:
            raise StopPlay("未確認獲勝，已停止推進。") from error
    game.click(*CLICK[state])
    # The stage carousel can appear briefly before the reward overlay opens.
    state = wait_menu(game, MENU_STATES | {"reward"}, stable_for=1.2)
    if state == "reward":
        game.click(*CLICK[state])
        wait_menu(game, MENU_STATES, stable_for=1.2)


def confirms_win(after, history):
    outcome = terminal(after)
    if outcome is not None:
        return outcome == -1
    replies = [after.next(move) for move in moves(after)]
    return history.count(after) < 3 and bool(replies) and all(
        terminal(reply) == 1 and history.count(reply) < 2 for reply in replies)


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
            if scene in RESULT_STATES or scene == "tutorial":
                return scene
            # Do not accept the old board or end-of-turn animation as the opponent's response.
            if after.turn not in after.board:
                return None
            return next_player_position(new_frame, pos, move)

        # The result splash can flash before the stage's tutorial overlay opens.
        frame, reply = wait_for(game, read_next, 32, stable_for=.7)
        if isinstance(reply, str):
            return reply, confirms_win(after, history)
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
        result, proven_win = play_match(game, frame, pos, notify)
        settle(game, result, proven_win, notify)
        notify("completed", number, rounds)
