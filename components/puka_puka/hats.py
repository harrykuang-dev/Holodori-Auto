"""Read chess hats from color, silhouette and facing direction."""

from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import cv2
import numpy as np

from solver import DOLPHIN, GOLD, KING, TURTLE, WHALE


class Hat(NamedTuple):
    kind: int
    pose: np.ndarray
    area: int
    saturation: float


@lru_cache(maxsize=1)
def references():
    with np.load(Path(__file__).with_name("hat_reference.npz"), allow_pickle=False) as archive:
        return {int(key): archive[key].astype(np.float32) / 255 for key in archive.files}


DILATION = np.ones((13, 13), np.uint8)
CLOSING = np.ones((5, 5), np.uint8)
POSE_WIDTH = 16
POSE_HEIGHT = 10
MIN_AREAS = {KING: 290, WHALE: 2300, DOLPHIN: 2300, TURTLE: 2300, GOLD: 420}
POSE_WEIGHTS = np.float32([1, .12])[None, :, None, None]


def describe(patch, row):
    """Extract the dominant shape of each hat color near a square."""
    radius = 64 + row * 5
    patch = patch[16:76, 115-radius:116+radius]
    h, s, v = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV).transpose(2, 0, 1)
    colors = {
        KING: ((h <= 9) | (h >= 175)) & (s > 145),
        WHALE: (h >= 108) & (h <= 130) & (s > 128),
        DOLPHIN: (h >= 142) & (h < 175) & (s > 93),
        TURTLE: (h >= 37) & (h <= 78) & (s > 100),
        GOLD: (h >= 19) & (h < 37) & (s > 125),
    }
    for kind, color in colors.items():
        count, labels, stats, _ = cv2.connectedComponentsWithStats(np.uint8(color & (v > 105)))
        if count <= 1:
            continue
        largest = np.argmax(stats[1:, cv2.CC_STAT_AREA]) + 1
        x, y, width, height, size = stats[largest]
        if size < 90 or width < 18 or height < 12:
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


def observe(patch, index):
    """Return the admissible signed pieces, or (0,) for an empty square."""
    detected = []
    bank = references()
    for hat in describe(patch, index // 4):
        if hat.kind == GOLD and hat.area < 850 and hat.saturation > 155:
            continue
        blue, orange = pose_costs(hat.pose, bank[hat.kind])
        # A small component can be a hat clipped by the HUD or part of a hammer.
        if hat.area >= MIN_AREAS[hat.kind]:
            maximum_cost = .09
        elif index == 3 and hat.kind in (WHALE, DOLPHIN):
            maximum_cost = .03  # The top-right controls can cover most of D1.
        else:
            maximum_cost = .008
        if min(blue, orange) > maximum_cost:
            continue
        detected.append((hat.area, hat.kind, blue, orange))
    if not detected:
        return (0,)
    _, kind, blue, orange = max(detected)
    best = min(blue, orange)
    if abs(blue-orange) <= max(.003, best * .8):
        return (kind, -kind)
    return (kind if blue < orange else -kind,)
