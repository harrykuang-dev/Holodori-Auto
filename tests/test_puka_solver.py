"""Check Raft Chess move selection when a proof is unavailable."""

from importlib import import_module
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


COMPONENT = Path(__file__).resolve().parents[1] / "components" / "puka_puka"
with patch.object(sys, "path", [str(COMPONENT), *sys.path]):
    solver = import_module("solver")


class RaftSolverTests(unittest.TestCase):
    def setUp(self):
        self.position = solver.from_table_code("S/---/-cl/LC-/---/EGeg")
        self.winning_move = solver.Move(1, 2)

    def test_tablebase_win_takes_priority_over_the_local_estimate(self):
        with (patch.object(solver, "probe", return_value={self.winning_move: (1, 11)}),
              patch.object(solver, "search_moves") as estimate):
            outcome, depth, choices, _ = solver.recommend(self.position, seconds=0, online=True)
        self.assertEqual((outcome, depth, choices), (1, 11, [self.winning_move]))
        estimate.assert_not_called()

    def test_unavailable_tablebase_still_returns_a_legal_move_at_the_deadline(self):
        for error in (TimeoutError(), ValueError()):
            with self.subTest(error=type(error)):
                with patch.object(solver, "probe", side_effect=error):
                    outcome, depth, choices, _ = solver.recommend(self.position, seconds=0, online=True)
                self.assertIsNone(outcome)
                self.assertEqual(depth, 1)
                self.assertTrue(choices)
                self.assertTrue(set(choices) <= set(solver.moves(self.position)))

    def test_when_every_move_loses_search_still_has_a_legal_choice(self):
        # Orange's leader has reached its goal and Blue cannot capture it.
        position = solver.Position((-solver.KING, 0, 0, 0,
                                    0, 0, 0, 0,
                                    0, 0, solver.KING, 0))
        best, distance, choices = solver.search_moves(position, (), 0)
        self.assertEqual((best, distance), (-1, 1))
        self.assertEqual(set(choices), set(solver.moves(position)))

    def test_threefold_reply_is_scored_as_a_draw(self):
        next_position = self.position.next(self.winning_move)
        another = solver.Move(5, 6)
        result = solver.rank_tablebase(self.position, (next_position, next_position),
                                        {self.winning_move: (1, 11), another: (-1, 2)})
        self.assertEqual(result, (0, 0, [self.winning_move]))
