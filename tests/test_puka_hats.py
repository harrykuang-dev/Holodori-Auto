"""Keep chess-board reads tied to the visible hats and legal positions."""

from importlib import import_module
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np


COMPONENT = Path(__file__).resolve().parents[1] / "components" / "puka_puka"
with patch.object(sys, "path", [str(COMPONENT), *sys.path]):
    solver = import_module("solver")
    vision = import_module("vision")
    hats = import_module("hats")


class RaftHatTests(unittest.TestCase):
    def setUp(self):
        self.frame = np.zeros((vision.HEIGHT, vision.WIDTH, 3), dtype=np.uint8)
        self.before = solver.Position((0, 0, 2, 5, 3, 0, -4, 0, 1, 2, -1, -3), turn=solver.ORANGE)
        self.expected = self.before.next(solver.Move(6, 5))
        self.alternative = self.before.next(solver.Move(11, 7))

    def test_each_hat_is_read_in_both_directions(self):
        for kind, poses in hats.references().items():
            with self.subTest(kind=kind):
                for reflected, expected in ((False, kind), (True, -kind)):
                    pose = poses[0, :, :, ::-1] if reflected else poses[0]
                    observation = hats.Hat(kind, pose, 2600, 150)
                    with patch.object(hats, "describe", return_value=(observation,)):
                        self.assertEqual(hats.observe(self.frame, 0), (expected,))

    def test_hatless_square_does_not_use_the_printed_move_pattern(self):
        for color in ((226, 151, 0), (22, 110, 237)):
            self.frame[230:348, 780:960] = color
            self.assertEqual(tuple(vision.observe_board(self.frame)), ((0,),) * 12)

    def test_d1_reads_any_hat_partly_covered_by_the_top_right_controls(self):
        for kind, poses in hats.references().items():
            with self.subTest(kind=kind):
                clipped_hat = hats.Hat(kind, poses[0], hats.MIN_AREAS[kind] - 1, 137)
                with (patch.object(hats, "describe", return_value=(clipped_hat,)),
                      patch.object(hats, "pose_costs", return_value=(.07, .021)) as costs):
                    self.assertEqual(hats.observe(self.frame, 3), (-kind,))
                    self.assertEqual(hats.observe(self.frame, 2), (0,))
                    costs.return_value = (.07, .035)
                    self.assertEqual(hats.observe(self.frame, 3), (0,))
                    costs.return_value = (.022, .021)
                    self.assertEqual(hats.observe(self.frame, 3), (kind, -kind))

    def test_indeterminate_hats_use_both_crowns_or_wait(self):
        observations = [(p,) for p in self.before.board]
        observations[8] = (solver.KING, -solver.KING)
        with patch.object(vision, "observe_board", return_value=observations):
            self.assertEqual(vision.read_board(self.frame), self.before.board)
            observations[10] = (solver.KING, -solver.KING)
            with self.assertRaises(vision.VisionError):
                vision.read_board(self.frame)

    def test_reply_uses_legal_play_to_resolve_a_partly_hidden_hat(self):
        observed = [(p,) for p in self.expected.board]
        observed[5] = (solver.TURTLE, -solver.TURTLE)
        candidates = [self.expected, self.alternative, self.before]
        with patch.object(vision, "observe_board", return_value=observed):
            self.assertEqual(vision.match_position(self.frame, candidates, previous=self.before.board),
                             self.expected)
            observed[5] = (solver.TURTLE,)
            with self.assertRaises(vision.VisionError):
                vision.match_position(self.frame, candidates, previous=self.before.board)

    def test_initial_read_accepts_an_endgame_without_reserves(self):
        board = (0, 0, solver.DOLPHIN, 0, 0, solver.KING, 0, -solver.KING,
                 0, solver.DOLPHIN, -solver.TURTLE, 0)
        with (patch.object(vision, "is_ready", return_value=True),
              patch.object(vision, "hand_read", return_value=[]),
              patch.object(vision, "observe_board", return_value=[(piece,) for piece in board])):
            self.assertEqual(vision.read_position(self.frame), solver.Position(board))
