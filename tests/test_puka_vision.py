"""Check screen and turn detection using graphics with no labels."""

from importlib import import_module
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

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

    def test_reward_layout_requires_the_turquoise_band(self):
        self.frame[328:380, 100:1510] = (226, 217, 109)
        self.assertEqual(stages.classify_screen(self.frame), 'reward')
        self.frame[328:380, 100:800] = 0
        self.assertIsNone(stages.classify_screen(self.frame))
