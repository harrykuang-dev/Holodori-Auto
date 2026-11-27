"""Read a solo match, choose moves, and verify each click against the next frame."""

import time
from functools import partial

from solver import BLUE, NAMES, moves, recommend, square, terminal
from stages import CHALLENGE_ENTRIES, CLICK, MENU_STATES, REFILL_STATES, RESULT_STATES, classify_screen
from vision import (VisionError, hand_inventory, hand_read, highlighted, is_ready, match_position,
                    point, read_position, selected_layout_visible, selected_piece, source_arrow)


POST_MATCH_OVERLAYS = {"reward", "event_next"}


class StopPlay(RuntimeError):
    pass


def next_player_position(frame, pos, move):
    if not is_ready(frame):
        raise VisionError("等待我方回合")
    after = pos.next(move)
    hands = hand_inventory(frame)
    replies = (after.next(reply) for reply in moves(after))
    candidates = [reply for reply in replies if terminal(reply) is None]
    # The game can show the blue legend before the opponent's move is visible.
    candidates.append(after)
    observed = match_position(frame, candidates, previous=after, hands=hands)
    if observed == after:
        raise VisionError("等待對方完成落子")
    return observed


def source_point(frame, pos, move):
    if move.source >= 0:
        return point(move.source, rows=pos.rows)
    capture_icons = hand_read(frame, BLUE)
    candidates = [(x, y) for x, y, p in capture_icons if p == -move.source]
    if hand_inventory(frame) != (pos.blue, pos.orange) or not candidates:
        raise StopPlay("无法确认部署用的候补图标")
    return candidates[0]


def selection_ready(frame, pos, move):
    piece = abs(pos.board[move.source]) if move.source >= 0 else -move.source
    return (not is_ready(frame) and selected_piece(frame, piece)
            and selected_layout_visible(frame, pos.rows)
            and (move.source < 0 or source_arrow(frame, move.source, rows=pos.rows))
            and highlighted(frame, move.target, rows=pos.rows))


def select_move(game, pos, move, read_current):
    def unchanged(frame):
        if read_current(frame) != pos:
            raise StopPlay("求解期间棋盘已变化")
        return pos

    for _ in range(2):
        # Retry a source click only after confirming the same unselected board.
        frame, _ = wait_for(game, unchanged, 4)
        game.click(*source_point(frame, pos, move))
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline:
            if selection_ready(game.capture(), pos, move):
                return
            time.sleep(.10)
    raise StopPlay(f"无法确认 {move.label()} 的选中标记和合法落点")


def choose(pos, history, notify):
    result, depth, choices, _ = recommend(pos, history, seconds=4, online=True)
    move = choices[0]
    notify("move", move.label(), result, depth)
    return move


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


def prepare(game, notify, *, auto_refill=False):
    entries = {"hub", "stage_start"} | CHALLENGE_ENTRIES
    allowed = {"tutorial", "board", "team_auto", "team_start", "result_ok", *entries} | POST_MATCH_OVERLAYS
    retry_entry = None
    refilled = False
    notify("waiting_entry")
    while True:
        state = wait_menu(game, allowed | REFILL_STATES, 50, stable_for=.55)
        if state in REFILL_STATES or state == "challenge_low_energy":
            if not auto_refill:
                raise StopPlay('能量不足。可手動補充，或開啟「自動補充能量」後再開始。')
            if refilled:
                raise StopPlay('補充後仍然需要能量，已停止本次入場。')
            if state == "challenge_low_energy":
                # The pink card opens the refill dialog when the cost is red.
                retry_entry = "challenge_continue"
                allowed.discard(state)
                game.click(*CLICK[retry_entry])
                state = wait_menu(game, REFILL_STATES | {retry_entry, "board"}, stable_for=.55)
        if state in REFILL_STATES:
            try:
                wait_menu(game, {"refill"}, 4, stable_for=.45)
            except StopPlay as error:
                raise StopPlay('無法確認一瓶道具的補充選項。') from error
            notify("refilling")
            game.click(*CLICK["refill"])
            refilled = True
            if retry_entry:
                allowed.add(retry_entry)
            state = wait_menu(game, allowed, stable_for=.55)
        if state == "board":
            return wait_for(game, read_position, 8, stable_for=.4)
        game.click(*CLICK[state])
        allowed.remove(state)
        if state in ("stage_start", "challenge_continue", "tutorial", "team_auto", "team_start"):
            allowed -= entries
        if state == 'team_start':
            allowed.discard('team_auto')
        if state in ("stage_start", "challenge_continue"):
            retry_entry = state
            notify("waiting_board")


def settle(game, state, notify):
    notify("waiting_result")
    # The stage carousel can appear briefly before the reward overlay opens.
    pending = RESULT_STATES | POST_MATCH_OVERLAYS | {"tutorial"}
    while state not in MENU_STATES:
        game.click(*CLICK[state])
        pending.discard(state)
        if state in {"result_details", "win_details", "result_ok"} | POST_MATCH_OVERLAYS:
            pending -= RESULT_STATES - {"result_ok"}
        state = wait_menu(game, MENU_STATES | pending, stable_for=1.2)


def play_match(game, frame, pos, notify):
    history = []
    read_current = partial(read_position, rows=pos.rows)
    endings = RESULT_STATES | CHALLENGE_ENTRIES | POST_MATCH_OVERLAYS | {"tutorial"}
    while True:
        if terminal(pos) is not None or not any(moves(pos)):
            return wait_menu(game, endings, 32, stable_for=.7)
        move = choose(pos, history, notify)
        select_move(game, pos, move, read_current)
        game.click(*point(move.target, selected=True, rows=pos.rows))
        after = pos.next(move)
        history.extend((pos, after))

        def read_reply(new_frame, previous=pos, submitted=move):
            return next_player_position(new_frame, previous, submitted)

        def read_next(new_frame):
            scene = classify_screen(new_frame)
            if scene in endings:
                return scene
            # Do not accept the old board or end-of-turn animation as the opponent's response.
            if after.turn not in after.board:
                return None
            return read_reply(new_frame)

        # The result splash can flash before the stage's tutorial overlay opens.
        frame, reply = wait_for(game, read_next, 32, stable_for=.7)
        if isinstance(reply, str):
            return reply
        pos = reply
        read_current = read_reply
        changes = [f"{square(i)}={NAMES[abs(p)] or '空'}" for i, p in enumerate(pos.board)
                   if p != after.board[i]]
        notify("reply", move.label(), "，".join(changes))
        if history.count(pos) >= 2:
            try:
                return wait_menu(game, endings, 2.5, stable_for=.55)
            except StopPlay:
                # The game may still allow a move after a non-consecutive repetition.
                pass


def run(game, rounds, notify, *, auto_refill=False):
    for number in range(1, rounds + 1):
        frame, pos = prepare(game, notify, auto_refill=auto_refill)
        result = play_match(game, frame, pos, notify)
        settle(game, result, notify)
        notify("completed", number, rounds)
