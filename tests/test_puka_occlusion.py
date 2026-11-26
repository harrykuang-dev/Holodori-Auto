"""Verify that occluded rafts yield a move only with enough visible evidence."""

from importlib import import_module
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np


COMPONENT = Path(__file__).resolve().parents[1] / 'components' / 'puka_puka'
with patch.object(sys, 'path', [str(COMPONENT), *sys.path]):
    solver = import_module('solver')
    vision = import_module('vision')


class OccludedRaftTests(unittest.TestCase):
    def setUp(self):
        self.frame = np.zeros((1, 1, 3), dtype=np.uint8)
        self.raster = np.zeros((100, 100, 3), dtype=np.uint8)
        self.turtle = -solver.TURTLE
        self.hats = {self.turtle: .90, -self.turtle: .37}
        self.before = solver.Position((0, 0, 2, 5, 3, 0, -4, 0, 1, 2, -1, -3), turn=solver.ORANGE)
        self.expected = self.before.next(solver.Move(6, 5))
        self.alternative = self.before.next(solver.Move(11, 7))

    def test_hidden_marker_uses_only_a_strong_noncontradictory_hat(self):
        exposed = [None] * 7 + [0]
        self.assertEqual(vision.classify(exposed, self.hats, self.raster), self.turtle)
        for other in (.65, .90):
            with self.assertRaises(vision.VisionError):
                vision.classify(exposed, {self.turtle: .90, -self.turtle: other}, self.raster)
        with self.assertRaises(vision.VisionError):
            vision.classify([None] * 8, self.hats, self.raster)

        exposed[3] = 0  # The orange turtle needs a painted left edge here.
        with self.assertRaises(vision.VisionError):
            vision.classify(exposed, self.hats, self.raster)

    def test_turtle_with_a_neutral_sample_over_its_hidden_stripe(self):
        for piece in (solver.TURTLE, -solver.TURTLE):
            with self.subTest(piece=piece):
                raster = np.full_like(self.raster, (239, 232, 223))
                raster[3:12, 46:55] = 0
                raster[3:12, 88:97] = 0
                stripe, opposite = (slice(88, 97), slice(3, 12)) if piece > 0 else (slice(3, 12), slice(88, 97))
                raster[46:55, stripe] = (177, 208, 211)
                marks = vision.tile_markers(raster)
                self.assertEqual(marks, [0, None, None, 0, 0, 0, 0, 0])
                self.assertEqual(vision.classify(marks, {piece: .70, -piece: .42}, raster), piece)

                with self.assertRaises(vision.VisionError):
                    vision.classify(marks, {piece: .70, -piece: .48}, raster)
                raster[46:55, opposite] = (177, 208, 211)
                with self.assertRaises(vision.VisionError):
                    vision.classify(vision.tile_markers(raster), {piece: .70, -piece: .42}, raster)
                raster[46:55, stripe] = raster[46:55, opposite] = (239, 232, 223)
                with self.assertRaises(vision.VisionError):
                    vision.classify(vision.tile_markers(raster), {piece: .70, -piece: .42}, raster)

    def test_legal_reply_can_recover_when_its_target_and_other_tiles_are_hidden(self):
        marks = [list(vision.pattern(piece)) for piece in self.expected.board]
        marks[5] = [None] * 7 + [0]
        marks[7] = [None] * 5 + [0, 0, 0]  # Only the unused alternative changes D2.
        candidates = [self.expected, self.alternative]
        b2_hats = self.hats

        def scores(_frame, index):
            return b2_hats if index == 5 else {self.turtle: 0, -self.turtle: 0}

        with patch.object(vision, 'read_board', side_effect=vision.VisionError), \
             patch.object(vision, 'marker_observations', return_value=marks), \
             patch.object(vision, 'tile', return_value=self.raster), \
             patch.object(vision, 'hat_scores', side_effect=scores):
            self.assertEqual(vision.match_position(self.frame, candidates, previous=self.before.board),
                             self.expected)
            self.assertEqual(vision.match_position(self.frame, [*candidates, self.before],
                                                   previous=self.before.board), self.expected)
            b2_hats = {self.turtle: .53, -self.turtle: .48}
            with self.assertRaises(vision.VisionError):
                vision.match_position(self.frame, [*candidates, self.before], previous=self.before.board)
            b2_hats = self.hats
            marks[5] = [solver.BLUE, solver.BLUE, 0, None, 0, None, None, 0]
            with self.assertRaisesRegex(vision.VisionError, 'B2'):
                vision.match_position(self.frame, candidates, previous=self.before.board)

    def test_complete_read_does_not_fall_back_after_a_contradiction(self):
        with patch.object(vision, 'read_board', return_value=self.alternative.board), \
             patch.object(vision, 'marker_observations') as observations:
            with self.assertRaises(vision.VisionError):
                vision.match_position(self.frame, [self.expected], previous=self.before.board)
            observations.assert_not_called()
