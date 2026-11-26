"""Decode images without passing Windows Unicode paths to OpenCV."""
from pathlib import Path

import cv2
import numpy as np


def read_image(path, flags=cv2.IMREAD_COLOR):
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    return cv2.imdecode(np.frombuffer(data, dtype=np.uint8), flags) if data else None
