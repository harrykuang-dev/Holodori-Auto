"""Read chess hats from color, silhouette and facing direction."""

from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import cv2
import numpy as np

from solver import BLUE, DOLPHIN, GOLD, KING, ORANGE, TURTLE, WHALE


class Hat(NamedTuple):
    kind: int
    pose: np.ndarray
    area: int
    saturation: float


class TileEvidence(NamedTuple):
    compatible: tuple[int, ...]
    exact: int | None
    painted: int
    visible: int
    mixed: bool = False


@lru_cache(maxsize=2)
def references(*, wide_whale=False):
    with np.load(Path(__file__).with_name("hat_reference.npz"), allow_pickle=False) as archive:
        keys = {WHALE: "wide_whale"} if wide_whale else {kind: str(kind) for kind in MIN_AREAS}
        return {kind: archive[key].astype(np.float32) / 255 for kind, key in keys.items()}


DILATION = np.ones((13, 13), np.uint8)
CLOSING = np.ones((5, 5), np.uint8)
POSE_WIDTH = 16
POSE_HEIGHT = 10
MIN_AREAS = {KING: 290, WHALE: 2300, DOLPHIN: 2300, TURTLE: 2300, GOLD: 420}
POSE_WEIGHTS = np.float32([1, .12])[None, :, None, None]


def describe(patch, row, *, wide_whale=False, tolerance=0.):
    """Extract the dominant shape of each hat color near a square."""
    radius = 64 + row * 5
    extra = 26 if wide_whale else 0
    patch = (patch[:, 115-radius-extra:116+radius+extra] if wide_whale
             else patch[16:76, 115-radius:116+radius])
    h, s, v = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV).transpose(2, 0, 1)
    colors = {
        KING: ((h <= 9) | (h >= 175)) & (s > 145 - 15*tolerance),
        WHALE: (h >= 108) & (h <= 130) & (s > 128 - 15*tolerance),
        DOLPHIN: (h >= 142) & (h < 175) & (s > 93 - 15*tolerance),
        TURTLE: (h >= 37) & (h <= 78) & (s > 100 - 15*tolerance),
        GOLD: (h >= 19) & (h < 37) & (s > 125 - 15*tolerance),
    }
    if wide_whale:
        colors = {WHALE: colors[WHALE]}
    for kind, color in colors.items():
        count, labels, stats, _ = cv2.connectedComponentsWithStats(np.uint8(color & (v > 105 - 12*tolerance)))
        if count <= 1:
            continue
        if wide_whale:
            # Expand the shape that was visible in the original crop.
            overlap = np.bincount(labels[16:76, extra:-extra].ravel(), minlength=count)
            if not overlap[1:].any():
                continue
            largest = np.argmax(overlap[1:]) + 1
        else:
            largest = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
        x, y, width, height, size = stats[largest]
        if size < 90 - 18*tolerance or width < 18 - 3*tolerance or height < 12 - 2*tolerance:
            continue
        component = cv2.morphologyEx(np.uint8(labels == largest), cv2.MORPH_CLOSE, CLOSING)
        near = cv2.dilate(component, DILATION)
        margin_x, margin_y = round(width * .13), round(height * .15)
        ys = slice(max(0, y-margin_y), y+height+margin_y)
        xs = slice(max(0, x-margin_x), x+width+margin_x)
        # Local highlights often outline the snout or eyes. Red crowns also have gold trim.
        detail = ((s < 98) & (v > 139)) if kind != KING else ((s > 133) & (h >= 14) & (h < 45))
        pose = np.array([cv2.resize(layer[ys, xs].astype(np.float32), (POSE_WIDTH, POSE_HEIGHT),
                                    interpolation=cv2.INTER_AREA)
                         for layer in (component, near * detail)])
        yield Hat(kind, pose, int(size), float(np.median(s[labels == largest])))


def pose_costs(pose, bank):
    def cost(observation):
        return float(np.mean((bank - observation)**2 * POSE_WEIGHTS, axis=(1, 2, 3)).min())

    return cost(pose), cost(pose[:, :, ::-1])


def pose_side(blue, orange, tolerance=0.):
    if abs(blue - orange) <= max(.003, min(blue, orange) * .8) * (1 - .35*tolerance):
        return None
    return BLUE if blue < orange else ORANGE


def observe(patch, index, *, floor=None, tracking=False, tolerance=0.):
    """Return the admissible signed pieces, or (0,) for an empty square."""
    detected = []
    bank = references()
    wider = None
    for hat in describe(patch, index // 4, tolerance=tolerance):
        minimum_area = MIN_AREAS[hat.kind] * (1 - .22*tolerance)
        if hat.kind == GOLD and hat.area < 850 - 120*tolerance and hat.saturation > 155 + 12*tolerance:
            continue
        blue, orange = pose_costs(hat.pose, bank[hat.kind])
        # A small component can be a hat clipped by the HUD or part of a hammer.
        if hat.area >= minimum_area:
            maximum_cost = .09
        elif index == 3:
            maximum_cost = .03  # The top-right controls can cover most of D1.
            facing = hat.kind if blue < orange else -hat.kind
            # An incomplete silhouette can still agree with several visible
            # movement marks of the same piece and side.
            if (floor and not floor.mixed and floor.painted >= 3
                    and hat.area * 2 >= minimum_area
                    and facing in floor.compatible and abs(blue - orange) >= .003 - .001*tolerance):
                maximum_cost = .09
        else:
            maximum_cost = .008
        if min(blue, orange) > maximum_cost + .025*tolerance:
            if (hat.kind != WHALE or hat.area < minimum_area
                    or not floor or not any(abs(piece) == WHALE for piece in floor.compatible)):
                continue
            wider = next(describe(patch, index // 4, wide_whale=True, tolerance=tolerance), None)
            if wider is None:
                continue
            wide_blue, wide_orange = pose_costs(wider.pose, references(wide_whale=True)[WHALE])
            facing = WHALE if blue < orange else -WHALE if orange < blue else None
            wide_facing = WHALE if wide_blue < wide_orange else -WHALE if wide_orange < wide_blue else None
            # Two crops and clean deck marks must agree before accepting a marginal whale.
            exact_floor = floor.exact == facing and floor.painted >= 3
            partial_reply = tolerance > 0 and floor.exact is None and floor.painted >= 3 - tolerance
            supported = (facing == wide_facing and facing in floor.compatible and not floor.mixed
                         and (exact_floor or partial_reply) and min(blue, orange) <= .10 + .018*tolerance
                         and min(wide_blue, wide_orange) <= .085 + .018*tolerance)
            if min(wide_blue, wide_orange) > .065 + .02*tolerance and not supported:
                continue
            blue, orange = wide_blue, wide_orange
        detected.append((hat.area, hat.kind, blue, orange))
    if not detected:
        if floor and floor.exact is not None and floor.painted >= 3 and floor.visible >= 6 - tolerance:
            return (floor.exact,)
        return (0,)
    primary = max(detected)
    if floor and floor.exact is not None and floor.painted >= 2:
        # A distinctive pattern can distinguish two plausible hat matches.
        alternative = next((match for match in detected if match[1] == abs(floor.exact)), None)
        if alternative is not None and min(alternative[2:]) <= min(primary[2:]) + .012 + .01*tolerance:
            primary = alternative
    _, kind, blue, orange = primary
    side = pose_side(blue, orange, tolerance)
    if floor:
        matching = [piece for piece in floor.compatible if abs(piece) == kind]
        enough_color = not floor.mixed or floor.painted >= 3
        can_override = floor.painted >= 2 and not floor.mixed
        if len(matching) == 1 and enough_color and (side is None or can_override):
            return (matching[0],)
    if tracking:
        return (kind, -kind)
    if side is None and kind == WHALE and wider is None:
        wide = next(describe(patch, index // 4, wide_whale=True, tolerance=tolerance), None)
        if wide is not None:
            costs = pose_costs(wide.pose, references(wide_whale=True)[WHALE])
            if min(costs) <= .065 + .02*tolerance:
                side = pose_side(*costs, tolerance=tolerance)
    return (kind, -kind) if side is None else (side * kind,)
