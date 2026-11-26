"""Build the raft hat reference bank from annotated local captures.

Each NPZ input supplies BGR `rois` (91×230), zero-based `index` values
in row-major order, and signed `board` piece labels (zero for empty).
Only compact silhouette and highlight descriptors are written to the bank.
"""

import argparse
from pathlib import Path
import sys

import numpy as np


COMPONENT = Path(__file__).resolve().parents[1] / "components" / "puka_puka"
sys.path.insert(0, str(COMPONENT))

from hats import POSE_WEIGHTS, describe
from solver import GOLD, KING, WHALE


def representatives(samples):
    pool = np.unique(np.rint(np.array(samples) * 255).astype(np.uint8), axis=0)
    poses = pool.astype(np.float32) / 255

    def distance(reference):
        return np.mean((poses-reference)**2 * POSE_WEIGHTS, axis=(1, 2, 3))

    chosen = [int(distance(poses.mean(axis=0)).argmin())]
    nearest = distance(poses[chosen[0]])
    while len(chosen) < min(len(pool), 96) and nearest.max() > .00065:
        next_pose = int(nearest.argmax())
        chosen.append(next_pose)
        nearest = np.minimum(nearest, distance(poses[next_pose]))
    return pool[chosen]


def calibrate(sources, output):
    samples = {str(kind): [] for kind in range(KING, GOLD + 1)}
    samples["wide_whale"] = []
    for source in sources:
        with np.load(source, allow_pickle=False) as data:
            for image, index, piece in zip(data["rois"], data["index"], data["board"], strict=True):
                if not piece:
                    continue
                kind = abs(piece)
                hat = next((hat for hat in describe(image, index//4) if hat.kind == kind), None)
                if hat is not None:
                    samples[str(kind)].append(hat.pose if piece > 0 else hat.pose[:, :, ::-1])
                if kind == WHALE:
                    wide = next(describe(image, index//4, wide_whale=True), None)
                    if wide is not None:
                        samples["wide_whale"].append(wide.pose if piece > 0 else wide.pose[:, :, ::-1])
    if missing := [kind for kind, poses in samples.items() if not poses]:
        raise ValueError(f"Missing annotated hats for {missing}")
    np.savez_compressed(output, **{kind: representatives(poses) for kind, poses in samples.items()})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, default=COMPONENT / "hat_reference.npz")
    args = parser.parse_args()
    calibrate(args.sources, args.output)
