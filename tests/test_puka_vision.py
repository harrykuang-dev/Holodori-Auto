"""Check screen and turn detection using graphics with no labels."""

from importlib import import_module
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import cv2
import numpy as np


COMPONENT = Path(__file__).resolve().parents[1] / 'components' / 'puka_puka'
with patch.object(sys, 'path', [str(COMPONENT), *sys.path]):
    stages = import_module('stages')
    vision = import_module('vision')


class PukaScreenTests(unittest.TestCase):
    def setUp(self):
        self.frame = np.zeros((915, 1626, 3), dtype=np.uint8)

    def test_lobby_uses_globe_and_stamina_icon(self):
        self.frame[795:832, 73:127] = (240, 172, 54)
        self.frame[799:814, 80:120] = 255
        self.frame[755:775, 1365:1384] = (152, 222, 104)
        self.frame[805:854, 1280:1525] = (235, 174, 53)
        self.assertEqual(stages.classify_screen(self.frame), 'hub')
        self.frame[755:775, 1365:1384] = 0
        self.assertIsNone(stages.classify_screen(self.frame))

    def test_board_uses_move_diagram_color(self):
        self.frame[112:319, 37:52] = 231
        self.frame[112:319, 218:234] = 231
        self.frame[56:82, 1245:1275] = (220, 162, 36)
        self.frame[53:87, 1442:1469] = 215
        self.frame[113:136, 193:216] = (229, 134, 46)
        self.assertTrue(vision.is_ready(self.frame))
        self.frame[113:136, 193:216] = (55, 168, 241)
        self.assertFalse(vision.is_ready(self.frame))

    def test_board_reads_empty_tile_behind_a_whale_hat(self):
        king, whale, turtle = vision.KING, vision.WHALE, vision.TURTLE
        board = (0, king, 0, -king, 0, 0, 0, 0, 0, whale, turtle, 0)
        white = (239, 232, 223)
        marker_colors = {0: white, vision.BLUE: (241, 146, 0), vision.ORANGE: (30, 110, 234)}

        def paint(index, raster):
            cv2.warpPerspective(raster, vision.transforms(False)[index], (1626, 915),
                                dst=self.frame, flags=cv2.WARP_INVERSE_MAP | cv2.INTER_NEAREST,
                                borderMode=cv2.BORDER_TRANSPARENT)

        for index, piece in enumerate(board):
            raster = np.full((100, 100, 3), white, dtype=np.uint8)
            for (x, y), mark in zip(vision.EDGES, vision.pattern(piece)):
                raster[y-6:y+7, x-6:x+7] = marker_colors[mark]
            if index == 5:
                # The whale on B3 fills the left of B2 and hides all but its right edge.
                raster[:, :60] = (113, 75, 64)
                raster[:28, :43] = (219, 103, 67)
                occluded = raster.copy()
            paint(index, raster)
        x, _ = vision.point(10)
        self.frame[375:429, x-74:x+10] = (71, 207, 64)

        self.assertEqual(vision.read_board(self.frame), board)

        occluded[:, 65:86] = (113, 75, 64)
        paint(5, occluded)
        with self.assertRaisesRegex(vision.VisionError, 'B2'):
            vision.read_board(self.frame)

    def test_reward_layout_requires_the_turquoise_band(self):
        self.frame[328:380, 100:1510] = (226, 217, 109)
        self.assertEqual(stages.classify_screen(self.frame), 'reward')
        self.frame[328:380, 100:800] = 0
        self.assertIsNone(stages.classify_screen(self.frame))
