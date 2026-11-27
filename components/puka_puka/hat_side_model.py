"""CPU model for resolving the side of an already identified hat."""

from functools import cache
from pathlib import Path
from zipfile import BadZipFile

import cv2
import numpy as np


HOG = cv2.HOGDescriptor((96, 48), (16, 16), (8, 8), (8, 8), 9)
COLOR_RANGES = (
    (0, 9, 145),
    (175, 179, 145),
    (108, 130, 128),
    (142, 174, 93),
    (37, 78, 100),
    (19, 36, 125),
)


def features(patch):
    image = cv2.resize(patch[:, 27:203], (96, 48), interpolation=cv2.INTER_AREA)
    gradient = HOG.compute(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)).ravel()
    hue, saturation, value = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).transpose(2, 0, 1)
    masks = []
    for low, high, minimum_saturation in COLOR_RANGES:
        valid = (hue >= low) & (hue <= high) & (saturation > minimum_saturation) & (value > 105)
        mask = cv2.resize(valid.astype(np.float32), (16, 8), interpolation=cv2.INTER_AREA)
        masks.append(.5 * mask.ravel())
    return np.concatenate((gradient, *masks))


@cache
def weights_file():
    try:
        with np.load(Path(__file__).with_name("hat_side_model.npz"), allow_pickle=False) as archive:
            weights, biases, classes, pairs = (archive[key] for key in ("weights", "biases", "classes", "pairs"))
    except (OSError, ValueError, KeyError, BadZipFile):
        return None
    feature_count = HOG.getDescriptorSize() + 16 * 8 * len(COLOR_RANGES)
    if (weights.shape != (55, feature_count) or biases.shape != (55,)
            or classes.shape != (11,) or pairs.shape != (55, 2)
            or not np.issubdtype(pairs.dtype, np.integer)
            or pairs.min() < 0 or pairs.max() >= len(classes)):
        return None
    return weights, biases, classes, pairs


def pick_side(patch, candidates):
    model = weights_file()
    if model is None:
        return None
    weights, biases, classes, pairs = model
    margins = weights @ features(patch) + biases
    if not np.isfinite(margins).all():
        return None
    pair_winners = np.where(margins > 0, pairs[:, 0], pairs[:, 1])
    votes = np.bincount(pair_winners, minlength=len(classes))
    winner = int(classes[votes.argmax()])
    if winner not in candidates or np.count_nonzero(votes == votes.max()) != 1:
        return None
    # Require the direct comparison between the two candidate sides to agree with the overall vote.
    direct = np.flatnonzero(np.isin(classes[pairs], candidates).all(axis=1))
    if direct.size == 1 and margins[direct[0]] != 0 and classes[pair_winners[direct[0]]] == winner:
        return winner
    return None
