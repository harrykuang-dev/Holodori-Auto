"""Check screen and turn detection using graphics with no labels."""

from importlib import import_module
from itertools import count
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

import cv2
import numpy as np


COMPONENT = Path(__file__).resolve().parents[1] / 'components' / 'puka_puka'
with patch.object(sys, 'path', [str(COMPONENT), *sys.path]):
    pilot = import_module('pilot')
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

    def test_refill_requires_the_item_dialog_and_default_quantity(self):
        self.frame[143:193, 931:1045] = 245
        self.frame[700:757, 930:1085] = (250, 150, 40)
        self.frame[304:389, 1337:1400] = (138, 200, 100)
        self.frame[304:379, 1028:1119] = (240, 168, 50)
        self.frame[575:598, 1100:1124] = 245
        self.frame[816:856, 992:1170] = 245
        self.frame[816:856, 1258:1475] = (240, 168, 50)
        self.assertEqual(stages.classify_screen(self.frame), 'refill')

        self.frame[575:598, 1100:1124] = (230, 224, 201)
        self.assertEqual(stages.classify_screen(self.frame), 'refill_panel')
        self.frame[575:598, 1100:1124] = 245
        self.frame[816:856, 1258:1475] = 175
        self.assertEqual(stages.classify_screen(self.frame), 'refill_panel')
        self.frame[304:379, 1028:1119] = 245
        self.assertNotIn(stages.classify_screen(self.frame), stages.REFILL_STATES)

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

    def test_dolphin_tile_ignores_orange_hammer_covering_one_marker(self):
        raster = np.full((100, 100, 3), (239, 232, 223), dtype=np.uint8)
        samples = {2: (70, 72, 78), 3: (239, 144, 0),
                   6: (54, 133, 229), 7: (70, 72, 78)}
        for marker, color in samples.items():
            x, y = vision.EDGES[marker]
            raster[y-4:y+5, x-4:x+5] = color
        hats = {vision.DOLPHIN: .68, -vision.DOLPHIN: .73}

        self.assertEqual(vision.classify(vision.tile_markers(raster), hats, raster), vision.DOLPHIN)

        x, y = vision.EDGES[6]
        raster[y-4:y+5, x-4:x+5] = (33, 113, 240)
        with self.assertRaises(vision.VisionError):
            vision.classify(vision.tile_markers(raster), hats, raster)


class PukaRefillTests(unittest.TestCase):
    def setUp(self):
        time_ticks = count(step=.2)
        self.enterContext(patch.object(pilot, 'time', SimpleNamespace(monotonic=lambda: next(time_ticks),
                                                                      sleep=lambda _: None)))
        self.enterContext(patch.object(pilot, 'classify_screen', side_effect=lambda scene: scene))
        self.enterContext(patch.object(pilot, 'read_position', return_value='ready position'))

    def game(self, first_scene, *after_click):
        scenes = iter(after_click)
        game = SimpleNamespace(scene=first_scene)
        game.capture = lambda: game.scene
        game.click = Mock(side_effect=lambda *_: setattr(game, 'scene', next(scenes)))
        return game

    def test_refill_is_off_by_default(self):
        game = self.game('refill')
        with self.assertRaisesRegex(pilot.StopPlay, '能量不足'):
            pilot.prepare(game, Mock())
        game.click.assert_not_called()

    def test_refill_retries_the_original_stage(self):
        game = self.game('challenge', 'refill', 'challenge', 'board')
        self.assertEqual(pilot.prepare(game, Mock(), auto_refill=True), ('board', 'ready position'))
        stage = call(*stages.CLICK['challenge'])
        self.assertEqual(game.click.call_args_list, [stage, call(*stages.CLICK['refill']), stage])

    def test_unavailable_or_repeated_refill_stops(self):
        unavailable = self.game('refill_panel')
        with self.assertRaisesRegex(pilot.StopPlay, '一瓶道具'):
            pilot.prepare(unavailable, Mock(), auto_refill=True)
        unavailable.click.assert_not_called()

        repeated = self.game('challenge', 'refill', 'challenge', 'refill')
        with self.assertRaisesRegex(pilot.StopPlay, '補充後仍然需要能量'):
            pilot.prepare(repeated, Mock(), auto_refill=True)
        self.assertEqual(repeated.click.call_args_list.count(call(*stages.CLICK['refill'])), 1)
