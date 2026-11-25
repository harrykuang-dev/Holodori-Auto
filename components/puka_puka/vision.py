"""Recognize the move markers printed on each floating tile."""

from collections import Counter
from functools import lru_cache

import cv2
import numpy as np

from solver import BLUE, DOLPHIN, GOLD, KING, ORANGE, TURTLE, WHALE, Position, square


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
EDGES = ((7, 7), (50, 7), (92, 7), (7, 50), (92, 50), (7, 92), (50, 92), (92, 92))
PATTERNS = {
    KING: (1, 1, 1, 1, 1, 1, 1, 1),
    WHALE: (1, 0, 1, 0, 0, 1, 0, 1),
    DOLPHIN: (0, 1, 0, 1, 1, 0, 1, 0),
    TURTLE: (0, 0, 0, 0, 1, 0, 0, 0),
    GOLD: (0, 1, 1, 1, 1, 0, 1, 1),
}
MIRROR = (2, 1, 0, 4, 3, 7, 6, 5)


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


def tile_markers(raster):
    observed = []
    weak_orange = []
    for x, y in EDGES:
        blue, green, red = bgr(raster[y-4:y+5, x-4:x+5])
        orange = (red > 200) & (green > 65) & (green < 153) & (blue < 90)
        fractions = (
            ((blue > 170) & (green > 120) & (green < 185) & (red < 80)).mean(),
            orange.mean(),
            ((blue > 164) & (red > 147) & (abs(blue - red) < 45) & (abs(green - red) < 35)).mean(),
        )
        winner = int(np.argmax(fractions))
        marker = (BLUE, ORANGE, 0)[winner] if fractions[winner] > .48 else None
        if marker == ORANGE and (orange & (green < 125)).mean() <= .48:
            weak_orange.append(len(observed))
        observed.append(marker)
    # A foreground hammer can look orange on a tile that has blue ink.
    if BLUE in observed:
        for index in weak_orange:
            observed[index] = None
    return observed


def marker_observations(frame):
    return [tile_markers(tile(frame, index)) for index in range(12)]


def visible_white_edge(raster, observed):
    for marks, left, right in (((0, 3, 5), 14, 35), ((2, 4, 7), 65, 86)):
        if all(observed[index] == 0 for index in marks):
            blue, green, red = bgr(raster[14:83, left:right])
            tile_white = ((blue > 225) & (green > 221) & (red > 210)
                          & (blue - red > 5) & (blue - red < 36) & (green - red > 3))
            if tile_white.mean() > .8:
                return True
    return False


def pattern(piece):
    if not piece:
        return (0,) * 8
    marks = PATTERNS[abs(piece)]
    if piece < 0:
        marks = tuple(marks[i] for i in MIRROR)
    return tuple((BLUE if piece > 0 else ORANGE) if mark else 0 for mark in marks)


def mismatch(observed, expected):
    return sum(a is not None and a != b for a, b in zip(observed, expected))


def hat_scores(frame, index):
    row = index // 4
    x, _ = point(index)
    y = (130, 272, 434)[row] - 30
    scores = {}
    for side in (BLUE, ORANGE):
        cx = x - side * (22 + row * 5)
        area = frame[y-29:y+26, cx-42:cx+42]
        h, s, v = np.moveaxis(cv2.cvtColor(area, cv2.COLOR_BGR2HSV), -1, 0)
        kind = {
            KING: ((h <= 9) | (h >= 175)) & (s > 145),
            WHALE: (h >= 108) & (h <= 130) & (s > 128),
            DOLPHIN: (h >= 142) & (h < 175) & (s > 93),
            TURTLE: (h >= 37) & (h <= 78) & (s > 100),
            GOLD: (h >= 19) & (h < 37) & (s > 125),
        }
        for piece, mask in kind.items():
            scores[side * piece] = (mask & (v > 105)).mean()
    return scores


def classify(observed, hats, raster):
    color_counts = Counter(mark for mark in observed if mark)
    known = sum(mark is not None for mark in observed)
    if not color_counts:
        piece = max(hats, key=hats.get)
        hat = hats[piece]
        if known >= 5 or (known == 4 and hat < .23):
            if known < 7 and hat > .37:
                raise VisionError("看到动物帽，阵营标记被挡住")
            return 0
        # A foreground hat can cover most of the next tile's surface.
        if known == 3 and hat < .14 and visible_white_edge(raster, observed):
            return 0
        if 0 < known < 4 and hat >= .80 and mismatch(observed, pattern(piece)) == 0:
            alternate = max((score for other, score in hats.items() if other != piece), default=0)
            if hat - alternate >= .30:
                return piece
        raise VisionError(f"浮台标记不明确 {observed}")
    hat_matches = sorted(((confidence, piece) for piece, confidence in hats.items()
                          if color_counts[BLUE if piece > 0 else ORANGE]), reverse=True)
    if hat_matches:
        confidence, piece = hat_matches[0]
        next_best = hat_matches[1][0] if len(hat_matches) > 1 else 0
        errors = mismatch(observed, pattern(piece))
        enough_tiles = (known >= 4 and errors <= 3) or (known >= 3 and errors == 0 and confidence >= .55)
        if confidence >= .38 and confidence - next_best >= .12 and enough_tiles:
            return piece
    options = [piece for piece in range(-GOLD, GOLD+1)
               if piece == 0 or color_counts[BLUE if piece > 0 else ORANGE]]
    scores = []
    for piece in options:
        hat = hats.get(piece, 0)
        error = mismatch(observed, pattern(piece))
        penalty = max(0., .19-hat)*8 if piece else 0.
        scores.append((error + penalty - min(2.1, max(0., hat-.14)*5), piece, error, hat))
    scores.sort()
    score, chosen, error, hat = scores[0]
    if known < (4 if hat > .18 else 5) or error > (3 if hat > .45 else 2) or scores[1][0] - score < .35:
        raise VisionError(f"浮台标记不明确 {observed}，候选 {scores[:3]}")
    return chosen


def read_board(frame):
    pieces = []
    for square_index in range(12):
        raster = tile(frame, square_index)
        try:
            pieces.append(classify(tile_markers(raster), hat_scores(frame, square_index), raster))
        except VisionError as e:
            raise VisionError(f"{square(square_index)} {e}") from e
    if Counter(pieces)[KING] != 1 or Counter(pieces)[-KING] != 1:
        raise VisionError("棋盘上应能识别到双方各一枚队长")
    return tuple(pieces)


def match_position(frame, candidates, *, previous):
    candidates = set(candidates)
    if not candidates:
        raise VisionError("预期状态为空")
    try:
        board = read_board(frame)
    except VisionError:
        board = None
    if board is not None:
        matching = [candidate for candidate in candidates if candidate.board == board]
        if len(matching) == 1:
            return matching[0]
        raise VisionError("识别到的棋盘与预期的合法局面不一致")
    observations = marker_observations(frame)
    visible = [sum(mark is not None for mark in marks) for marks in observations]
    if sum(visible) < 65:
        raise VisionError("棋盘仍在移动或被遮挡")

    sparse_pieces = {}
    for index, count in enumerate(visible):
        if count >= 4 or all(previous[index] == pos.board[index] for pos in candidates):
            continue
        try:
            sparse_pieces[index] = classify(observations[index], hat_scores(frame, index), tile(frame, index))
        except VisionError:
            continue
    candidates = [pos for pos in candidates
                  if all(pos.board[index] == piece for index, piece in sparse_pieces.items())]
    if not candidates:
        raise VisionError("被遮挡的棋子与预期的合法局面不一致")
    scores = [(sum(mismatch(marks, pattern(piece)) for marks, piece in zip(observations, pos.board)), pos)
              for pos in candidates]
    scores.sort(key=lambda value: value[0])
    errors, best = scores[0]
    if errors > 6 or (len(scores) > 1 and scores[1][0] <= errors + 2):
        raise VisionError(f"无法唯一确认对方落子，最低标记误差 {errors}")
    for index, expected in enumerate(best.board):
        if previous[index] == expected:
            continue
        ink = [mark for mark in observations[index] if mark]
        side = BLUE if expected > 0 else ORANGE if expected < 0 else 0
        if len(ink) >= 2 and side not in ink:
            raise VisionError(f"{square(index)} 的浮台颜色与预期落子不符")
        if visible[index] < 4 and index not in sparse_pieces:
            raise VisionError(f"{square(index)} 的落子标记被遮挡")
    return best


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
    valid = [PATTERNS[piece]]
    if piece in (TURTLE, GOLD):
        clockwise = (5, 3, 0, 6, 1, 7, 4, 2)
        valid.append(tuple(PATTERNS[piece][i] for i in clockwise))
        valid.append(tuple(PATTERNS[piece][i] for i in reversed(clockwise)))
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
    left = frame[806:855, 145:695] if side == BLUE else frame[806:855, 931:1480]
    hsv = cv2.cvtColor(left, cv2.COLOR_BGR2HSV)
    h, s, v = np.moveaxis(hsv, -1, 0)
    masks = {TURTLE: (h >= 40) & (h <= 78), DOLPHIN: (h >= 140) & (h <= 178),
             WHALE: (h >= 106) & (h <= 128)}
    pieces = []
    for piece, mask in masks.items():
        valid = (mask & (s > 90) & (v > 105)).astype(np.uint8)
        n, _, stats, _ = cv2.connectedComponentsWithStats(valid)
        for x, y, w, ch, area in stats[1:n]:
            if 35 <= w <= 108 and 12 <= ch <= 49 and area >= 450 and y < 39:
                pieces.append((int(x + w // 2 + (145 if side == BLUE else 931)), 847, piece))
    pieces.sort(reverse=side == ORANGE)
    previous = 115 if side == BLUE else 1511
    row = []
    for entry in pieces:
        gap = side * (entry[0] - previous)
        if not 58 <= gap <= 153:
            break
        row.append(entry)
        previous = entry[0]
    return row


def read_position(frame):
    if not is_ready(frame):
        raise VisionError("尚未確認藍方回合與單人棋盤。")
    board = read_board(frame)
    return Position(board, *(tuple(sorted(p for _, _, p in hand_read(frame, side)))
                             for side in (BLUE, ORANGE)))
