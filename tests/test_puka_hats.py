"""Keep chess-board reads tied to the visible hats and legal positions."""

from importlib import import_module
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import cv2
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

    def test_aligned_corner_marks_resolve_whale_direction(self):
        kind = solver.WHALE
        hat = hats.Hat(kind, hats.references()[kind][0], 5921, 150)
        floor = vision.raft_evidence((1, None, None, 0, None, 1, 0, None))
        self.assertEqual(floor.exact, kind)
        with (patch.object(hats, "describe", return_value=(hat,)),
              patch.object(hats, "pose_costs", return_value=(.078, .082))):
            self.assertEqual(hats.observe(self.frame, 7, floor=floor), (kind,))

    def test_three_matching_corners_can_resolve_an_ambiguous_hat_with_one_outlier(self):
        kind = solver.WHALE
        hat = hats.Hat(kind, hats.references()[kind][0], 7290, 150)
        floor = vision.raft_evidence((-1, None, -1, 0, None, 1, 0, -1))
        self.assertEqual(floor.compatible, (-kind,))
        self.assertIsNone(floor.exact)
        with (patch.object(hats, "describe", side_effect=lambda *_args, **_kwargs: iter((hat,))),
              patch.object(hats, "pose_costs", return_value=(.110, .080))):
            self.assertEqual(hats.observe(self.frame, 8, floor=floor), (-kind,))
        self.assertIsNone(vision.raft_evidence((1, None, -1, 0, None, 1, 0, -1)))

    def test_complete_tile_pattern_selects_between_plausible_hat_kinds(self):
        whale, dolphin = solver.WHALE, solver.DOLPHIN
        bank = hats.references()
        candidates = (hats.Hat(whale, bank[whale][0], 3300, 150),
                      hats.Hat(dolphin, bank[dolphin][0], 3800, 150))
        floor = vision.raft_evidence((-1, 0, -1, 0, 0, -1, 0, -1))
        with (patch.object(hats, "describe", return_value=candidates),
              patch.object(hats, "pose_costs", side_effect=((.07, .021), (.019, .07)))):
            self.assertEqual(hats.observe(self.frame, 7, floor=floor), (-whale,))

    def test_single_stripe_needs_hat_support(self):
        floor = vision.raft_evidence((0, 0, 0, 0, 1, 0, 0, 0))
        self.assertEqual(floor.exact, solver.TURTLE)
        with patch.object(hats, "describe", return_value=()):
            self.assertEqual(hats.observe(self.frame, 0, floor=floor), (0,))

    def test_nameplate_colors_do_not_conflict_with_a_turtles_direction(self):
        kind = solver.TURTLE
        hat = hats.Hat(kind, hats.references()[kind][0], 6200, 150)
        blue, orange = (255, 167, 49), (35, 112, 241)
        for rows in (3, 4):
            for column, side, stripe_x, plate_x, paint, plate, costs in (
                    (0, solver.ORANGE, 7, 7, orange, blue, (.088, .059)),
                    (3, solver.BLUE, 92, 92, blue, orange, (.059, .088))):
                with self.subTest(rows=rows, column=column):
                    index = 4 * (rows - 1) + column
                    raster = np.full((100, 100, 3), 128, dtype=np.uint8)
                    raster[45:56, stripe_x-5:stripe_x+6] = paint
                    raster[87:98, plate_x-5:plate_x+6] = plate
                    inverse = np.linalg.inv(vision.transforms(False, rows)[index])
                    frame = cv2.warpPerspective(raster, inverse, (vision.WIDTH, vision.HEIGHT))
                    with (patch.object(vision, "observe", return_value=(kind, -kind)),
                          patch.object(vision, "describe", return_value=(hat,)),
                          patch.object(vision, "pose_costs", return_value=costs)):
                        observations = tuple(vision.observe_board(frame, rows=rows))
                    self.assertEqual(observations[index], (side * kind,))

    def test_same_color_raft_marks_correct_a_crown_facing_error(self):
        kind = solver.KING
        hat = hats.Hat(kind, hats.references()[kind][0], 943, 150)
        floor = vision.raft_evidence((0, None, -1, None, -1, 0, 0, -1))
        self.assertIn(-kind, floor.compatible)
        with (patch.object(hats, "describe", return_value=(hat,)),
              patch.object(hats, "pose_costs", return_value=(.0106, .0542))):
            self.assertEqual(hats.observe(self.frame, 0, floor=floor), (-kind,))

    def test_wide_whale_profile_recovers_occupancy_with_matching_raft(self):
        kind = solver.WHALE
        hat = hats.Hat(kind, hats.references()[kind][0], 7588, 150)
        for first_corner, expected in ((-1, (-kind,)), (None, (kind, -kind))):
            with self.subTest(first_corner=first_corner):
                floor = vision.raft_evidence((first_corner, None, -1, 0, None, 1, 0, -1))
                with (patch.object(hats, "describe", side_effect=lambda *_args, **_kwargs: iter((hat,))),
                      patch.object(hats, "pose_costs", side_effect=((.1125, .0943), (.0916, .0612)))):
                    self.assertEqual(hats.observe(self.frame, 8, floor=floor), expected)

    def test_well_exposed_unique_pattern_can_recover_a_hidden_hat(self):
        floor = vision.raft_evidence((1, 0, 1, 0, 0, 1, 0, 1))
        with patch.object(hats, "describe", return_value=()):
            self.assertEqual(hats.observe(self.frame, 7, floor=floor), (solver.WHALE,))

    def test_d1_reads_any_hat_partly_covered_by_the_top_right_controls(self):
        for kind, poses in hats.references().items():
            with self.subTest(kind=kind):
                clipped_hat = hats.Hat(kind, poses[0], hats.MIN_AREAS[kind] - 1, 137)
                with (patch.object(hats, "describe", side_effect=lambda *_args, **_kwargs: iter((clipped_hat,))),
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

    def test_model_only_breaks_an_uncertain_nonleader_side_on_direct_reads(self):
        candidates = (solver.TURTLE, -solver.TURTLE)
        observed = [candidates, (solver.DOLPHIN,), (solver.KING, -solver.KING)] + [(0,)] * 9
        with patch.object(vision, "pick_side", return_value=-solver.TURTLE) as pick:
            with patch.object(vision, "observe", side_effect=observed):
                resolved = tuple(vision.observe_board(self.frame, rows=3))
            self.assertEqual(resolved, ((-solver.TURTLE,), *observed[1:]))
            pick.assert_called_once()
            with patch.object(vision, "observe", side_effect=observed):
                tracked = tuple(vision.observe_board(self.frame, rows=3, tracking=True))
            self.assertEqual(tracked, tuple(observed))
            pick.assert_called_once()

    def test_ambiguous_whale_uses_the_direction_from_a_wider_profile(self):
        kind = solver.WHALE
        hat = hats.Hat(kind, hats.references()[kind][0], 5921, 150)
        for wide_costs, expected in (((.034, .072), (kind,)), ((.072, .034), (-kind,)),
                                     ((.035, .036), (kind, -kind)), ((.08, .16), (kind, -kind))):
            with self.subTest(wide_costs=wide_costs):
                with (patch.object(hats, "describe", side_effect=lambda *_args, **_kwargs: iter((hat,))) as describe,
                      patch.object(hats, "pose_costs", side_effect=((.078, .082), wide_costs))):
                    self.assertEqual(hats.observe(self.frame, 7), expected)
                    self.assertTrue(describe.call_args.kwargs["wide_whale"])

    def test_reply_uses_legal_play_to_resolve_a_partly_hidden_hat(self):
        observed = [(p,) for p in self.expected.board]
        observed[5] = (solver.TURTLE, -solver.TURTLE)
        candidates = [self.expected, self.alternative, self.before]
        hands = self.expected.blue, self.expected.orange
        with patch.object(vision, "observe_board", return_value=observed):
            self.assertEqual(vision.match_position(self.frame, candidates, previous=self.before, hands=hands),
                             self.expected)
            observed[5] = (solver.TURTLE,)
            with self.assertRaises(vision.VisionError):
                vision.match_position(self.frame, candidates, previous=self.before, hands=hands)

    def test_deployment_needs_a_visible_hat_and_a_matching_removed_reserve(self):
        kind = solver.WHALE
        previous = solver.Position((0, -1, 0, 0, 3, -kind, 0, 3, 0, 1, 0, 0),
                                   (4, 4), (kind,), solver.ORANGE)
        expected = previous.next(solver.Move(-kind, 8))
        alternative = previous.next(solver.Move(-kind, 10))
        candidates = [previous, expected, alternative]
        observed = [(piece,) for piece in expected.board]
        observed[8] = (kind, -kind)
        with patch.object(vision, "observe_board", return_value=observed):
            self.assertEqual(vision.match_position(self.frame, candidates, previous=previous,
                                                   hands=(expected.blue, expected.orange)), expected)
            with self.assertRaises(vision.VisionError):
                vision.match_position(self.frame, candidates, previous=previous,
                                      hands=(previous.blue, previous.orange))
            observed[8] = (0,)
            with self.assertRaises(vision.VisionError):
                vision.match_position(self.frame, candidates, previous=previous,
                                      hands=(expected.blue, expected.orange))

    def test_verified_reply_can_retain_one_hidden_unchanged_piece(self):
        previous = solver.from_table_code("G/---/eG-/l-L/CGe/C")
        expected = previous.next(solver.Move(1, 0))
        observations = [(piece,) for piece in expected.board]
        observations[0] = (solver.KING, -solver.KING)
        observations[8] = (0,)
        hands = expected.blue, expected.orange
        with patch.object(vision, "observe_board", return_value=observations):
            self.assertEqual(vision.match_position(self.frame, [expected], previous=previous, hands=hands), expected)
            with self.subTest("two hidden pieces"):
                observations[2] = (0,)
                with self.assertRaises(vision.VisionError):
                    vision.match_position(self.frame, [expected], previous=previous, hands=hands)
            with self.subTest("hidden destination"):
                observations[2] = (-solver.WHALE,)
                observations[0] = (0,)
                with self.assertRaises(vision.VisionError):
                    vision.match_position(self.frame, [expected], previous=previous, hands=hands)

    def test_initial_read_accepts_an_endgame_without_reserves(self):
        board = (0, 0, solver.DOLPHIN, 0, 0, solver.KING, 0, -solver.KING,
                 0, solver.DOLPHIN, -solver.TURTLE, 0)
        with (patch.object(vision, "is_ready", return_value=True),
              patch.object(vision, "hand_read", return_value=[]),
              patch.object(vision, "observe_board", return_value=[(piece,) for piece in board])):
            self.assertEqual(vision.read_position(self.frame), solver.Position(board))
