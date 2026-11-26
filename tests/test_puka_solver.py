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

    def test_only_the_four_row_board_allows_entering_its_fourth_row(self):
        three_rows = (0, 0, 0, -solver.KING, solver.KING, 0, 0, 0,
                      0, 0, solver.DOLPHIN, 0)
        normal = solver.Position(three_rows)
        challenge = solver.Position(three_rows + (0, 0, 0, 0))
        fourth_row_move = solver.Move(10, 14)

        self.assertNotIn(fourth_row_move, solver.moves(normal))
        self.assertIn(fourth_row_move, solver.moves(challenge))
        self.assertEqual(challenge.next(fourth_row_move).board[14], solver.DOLPHIN)
        self.assertNotIn(fourth_row_move, solver.moves(normal))

    def test_fourth_row_uses_the_same_promotion_and_goal_columns(self):
        board = (0, 0, -solver.KING, 0,
                 0, 0, 0, 0,
                 0, 0, 0, 0,
                 0, 0, solver.TURTLE, 0)
        turtle = solver.Position(board, (solver.TURTLE,))
        self.assertEqual(turtle.next(solver.Move(14, 15)).board[15], solver.GOLD)
        self.assertEqual(turtle.next(solver.Move(-solver.TURTLE, 15)).board[15], solver.TURTLE)

        leader = solver.Position(board[:14] + (solver.KING, 0))
        reached = leader.next(solver.Move(14, 15))
        self.assertIsNone(solver.terminal(reached))
        self.assertEqual(solver.terminal(reached.next(solver.Move(2, 1))), 1)

    def test_four_row_challenge_recommends_a_local_move_with_full_inventory(self):
        board = (0, solver.DOLPHIN, 0, 0,
                 0, solver.WHALE, 0, -solver.KING,
                 solver.KING, -solver.TURTLE, -solver.WHALE, 0,
                 0, solver.TURTLE, solver.DOLPHIN, 0)
        position = solver.Position(board)
        self.assertTrue(solver.full_inventory(position))
        with patch.object(solver, "probe") as probe:
            _, _, choices, _ = solver.recommend(position, seconds=0, online=True)
        probe.assert_not_called()
        self.assertTrue(choices)
        self.assertTrue(set(choices) <= set(solver.moves(position)))
        with self.assertRaises(ValueError):
            solver.table_code(position)
