"""Read the chess hats and verify language-independent controls."""

from functools import lru_cache

import cv2
import numpy as np

from hat_side_model import pick_side
from hats import TileEvidence, describe, observe, pose_costs, references
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
FOUR_ROW_LEFT = (
    ((378, 255), (540, 255), (516, 322), (349, 322)),
    ((608, 257), (778, 257), (776, 322), (592, 322)),
    ((324, 343), (509, 343), (481, 425), (280, 425)),
    ((591, 344), (775, 344), (771, 425), (567, 425)),
    ((268, 450), (476, 450), (436, 552), (215, 552)),
    ((566, 450), (769, 450), (761, 552), (534, 552)),
    ((198, 584), (433, 584), (384, 718), (125, 718)),
    ((523, 585), (766, 585), (749, 719), (493, 719)),
)
SELECTED_LEFT = (
    ((460, 266), (594, 266), (585, 373), (448, 373)),
    ((652, 266), (785, 266), (783, 373), (646, 373)),
    ((440, 402), (582, 402), (568, 519), (426, 519)),
    ((641, 402), (782, 402), (778, 519), (636, 519)),
    ((419, 553), (569, 553), (555, 685), (401, 685)),
    ((630, 553), (782, 553), (778, 685), (624, 685)),
)
FOUR_ROW_SELECTED_LEFT = (
    ((470, 165), (603, 165), (597, 265), (456, 265)),
    ((652, 165), (787, 165), (784, 265), (646, 265)),
    ((452, 292), (591, 292), (581, 404), (436, 404)),
    ((645, 291), (789, 291), (786, 403), (639, 403)),
    ((427, 435), (581, 435), (573, 561), (414, 561)),
    ((634, 434), (787, 434), (786, 561), (627, 561)),
    ((405, 593), (564, 593), (554, 733), (386, 733)),
    ((626, 593), (786, 593), (787, 734), (614, 734)),
)
DEST = np.float32(((0, 0), (99, 0), (99, 99), (0, 99)))
HAT_ROWS = {3: (100, 242, 404), 4: (84, 172, 270, 392)}
ARROW_ROWS = {3: (108, 263, 434), 4: (52, 175, 325, 512)}
RAFT_EDGES = ((7, 7), (50, 7), (92, 7), (7, 50), (92, 50), (7, 92), (50, 92), (92, 92))
# The nameplates cover these probes on the front row, in column order.
NAMEPLATE_EDGES = {3: ((5,), (), (), (7,)), 4: ((5, 6), (), (), (6, 7))}
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


@lru_cache(maxsize=4)
def board_quads(rows, selected):
    if rows == 4:
        return tuple(quads(FOUR_ROW_SELECTED_LEFT if selected else FOUR_ROW_LEFT))
    if rows != 3:
        raise VisionError("尚未確認這個棋盤的浮台位置")
    left = SELECTED_LEFT if selected else QUADS_LEFT
    return tuple(tuple((x, y - 30) for x, y in quad) for quad in quads(left))


@lru_cache(maxsize=4)
def transforms(selected, rows=3):
    return tuple(cv2.getPerspectiveTransform(np.float32(quad), DEST)
                 for quad in board_quads(rows, selected))


def tile(frame, index, selected=False, *, rows=3):
    return cv2.warpPerspective(frame, transforms(selected, rows)[index], (100, 100))


def point(index, selected=False, *, rows=3):
    tl, tr, br, bl = board_quads(rows, selected)[index]
    return (round((tl[0] + tr[0] + 2 * br[0] + 2 * bl[0]) / 6),
            round((tl[1] + tr[1] + 2 * br[1] + 2 * bl[1]) / 6))


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


def raft_rim(frame, quad):
    _, _, right, left = quad
    x, y = ((a + b) // 2 for a, b in zip(left, right))
    b, g, r = bgr(frame[y+5:y+16, x-52:x+52])
    rim = (b > 183) & (b-r > 100) & (b-g > 70)
    b, g, r = bgr(frame[y-20:y-8, x-52:x+52])
    deck = ((b > 163) & (g > 133) & (r > 116)
            | (b > 180) & (g > 105) & (r < 90)
            | (r > 185) & (g > 65) & (g < 160) & (b < 100))
    return rim.mean() > .22 and deck.mean() > .40


def board_rows(frame):
    matches = {}
    for rows in HAT_ROWS:
        rims = [raft_rim(frame, quad) for quad in board_quads(rows, False)]
        matches[rows] = tuple(sum(rims[i:i+4]) for i in range(0, len(rims), 4))
    # The bottom rows overlap in the two projections, so use higher rows to tell them apart.
    back, middle, front = matches[3]
    three = front >= 2 and (middle >= 2 or (back >= 3 and middle >= 1 and front >= 3))
    four = sum(hit >= 2 for hit in matches[4][:3]) >= 2 and matches[4][3] >= 2
    if three == four:
        raise VisionError("尚未確認棋盤的浮台排數")
    return 3 if three else 4


def selected_layout_visible(frame, rows):
    if rows == 3:
        return True
    rims = [raft_rim(frame, quad) for quad in board_quads(rows, True)]
    return all(sum(rims[i:i+4]) >= 2 for i in range(0, len(rims), 4))


def back_row_obscured(frame):
    # The danger banner covers back-row hats while leaving the turn legend visible.
    for left, right in ((510, 675), (1000, 1135)):
        b, g, r = bgr(frame[88:116, left:right])
        band = ((b >= 96) & (b <= 143) & (g >= 43) & (g <= 94)
                & (b-g >= 40) & (abs(r-g) < 12))
        if band.mean() <= .32:
            return False
    return True


def raft_markers(raster, *, covered=(), tolerance=0.):
    markers = []
    weak_orange = []
    for edge, (x, y) in enumerate(RAFT_EDGES):
        if edge in covered:
            markers.append(None)
            continue
        b, g, r = bgr(raster[y-4:y+5, x-4:x+5])
        orange = (r > 200) & (g > 65) & (g < 153) & (b < 90)
        strengths = (((b > 170) & (g > 120) & (g < 185) & (r < 80)).mean(),
                     orange.mean(),
                     ((b > 164) & (r > 147) & (abs(b-r) < 45) & (abs(g-r) < 35)).mean())
        winner = int(np.argmax(strengths))
        confidence = .48 - .12*tolerance
        marker = (BLUE, ORANGE, 0)[winner] if strengths[winner] > confidence else None
        if marker == ORANGE and (orange & (g < 125)).mean() <= confidence:
            weak_orange.append(len(markers))
        markers.append(marker)
    if BLUE in markers:
        # A bright hammer can cover one tile edge without changing its team.
        for edge in weak_orange:
            markers[edge] = None
    return markers


def raft_evidence(markers, *, tolerance=0.):
    blue, orange = markers.count(BLUE), markers.count(ORANGE)
    visible = sum(mark is not None for mark in markers)
    painted, other = max(blue, orange), min(blue, orange)
    if not painted or (other and (other != 1 or painted < 2)):
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
        if white_misses <= (0 if other else 1 + tolerance) or (kind == KING and not other and painted >= 3):
            # A crown's silhouette is nearly symmetric. Several same-color edge marks
            # identify its team despite pale hair or reflections over the other edges.
            compatible.append(side * kind)
        if white_misses == 0:
            exact.append(side * kind)
    unique = exact[0] if not other and len(exact) == 1 and visible >= 4 else None
    return TileEvidence(tuple(compatible), unique, painted, visible, mixed=bool(other))


def single_mark_hat(patch, row, markers, choices, *, tolerance=0.):
    # An occluded deck can still confirm the side when its visible mark agrees with the hat.
    painted = [(i, mark) for i, mark in enumerate(markers) if mark in (BLUE, ORANGE)]
    if len(painted) != 1:
        return None
    edge, side = painted[0]
    # The undo control can cover the back-row turtle's shell and the opposite raft edge.
    clipped = choices == (0,) and row == 0 and markers.count(0) >= 3
    kind = TURTLE if clipped else abs(choices[0])
    if not kind or not MOVE_DIAGRAMS[kind][edge if side == BLUE else MIRROR_EDGES[edge]]:
        return None
    hat = next((candidate for candidate in describe(patch, row, tolerance=tolerance)
                if candidate.kind == kind), None)
    if hat is None or (clipped and hat.area < 900 - 180*tolerance):
        return None
    blue, orange = pose_costs(hat.pose, references()[kind])
    cost, reverse = (blue, orange) if side == BLUE else (orange, blue)
    maximum, difference = (.12, .025) if clipped else (.09, .018)
    return side * kind if cost < maximum + .02*tolerance and reverse - cost > difference*(1 - .35*tolerance) else None


def resolve_hat_side(patch, row, markers, kind, *, tolerance=0.):
    predicted = pick_side(patch, (kind, -kind))
    painted = [(edge, mark) for edge, mark in enumerate(markers) if mark in (BLUE, ORANGE)]
    if not painted:
        return predicted
    side = painted[0][1]
    pattern = MOVE_DIAGRAMS[kind]
    if not all(mark == side and pattern[edge if side == BLUE else MIRROR_EDGES[edge]]
               for edge, mark in painted):
        return predicted

    # Shadows and reflections can make a printed mark look white. Corroborate
    # the colored marks with the hat profile before trusting a partial pattern.
    hat = next((hat for hat in describe(patch, row, tolerance=tolerance) if hat.kind == kind), None)
    if hat is not None:
        blue, orange = pose_costs(hat.pose, references()[kind])
        cost, reverse = (blue, orange) if side == BLUE else (orange, blue)
        minimum_gap = .012 if len(painted) == 1 else .008
        if cost <= .08 + .02*tolerance and reverse - cost >= minimum_gap*(1 - .35*tolerance):
            return side * kind
    if len(painted) >= 2 and predicted == -side * kind:
        # Neither source is decisive once several aptly positioned marks contradict the model.
        return None
    return predicted


def observe_board(frame, *, tracking=False, rows=None, tolerance=0.):
    if rows is None:
        rows = board_rows(frame) if is_ready(frame) else 3
    if back_row_obscured(frame):
        raise VisionError("等待提示移開後排棋帽")
    for index in range(rows * 4):
        row = index // 4
        x, _ = point(index, rows=rows)
        y = HAT_ROWS[rows][row]
        covered = NAMEPLATE_EDGES[rows][index % 4] if row == rows - 1 else ()
        markers = raft_markers(tile(frame, index, rows=rows), covered=covered, tolerance=tolerance)
        floor = raft_evidence(markers, tolerance=tolerance)
        if rows == 4 and row == 0:
            # The extra row is farther from the camera. Match its hats at the normal scale.
            patch = cv2.resize(frame[y-39:y+39, x-98:x+98], (230, 91))
        else:
            patch = frame[y-46:y+45, x-115:x+115]
        choices = observe(patch, index, floor=floor, tracking=tracking, tolerance=tolerance)
        if (rows == 4 or covered) and floor and floor.painted == 1 and (len(choices) > 1 or choices == (0,)):
            if (marked := single_mark_hat(patch, row, markers, choices, tolerance=tolerance)) is not None:
                choices = (marked,)
        uncovered_edges = len(RAFT_EDGES) - len(covered)
        if len(choices) > 1 and markers.count(0) >= min(7, uncovered_edges) and floor is None:
            # A nearly unmarked deck excludes a neighboring hat leaking into this crop.
            if abs(choices[0]) != TURTLE or (markers[3] == markers[4] == 0):
                choices = (0,)
        if rows == 4 and not tracking and choices == (0,) and floor and (
                floor.painted >= 2 or markers[3] == ORANGE or markers[4] == BLUE):
            raise VisionError(f"尚未確認 {square(index)} 的棋帽")
        if not tracking and len(choices) == 2 and abs(choices[0]) != KING:
            if (piece := resolve_hat_side(patch, row, markers, abs(choices[0]), tolerance=tolerance)) is not None:
                choices = (piece,)
        yield choices


def read_board(frame, *, rows=None, tolerance=0.):
    observations = list(observe_board(frame, rows=rows, tolerance=tolerance))
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


def match_position(frame, candidates, *, previous, hands, tolerance=0.):
    candidates = {pos for pos in candidates if (pos.blue, pos.orange) == hands}
    if not candidates:
        raise VisionError("預期狀態為空")
    observations = tuple(observe_board(frame, tracking=True, rows=previous.rows, tolerance=tolerance))

    def hidden_count(pos):
        hidden = 0
        for old, piece, choices in zip(previous.board, pos.board, observations):
            if piece in choices:
                continue
            if not (piece and piece == old and choices == (0,)):
                return None
            hidden += 1
            if hidden > 1:
                return None
        return hidden

    ranked = [(hidden, candidate) for candidate in candidates
              if (hidden := hidden_count(candidate)) is not None]
    fewest_hidden = min((hidden for hidden, _ in ranked), default=0)
    matching = [candidate for hidden, candidate in ranked if hidden == fewest_hidden]
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


def highlighted(frame, target, *, rows=3):
    blue, green, red = bgr(tile(frame, target, True, rows=rows)[19:82, 18:83])
    return ((blue > 185) & (green > 145) & (blue - green > 10) & (green - red > 45)).mean() > .21


def source_arrow(frame, origin, *, rows=3):
    x, _ = point(origin, selected=True, rows=rows)
    y = ARROW_ROWS[rows][origin // 4]
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


def hand_read(frame, side, *, tolerance=0.):
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
        valid = (mask & (s > 90 - 12*tolerance) & (v > 105 - 12*tolerance)).astype(np.uint8)
        _, _, stats, _ = cv2.connectedComponentsWithStats(valid)
        for x, y, w, ch, area in stats[1:]:
            if not (35 - 6*tolerance <= w <= 108 + 6*tolerance and ch >= 30 - 5*tolerance
                    and area >= 450 - 100*tolerance and y + ch >= 36 - 4*tolerance):
                continue
            center = int(x + w // 2 + left)
            slot = round(side * (center - first) / spacing)
            if not (0 <= slot < len(centers) and abs(center - centers[slot]) <= 25 + 5*tolerance):
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


def hand_inventory(frame, *, tolerance=0.):
    return tuple(tuple(sorted(piece for _, _, piece in hand_read(frame, side, tolerance=tolerance)))
                 for side in (BLUE, ORANGE))


def read_position(frame, *, rows=None, tolerance=0.):
    if not is_ready(frame):
        raise VisionError("尚未確認藍方回合與單人棋盤。")
    board = read_board(frame, rows=rows, tolerance=tolerance)
    return Position(board, *hand_inventory(frame, tolerance=tolerance))
