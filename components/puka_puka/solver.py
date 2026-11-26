"""Game positions and a shortest-forced-result search for the 3×4 board."""

from collections import Counter
from dataclasses import dataclass
from functools import cache, lru_cache
from http.client import HTTPException
import json
import time
from urllib.parse import urlencode
from urllib.request import urlopen


BLUE, ORANGE = 1, -1
KING, WHALE, DOLPHIN, TURTLE, GOLD = range(1, 6)
NAMES = ("", "队长", "鲸鱼", "海豚", "绿龟", "金龟")
LETTERS = " LEGCR"
ORTHOGONAL = ((0, -1), (0, 1), (-1, 0), (1, 0))
DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))
VELOCITY = ((), ORTHOGONAL + DIAGONAL, DIAGONAL, ORTHOGONAL, ((0, 1),),
            ORTHOGONAL + ((-1, 1), (1, 1)))
TABLEBASE = "https://dobutsu.brianhliou.com/api"
MATE = 100_000
MATERIAL = (0, 0, 190, 230, 100, 340)
KING_ADVANCE = (0, 12, 55, 230)


def square(index):
    return f"{'ABCD'[index % 4]}{index // 4 + 1}"


@dataclass(frozen=True, slots=True)
class Move:
    source: int  # Negative piece type for a reserve placement.
    target: int

    def label(self):
        origin = square(self.source) if self.source >= 0 else f"部署{NAMES[-self.source]}"
        return f"{origin} → {square(self.target)}"


@dataclass(frozen=True, slots=True)
class Position:
    board: tuple[int, ...]
    blue: tuple[int, ...] = ()
    orange: tuple[int, ...] = ()
    turn: int = BLUE

    def hand(self, side):
        return self.blue if side == BLUE else self.orange

    def next(self, move):
        board = list(self.board)
        hand = list(self.hand(self.turn))
        piece = -move.source
        if move.source < 0:
            hand.remove(piece)
        else:
            piece = abs(board[move.source])
            board[move.source] = 0
            captured = abs(board[move.target])
            if captured > KING:
                hand.append(TURTLE if captured == GOLD else captured)
            if piece == TURTLE and move.target % 4 == goal(self.turn):
                piece = GOLD
        board[move.target] = piece * self.turn
        our_hand = tuple(sorted(hand))
        if self.turn == BLUE:
            return Position(tuple(board), our_hand, self.orange, ORANGE)
        return Position(tuple(board), self.blue, our_hand, BLUE)


def goal(side):
    return 3 if side == BLUE else 0


@cache
def destinations(index, piece, side):
    row, col = divmod(index, 4)
    return tuple((row + dr) * 4 + col + side * dc for dr, dc in VELOCITY[piece]
                 if 0 <= row + dr < 3 and 0 <= col + side * dc < 4)


def moves(pos):
    for origin, val in enumerate(pos.board):
        if val * pos.turn > 0:
            for target in destinations(origin, abs(val), pos.turn):
                if pos.board[target] * pos.turn <= 0:
                    yield Move(origin, target)
    for piece in sorted(set(pos.hand(pos.turn))):
        for target, val in enumerate(pos.board):
            if not val:
                yield Move(-piece, target)


def terminal(pos):
    if pos.turn not in pos.board:
        return -1
    if -pos.turn not in pos.board:
        return 1
    king = pos.board.index(pos.turn)
    if king % 4 == goal(pos.turn):
        return 1  # The opponent just completed their reply.
    return None


def ordering(pos, move):
    target = abs(pos.board[move.target])
    piece = abs(pos.board[move.source]) if move.source >= 0 else -move.source
    return (target == KING, piece == KING and move.target % 4 == goal(pos.turn),
            bool(target), piece == TURTLE and move.source >= 0 and move.target % 4 == goal(pos.turn))


def solve(pos, history=(), seconds=2.0, max_depth=12):
    """Return (result, plies, tied moves). None means the search couldn't prove it."""
    stop_at = time.monotonic() + seconds
    counts = Counter(history)
    visits = 0

    def has_win(state, ply, outcome):
        nonlocal visits
        visits += 1
        if visits % 1024 == 0 and time.monotonic() >= stop_at:
            raise TimeoutError
        result = terminal(state)
        if result is not None:
            return result == outcome
        if counts[state] >= 2 or ply == 0:
            return False
        legal = sorted(moves(state), key=lambda m: ordering(state, m), reverse=True)
        if not legal:
            return False  # Unconfirmed stalemate outcome.
        counts[state] += 1
        try:
            replies = (has_win(state.next(m), ply - 1, -outcome) for m in legal)
            return any(replies) if outcome == 1 else all(replies)
        finally:
            counts[state] -= 1

    result = terminal(pos)
    if result is not None or counts[pos] >= 2:
        return (result if result is not None else 0), 0, []
    legal = list(moves(pos))
    if not legal:
        return None, None, []
    counts[pos] += 1
    earlier_losses = []
    try:
        for depth in range(1, max_depth + 1):
            if time.monotonic() >= stop_at:
                break
            wins = [m for m in legal if has_win(pos.next(m), depth - 1, -1)]
            if wins:
                return 1, depth, wins
            losses = [m for m in legal if has_win(pos.next(m), depth - 1, 1)]
            if len(losses) == len(legal):
                return -1, depth, [m for m in legal if m not in earlier_losses]
            earlier_losses = losses
    except TimeoutError:
        pass
    return None, None, []


def evaluate(pos):
    """Estimate the side-to-move advantage and detect an immediate king capture."""
    score = 0
    attacks = {BLUE: set(), ORANGE: set()}
    for index, piece in enumerate(pos.board):
        if not piece:
            continue
        side = BLUE if piece > 0 else ORANGE
        kind = abs(piece)
        destinations_from_piece = destinations(index, kind, side)
        attacks[side].update(destinations_from_piece)
        advance = 3 - abs(goal(side) - index % 4)
        if kind == KING:
            value = KING_ADVANCE[advance]
        else:
            mobility = sum(pos.board[target] * side <= 0 for target in destinations_from_piece)
            value = MATERIAL[kind] + 9 * mobility + 12 * advance
        score += side * value
    if pos.board.index(-pos.turn) in attacks[pos.turn]:
        return MATE
    if pos.board.index(pos.turn) in attacks[-pos.turn]:
        score -= pos.turn * 75
    for side in (BLUE, ORANGE):
        score += side * sum(MATERIAL[piece] for piece in pos.hand(side))
    return score * pos.turn


def search_moves(pos, history, seconds, max_depth=16):
    """Rank legal moves with completed iterations of alpha-beta search."""
    deadline = time.monotonic() + seconds
    counts = Counter(history)
    counts[pos] += 1
    nodes = 0
    preferred = {}

    @lru_cache(maxsize=24_000)
    def ordered(state):
        return tuple(sorted(moves(state), key=lambda move: ordering(state, move), reverse=True))

    @lru_cache(maxsize=24_000)
    def leaf(state):
        return evaluate(state)

    def visit(state, remaining, ply, alpha, beta):
        nonlocal nodes
        nodes += 1
        if nodes % 128 == 0 and time.monotonic() >= deadline:
            raise TimeoutError
        outcome = terminal(state)
        if outcome is not None:
            return outcome * (MATE - ply)
        if counts[state] >= 2:
            return 0
        if remaining == 0:
            score = leaf(state)
            return MATE - ply - 1 if score == MATE else score
        legal = ordered(state)
        if not legal:
            return 0
        first = preferred.get(state)
        if first is not None and first != legal[0]:
            legal = (first, *(move for move in legal if move != first))
        best = -MATE
        counts[state] += 1
        try:
            for move in legal:
                score = -visit(state.next(move), remaining - 1, ply + 1, -beta, -alpha)
                if score > best:
                    best, preferred[state] = score, move
                if best >= beta:
                    break
                alpha = max(best, alpha)
        finally:
            counts[state] -= 1
        return best

    children = {move: pos.next(move) for move in ordered(pos)}
    if not children:
        return None, None, []
    # Even with a zero budget, use the one-move evaluation for each legal action.
    ranked = {move: -visit(child, 0, 1, -MATE, MATE) for move, child in children.items()}
    depth = 1
    try:
        for limit in range(2, max_depth + 1):
            if time.monotonic() >= deadline or abs(max(ranked.values())) >= MATE - max_depth - 2:
                break
            scores = {}
            alpha = -MATE
            for move in sorted(children, key=ranked.get, reverse=True):
                # Keep the equality window open so tied best moves retain exact scores.
                score = -visit(children[move], limit - 1, 1, -MATE, -alpha + 1)
                scores[move] = score
                alpha = max(alpha, score)
            depth, ranked = limit, scores
    except TimeoutError:
        pass
    best = max(ranked.values())
    choices = [move for move, score in ranked.items() if score == best]
    if abs(best) >= MATE - max_depth - 2:
        return (1 if best > 0 else -1), MATE - abs(best), choices
    return None, depth, choices


def table_code(pos):
    def letter(p):
        return LETTERS[p] if p > 0 else LETTERS[-p].lower() if p < 0 else "-"

    ranks = ["".join(letter(pos.board[row * 4 + col]) for row in range(3))
             for col in range(3, -1, -1)]
    hands = "".join(map(letter, pos.blue)) + "".join(letter(-p) for p in pos.orange)
    return "/".join(["S" if pos.turn == BLUE else "G", *ranks, hands or "-"])


def from_table_code(code):
    side, *rows, hands = code.split("/")
    if side not in {"S", "G"} or len(rows) != 4 or any(len(row) != 3 for row in rows):
        raise ValueError(f"无效盘面 {code}")
    signed = {**dict(zip("-LEGCR", range(6))), **dict(zip("legcr", range(-1, -6, -1)))}
    board = tuple(signed[rows[col][row]] for row in range(3) for col in range(3, -1, -1))
    reserves = [signed[p] for p in hands]
    return Position(board, tuple(sorted(p for p in reserves if p > 0)),
                    tuple(sorted(-p for p in reserves if p < 0)), BLUE if side == "S" else ORANGE)


def full_inventory(pos):
    pieces = [abs(p) for p in pos.board if p] + list(pos.blue) + list(pos.orange)
    return Counter(TURTLE if p == GOLD else p for p in pieces) == Counter({p: 2 for p in range(1, 5)})


@cache
def probe(pos):
    if not full_inventory(pos):
        raise ValueError("完整开局棋谱库需要双方合计八枚棋子")
    code = table_code(pos)
    with urlopen(f"{TABLEBASE}?{urlencode({'pos': code})}", timeout=2.5) as response:
        reply = json.load(response)
    if reply.get("pos") != code:
        raise ValueError("棋谱库未返回请求的局面")
    result = {"win": 1, "draw": 0, "loss": -1}
    data = {from_table_code(item["to"]): (result[item["result"]], item["dtm"] or 0)
            for item in reply["moves"]}
    legal = {m: pos.next(m) for m in moves(pos)}
    if set(data) != set(legal.values()):
        raise ValueError("棋谱库和本地规则给出的后继局面不一致")
    return {m: data[child] for m, child in legal.items()}


def recommend(pos, history=(), seconds=2.0, online=False):
    proof_budget = min(.5, seconds / 4)
    started = time.monotonic()
    outcome, depth, proven = solve(pos, history, proof_budget)
    remaining = max(0., seconds - (time.monotonic() - started))
    if proven or terminal(pos) is not None:
        return outcome, depth, proven, "本地证明"
    if online and full_inventory(pos):
        try:
            scores = probe(pos)
            if scores:
                return (*rank_tablebase(pos, history, scores), "动物将棋棋谱库")
        except (OSError, HTTPException, ValueError, KeyError, TypeError, AttributeError):
            pass
    outcome, depth, choices = search_moves(pos, history, remaining)
    return outcome, depth, choices, "本地估算" if outcome is None else "本地证明"


def rank_tablebase(pos, history, scores):
    repetitions = Counter(history)
    repetitions[pos] += 1
    ranked = {}
    for move, (res, distance) in scores.items():
        child = pos.next(move)
        if terminal(child) is None and repetitions[child] >= 2:
            res, distance = 0, 0
        ranked[move] = (res, distance if res < 0 else -distance)
    best = max(ranked.values())
    return best[0], abs(best[1]), [m for m, value in ranked.items() if value == best]
