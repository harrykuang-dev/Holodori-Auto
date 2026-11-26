"""Read the chess hats and verify language-independent controls."""

from functools import lru_cache

import cv2
import numpy as np

from hats import TileEvidence, observe
from solver import BLUE, DOLPHIN, GOLD, KING, ORANGE, TURTLE, WHALE, Move, Position, square


WIDTH, HEIGHT = 1626, 915
QUADS_LEFT = (
    ((344, 280), (520, 280), (495, 383), (309, 383)),
    ((593, 280), (772, 280), (770, 383), (580, 383)),
    ((298, 414), (494, 414), (461, 540), (252, 540)),
    ((575, 414), (768, 414), (762, 540), (556, 540)),
    ((237, 577), (452, 577), (424, 733), (185, 733)),
    ((549, 577), (764, 577), (758, 733), (525, 733)),
)
SELECTED_LEFT = (
    ((460, 266), (594, 266), (585, 373), (448, 373)),
    ((652, 266), (785, 266), (783, 373), (646, 373)),
    ((440, 402), (582, 402), (568, 519), (426, 519)),
    ((641, 402), (782, 402), (778, 519), (636, 519)),
    ((419, 553), (569, 553), (555, 685), (401, 685)),
    ((630, 553), (782, 553), (778, 685), (624, 685)),
)
DEST = np.float32(((0, 0), (99, 0), (99, 99), (0, 99)))
RAFT_EDGES = ((7, 7), (50, 7), (92, 7), (7, 50), (92, 50), (7, 92), (50, 92), (92, 92))
MIRROR_EDGES = (2, 1, 0, 4, 3, 7, 6, 5)
MOVE_DIAGRAMS = {
    KING: (1, 1, 1, 1, 1, 1, 1, 1),
    WHALE: (1, 0, 1, 0, 0, 1, 0, 1),
    DOLPHIN: (0, 1, 0, 1, 1, 0, 1, 0),
    TURTLE: (0, 0, 0, 0, 1, 0, 0, 0),
    GOLD: (0, 1, 1, 1, 1, 0, 1, 1),
}


class VisionError(ValueError):
    pass


def quads(left):
    for i in range(0, len(left), 2):
        a, b = left[i:i+2]
        pair = a, b
        yield from pair
        for quad in reversed(pair):
            yield tuple((WIDTH - quad[j][0], quad[j][1]) for j in (1, 0, 3, 2))


@lru_cache(maxsize=2)
def transforms(selected):
    left = SELECTED_LEFT if selected else QUADS_LEFT
    return tuple(cv2.getPerspectiveTransform(np.float32([(x, y - 30) for x, y in quad]), DEST)
                 for quad in quads(left))


def tile(frame, index, selected=False):
    return cv2.warpPerspective(frame, transforms(selected)[index], (100, 100))


def point(index, selected=False):
    fields = tuple(quads(SELECTED_LEFT if selected else QUADS_LEFT))
    tl, tr, br, bl = fields[index]
    return (round((tl[0] + tr[0] + 2 * br[0] + 2 * bl[0]) / 6),
            round((tl[1] + tr[1] + 2 * br[1] + 2 * bl[1]) / 6) - 30)


def canonical(frame):
    h, w = frame.shape[:2]
    if not 1.76 <= w / h <= 1.80:
        raise VisionError(f"目前需要 16:9 游戏客户区，实际为 {w}×{h}")
    if (w, h) == (WIDTH, HEIGHT):
        return frame
    return cv2.resize(frame, (WIDTH, HEIGHT), interpolation=cv2.INTER_LINEAR)


def split_frame(frame):
    """Accept a client capture or the recorded 1626×945 window including its frame."""
    if frame.shape[:2] == (945, 1626):
        frame = frame[30:]
    return canonical(frame)


def bgr(area):
    return np.moveaxis(area.astype(np.int16), -1, 0)


def raft_markers(raster):
    markers = []
    weak_orange = []
    for x, y in RAFT_EDGES:
        b, g, r = bgr(raster[y-4:y+5, x-4:x+5])
        orange = (r > 200) & (g > 65) & (g < 153) & (b < 90)
        strengths = (((b > 170) & (g > 120) & (g < 185) & (r < 80)).mean(),
                     orange.mean(),
                     ((b > 164) & (r > 147) & (abs(b-r) < 45) & (abs(g-r) < 35)).mean())
        winner = int(np.argmax(strengths))
        marker = (BLUE, ORANGE, 0)[winner] if strengths[winner] > .48 else None
        if marker == ORANGE and (orange & (g < 125)).mean() <= .48:
            weak_orange.append(len(markers))
        markers.append(marker)
    if BLUE in markers:
        # A bright hammer can cover one tile edge without changing its team.
        for edge in weak_orange:
            markers[edge] = None
    return markers


def raft_evidence(markers):
    blue, orange = markers.count(BLUE), markers.count(ORANGE)
    visible = sum(mark is not None for mark in markers)
    painted, other = max(blue, orange), min(blue, orange)
    if not painted or (other and (other != 1 or painted < 3)):
        return None
    side = BLUE if blue > orange else ORANGE
    compatible = []
    exact = []
    for kind, pattern in MOVE_DIAGRAMS.items():
        if side == ORANGE:
            pattern = tuple(pattern[i] for i in MIRROR_EDGES)
        if any(mark == side and not edge for mark, edge in zip(markers, pattern)):
            continue
        white_misses = sum(mark == 0 and edge for mark, edge in zip(markers, pattern))
        if painted == 1:
            opposite = 3 if side == BLUE else 4
            if kind != TURTLE or markers[opposite] != 0:
                continue
        if white_misses <= (0 if other else 1):
            compatible.append(side * kind)
        if white_misses == 0:
            exact.append(side * kind)
    unique = exact[0] if not other and len(exact) == 1 and visible >= 4 else None
    return TileEvidence(tuple(compatible), unique, painted, visible, mixed=bool(other))


def observe_board(frame):
    for index in range(12):
        row = index // 4
        x, _ = point(index)
        y = (100, 242, 404)[row]
        floor = raft_evidence(raft_markers(tile(frame, index)))
        yield observe(frame[y-46:y+45, x-115:x+115], index, floor=floor)


def read_board(frame):
    observations = list(observe_board(frame))
    crowns = [(index, choices) for index, choices in enumerate(observations)
              if abs(choices[0]) == KING]
    if len(crowns) != 2:
        raise VisionError("棋盤上應有雙方各一枚隊長")
    (first, one), (second, other) = crowns
    assignments = [(leader, -leader) for leader in one if -leader in other]
    if len(assignments) != 1:
        raise VisionError("暫時無法確認兩枚隊長的朝向")
    leader, opponent = assignments[0]
    observations[first], observations[second] = (leader,), (opponent,)
    for index, choices in enumerate(observations):
        if len(choices) != 1:
            raise VisionError(f"{square(index)} 的帽子朝向不明")
    return tuple(choices[0] for choices in observations)


def match_position(frame, candidates, *, previous, hands):
    candidates = {pos for pos in candidates if (pos.blue, pos.orange) == hands}
    if not candidates:
        raise VisionError("預期狀態為空")
    observations = tuple(observe_board(frame))
    matching = [candidate for candidate in candidates
                if all(piece in choices for piece, choices in zip(candidate.board, observations))]
    if len(matching) != 1:
        raise VisionError("暫時無法從棋帽確認唯一的合法局面")
    confirmed = matching[0]
    changes = [i for i, (before, piece) in enumerate(zip(previous.board, confirmed.board)) if before != piece]
    if changes and all(len(observations[i]) > 1 for i in changes):
        if len(changes) == 1:
            target = changes[0]
            kind = abs(confirmed.board[target])
            if (not previous.board[target] and kind in previous.hand(previous.turn)
                    and previous.next(Move(-kind, target)) == confirmed):
                # The matching reserve disappeared and its hat is visible at this unique destination.
                return confirmed
        raise VisionError("暫時看不清有變動的棋帽")
    return confirmed


def highlighted(frame, target):
    blue, green, red = bgr(tile(frame, target, True)[19:82, 18:83])
    return ((blue > 185) & (green > 145) & (blue - green > 10) & (green - red > 45)).mean() > .21


def source_arrow(frame, origin):
    x, _ = point(origin, selected=True)
    y = (138, 293, 464)[origin // 4] - 30
    area = frame[y-34:y+35, x-54:x+55]
    blue, green, red = bgr(area)
    interior = ((blue > 200) & (green > 130) & (green < 221) & (red < 52)).astype(np.uint8)
    contours, _ = cv2.findContours(interior, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in contours:
        cx, cy, w, h = cv2.boundingRect(contour)
        if not (31 <= w <= 67 and 13 <= h <= 36 and 225 <= cv2.contourArea(contour) <= 950):
            continue
        # The blue arrow tapers downward. Also require its white outline.
        upper = interior[cy+2:cy+h//3, cx:cx+w].sum()
        lower = interior[cy+h*2//3:cy+h, cx:cx+w].sum()
        outline = area[max(0, cy-6):cy, cx:cx+w]
        if upper > lower and outline.size and (outline.min(axis=2) > 224).mean() > .22:
            return True
    return False


def selected_piece(frame, piece):
    # The left information panel displays the move pattern of the selected hat.
    marks = []
    for i, j in ((0,0), (1,0), (2,0), (0,1), (2,1), (0,2), (1,2), (2,2)):
        x, y = 101 + 36*i, 196 + 36*j
        b, g, r = bgr(frame[y-5:y+6, x-5:x+6])
        marks.append(int(((b > 175) & (g > 75) & (g < 180) & (r < 65)).mean() > .55))
    valid = [MOVE_DIAGRAMS[piece]]
    if piece in (TURTLE, GOLD):
        clockwise = (5, 3, 0, 6, 1, 7, 4, 2)
        valid.append(tuple(MOVE_DIAGRAMS[piece][i] for i in clockwise))
        valid.append(tuple(MOVE_DIAGRAMS[piece][i] for i in reversed(clockwise)))
    return tuple(marks) in valid


def legend(frame):
    return all(frame[112:319, left:right].min(axis=2).mean() > 190
               for left, right in ((37, 52), (218, 234)))


def is_ready(frame):
    # The move diagram switches from blue to orange on the opponent's turn.
    b, g, r = bgr(frame[113:136, 193:216])
    blue_legend = ((b > 172) & (g > 85) & (g < 175) & (r < 68)).mean() > .23
    b, g, r = bgr(frame[56:82, 1245:1275])
    clock = ((b > 155) & (g > 100) & (g < 204) & (r < 100)).mean() > .38
    solo_undo = clock and (frame[53:87, 1442:1469].min(axis=2) > 164).mean() > .65
    return blue_legend and solo_undo and legend(frame)


def hand_read(frame, side):
    """Classify the row of captured-piece icons by hat hue, in display order."""
    first = 210 if side == BLUE else 1465
    spacing = 127
    centers = [first + spacing * slot * side for slot in range(6)]
    left, right = min(centers) - 65, max(centers) + 66
    hsv = cv2.cvtColor(frame[806:855, left:right], cv2.COLOR_BGR2HSV)
    h, s, v = np.moveaxis(hsv, -1, 0)
    masks = {TURTLE: (h >= 40) & (h <= 78), DOLPHIN: (h >= 140) & (h <= 178),
             WHALE: (h >= 106) & (h <= 128)}
    pieces = [None] * len(centers)
    for piece, mask in masks.items():
        valid = (mask & (s > 90) & (v > 105)).astype(np.uint8)
        _, _, stats, _ = cv2.connectedComponentsWithStats(valid)
        for x, y, w, ch, area in stats[1:]:
            if not (35 <= w <= 108 and ch >= 30 and area >= 450 and y + ch >= 36):
                continue
            center = int(x + w // 2 + left)
            slot = round(side * (center - first) / spacing)
            if not (0 <= slot < len(centers) and abs(center - centers[slot]) <= 25):
                continue
            if pieces[slot] is None or area > pieces[slot][0]:
                pieces[slot] = (area, center, piece)

    row = []
    for entry in pieces:
        if entry is None:
            break
        _, center, piece = entry
        row.append((center, 847, piece))
    return row


def hand_inventory(frame):
    return tuple(tuple(sorted(piece for _, _, piece in hand_read(frame, side)))
                 for side in (BLUE, ORANGE))


def read_position(frame):
    if not is_ready(frame):
        raise VisionError("尚未確認藍方回合與單人棋盤。")
    board = read_board(frame)
    return Position(board, *hand_inventory(frame))
