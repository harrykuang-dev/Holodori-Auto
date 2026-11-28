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

    def test_stage_menu_uses_only_the_ready_center_card(self):
        self.frame[29:72, 46:106] = 245
        self.frame[47:95, 1517:1597] = 245
        self.frame[441:473, 1562:1576] = 245
        for x in (298, 1326):
            self.frame[247:334, x-160:x-112] = (244, 237, 214)
            self.frame[721:755, x-105:x+104] = (235, 174, 53)
        self.frame[247:334, 652:700] = (191, 164, 150)
        self.assertEqual(stages.classify_screen(self.frame), 'level_menu')

        self.frame[247:334, 652:700] = (244, 237, 214)
        self.frame[721:755, 707:916] = (235, 174, 53)
        for badge in ((122, 220, 75), (245, 148, 132)):
            self.frame[189:204, 740:757] = badge
            self.assertEqual(stages.classify_screen(self.frame), 'stage_start')

        for x in (686, 812, 938):
            cv2.circle(self.frame, (x, 548), 27, (245, 245, 245), 9)
            cv2.circle(self.frame, (x, 548), 13, (245, 245, 245), -1)
        self.assertEqual(stages.classify_screen(self.frame), 'level_menu')
        self.frame[513:584, 651:973] = 0
        self.frame[134:173, 736:888] = (241, 73, 42)
        self.frame[150:168, 752:872] = (44, 227, 249)
        self.assertEqual(stages.classify_screen(self.frame), 'level_menu')

    def test_event_next_uses_shared_settlement_controls(self):
        self.frame[29:72, 46:106] = 245
        self.frame[805:854, 1280:1525] = (235, 174, 53)
        self.assertEqual(stages.classify_screen(self.frame), 'result')

        self.frame[41:100, 1515:1595] = 245
        self.assertNotEqual(stages.classify_screen(self.frame), 'event_next')
        check = np.array([(1365, 825), (1371, 833), (1385, 819)], dtype=np.int32)
        cv2.polylines(self.frame, [check], False, (245, 245, 245), 3)
        self.assertNotEqual(stages.classify_screen(self.frame), 'event_next')
        self.frame[805:854, 1280:1525] = (235, 174, 53)
        arrow = np.array([(1313, 827), (1324, 827), (1324, 821), (1337, 831),
                          (1324, 841), (1324, 835), (1313, 835)], dtype=np.int32)
        cv2.fillPoly(self.frame, [arrow], (245, 245, 245))
        for artwork in ((20, 35, 91), (220, 37, 144)):
            self.frame[224:714, 170:775] = artwork
            self.frame[300:639, 793:1502] = artwork
            self.assertEqual(stages.classify_screen(self.frame), 'event_next')
        self.frame[805:854, 1280:1525] = 130
        self.assertIsNone(stages.classify_screen(self.frame))

    def test_result_confirmation_uses_the_checkmark_with_a_reward_card(self):
        self.frame[29:72, 46:106] = 245
        self.frame[805:854, 1280:1525] = (235, 174, 53)
        self.frame[395:425, 1060:1495] = 245
        self.frame[440:550, 1430:1495] = 245
        self.assertEqual(stages.classify_screen(self.frame), 'result')
        check = np.array([(1320, 826), (1326, 832), (1340, 818)], dtype=np.int32)
        cv2.polylines(self.frame, [check], False, (245, 245, 245), 3)
        self.assertEqual(stages.classify_screen(self.frame), 'result_ok')
        self.frame[440:550, 1430:1495] = 0
        self.assertEqual(stages.classify_screen(self.frame), 'result')

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

    def test_challenge_requires_both_cards_and_reads_the_cost_color(self):
        self.frame[305:680, 478:776] = (152, 45, 250)
        self.frame[400:482, 583:668] = 250
        self.frame[305:680, 844:1150] = (250, 192, 46)
        self.frame[320:660, 867:1137] = 250
        self.frame[402:473, 960:1032] = (250, 192, 46)
        self.assertIsNone(stages.classify_screen(self.frame))

        for color, expected in ((250, 'challenge_continue'), ((40, 44, 248), 'challenge_low_energy')):
            with self.subTest(expected=expected):
                self.frame[275:295, 639:671] = color
                self.assertEqual(stages.classify_screen(self.frame), expected)
        self.frame[:, 844:1150] = 0
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

    def test_boards_wait_for_the_warning_to_clear_before_reading_hats(self):
        for rows in (3, 4):
            with self.subTest(rows=rows):
                self.frame[88:116, 510:675] = (118, 68, 66)
                self.frame[88:116, 1000:1135] = (118, 68, 66)
                with self.assertRaisesRegex(vision.VisionError, '提示移開'):
                    tuple(vision.observe_board(self.frame, rows=rows))
                self.frame[88:116, 1000:1135] = 0
                self.assertEqual(len(tuple(vision.observe_board(self.frame, rows=rows))), rows * 4)

    def test_reserve_detection_ignores_background_between_icons(self):
        self.frame[806:819, 1229:1312] = (222, 70, 60)
        self.frame[821:855, 1296:1380] = (222, 70, 60)
        self.frame[807:855, 1415:1515] = (220, 60, 208)
        self.assertEqual(vision.hand_read(self.frame, vision.ORANGE),
                         [(1465, 847, vision.DOLPHIN), (1338, 847, vision.WHALE)])

    def test_reserve_detection_covers_all_slots_in_display_order(self):
        for side, first in ((vision.BLUE, 210), (vision.ORANGE, 1465)):
            with self.subTest(side=side):
                self.frame[:] = 0
                entries = []
                for slot in range(6):
                    x = first + side * slot * 127
                    self.frame[810:855, x-45:x+45] = (70, 210, 65)
                    entries.append((x, 847, vision.TURTLE))
                self.assertEqual(vision.hand_read(self.frame, side), entries)

    def test_reward_layout_requires_the_turquoise_band(self):
        self.frame[328:380, 100:1510] = (226, 217, 109)
        self.assertEqual(stages.classify_screen(self.frame), 'reward')
        self.frame[328:380, 100:800] = 0
        self.assertIsNone(stages.classify_screen(self.frame))



class PukaEntryTests(unittest.TestCase):
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

    def test_start_on_event_page_passes_through_remaining_rewards(self):
        game = self.game('event_next', 'reward', 'stage_start', 'board')
        self.assertEqual(pilot.prepare(game, Mock()), ('board', 'ready position'))
        self.assertEqual(game.click.call_args_list, [call(*stages.CLICK[state])
            for state in ('event_next', 'reward', 'stage_start')])

    def test_start_from_a_pending_result_confirmation(self):
        game = self.game('result_ok', 'challenge_continue', 'board')
        self.assertEqual(pilot.prepare(game, Mock()), ('board', 'ready position'))
        self.assertEqual(game.click.call_args_list, [call(*stages.CLICK[state])
            for state in ('result_ok', 'challenge_continue')])

    def test_waits_for_the_game_to_center_the_next_stage(self):
        frames = iter(('level_menu', 'stage_start', 'level_menu', *('stage_start',) * 5))
        game = self.game('level_menu', 'board')

        def capture():
            if game.scene == 'board':
                return 'board'
            self.assertFalse(game.click.called)
            return next(frames)

        game.capture = capture
        self.assertEqual(pilot.prepare(game, Mock()), ('board', 'ready position'))
        game.click.assert_called_once_with(812, 737)

    def test_refill_is_off_by_default(self):
        game = self.game('refill')
        with self.assertRaisesRegex(pilot.StopPlay, '能量不足'):
            pilot.prepare(game, Mock())
        game.click.assert_not_called()

    def test_refill_retries_the_original_stage(self):
        game = self.game('stage_start', 'refill', 'stage_start', 'board')
        self.assertEqual(pilot.prepare(game, Mock(), auto_refill=True), ('board', 'ready position'))
        stage = call(*stages.CLICK['stage_start'])
        self.assertEqual(game.click.call_args_list, [stage, call(*stages.CLICK['refill']), stage])

    def test_unavailable_or_repeated_refill_stops(self):
        unavailable = self.game('refill_panel')
        with self.assertRaisesRegex(pilot.StopPlay, '一瓶道具'):
            pilot.prepare(unavailable, Mock(), auto_refill=True)
        unavailable.click.assert_not_called()

        repeated = self.game('stage_start', 'refill', 'stage_start', 'refill')
        with self.assertRaisesRegex(pilot.StopPlay, '補充後仍然需要能量'):
            pilot.prepare(repeated, Mock(), auto_refill=True)
        self.assertEqual(repeated.click.call_args_list.count(call(*stages.CLICK['refill'])), 1)

    def test_challenge_continues_without_refilling_when_energy_is_sufficient(self):
        game = self.game('challenge_continue', 'board')
        self.assertEqual(pilot.prepare(game, Mock()), ('board', 'ready position'))
        game.click.assert_called_once_with(*stages.CLICK['challenge_continue'])

    def test_challenge_low_energy_requires_enabling_refills(self):
        game = self.game('challenge_low_energy')
        with self.assertRaisesRegex(pilot.StopPlay, '能量不足'):
            pilot.prepare(game, Mock())
        game.click.assert_not_called()

    def test_challenge_refills_once_and_retries_the_same_card(self):
        game = self.game('challenge_low_energy', 'refill', 'challenge_continue', 'board')
        self.assertEqual(pilot.prepare(game, Mock(), auto_refill=True), ('board', 'ready position'))
        play = call(*stages.CLICK['challenge_continue'])
        self.assertEqual(game.click.call_args_list, [play, call(*stages.CLICK['refill']), play])

    def test_challenge_stops_if_still_low_after_refilling(self):
        game = self.game('challenge_low_energy', 'refill', 'challenge_low_energy')
        with self.assertRaises(pilot.StopPlay):
            pilot.prepare(game, Mock(), auto_refill=True)
        self.assertEqual(game.click.call_args_list, [call(*stages.CLICK['challenge_continue']),
                                                    call(*stages.CLICK['refill'])])


class PukaSettlementTests(unittest.TestCase):
    def test_event_and_rewards_are_acknowledged_once_before_next_round(self):
        game = Mock()
        states = iter(('result_details', 'event_next', 'reward', 'stage_start'))
        waits = []

        def wait(_game, allowed, **kwargs):
            state = next(states)
            self.assertIn(state, allowed)
            waits.append(set(allowed))
            return state

        with patch.object(pilot, 'wait_menu', side_effect=wait):
            pilot.settle(game, 'result', Mock())

        self.assertEqual(game.click.call_args_list, [call(*stages.CLICK[state])
            for state in ('result', 'result_details', 'event_next', 'reward')])
        self.assertNotIn('event_next', waits[2])
        self.assertNotIn('reward', waits[3])

    def test_a_draw_or_loss_can_finish_without_a_proven_win(self):
        game = Mock()
        with patch.object(pilot, 'wait_menu', return_value='stage_start'):
            pilot.settle(game, 'result_details', Mock())
        game.click.assert_called_once_with(*stages.CLICK['result_details'])

    def test_ok_remains_available_after_event_settlement(self):
        game = Mock()
        states = iter(('event_next', 'result_ok', 'challenge_continue'))

        def wait(_game, allowed, **kwargs):
            state = next(states)
            self.assertIn(state, allowed)
            if state == 'challenge_continue':
                self.assertNotIn('result_ok', allowed)
            return state

        with patch.object(pilot, 'wait_menu', side_effect=wait):
            pilot.settle(game, 'win_details', Mock())
        self.assertEqual(game.click.call_args_list, [call(*stages.CLICK[state])
            for state in ('win_details', 'event_next', 'result_ok')])

    def test_challenge_leaves_the_continue_card_unclicked_at_the_round_limit(self):
        for card in ('challenge_continue', 'challenge_low_energy'):
            with self.subTest(card=card):
                game, notify = Mock(), Mock()
                waits = []

                def wait(_game, allowed, **kwargs):
                    waits.append(allowed)
                    self.assertIn(card, allowed)
                    return card

                with patch.object(pilot, 'prepare', return_value=(None, 'ready board')) as prepare, \
                        patch.object(pilot, 'play_match', return_value='event_next'), \
                        patch.object(pilot, 'wait_menu', side_effect=wait):
                    pilot.run(game, 1, notify, auto_refill=True)
                self.assertEqual(len(waits), 1)
                prepare.assert_called_once_with(game, notify, auto_refill=True)
                game.click.assert_called_once_with(*stages.CLICK['event_next'])
                notify.assert_called_with('completed', 1, 1)


class PukaTrackingTests(unittest.TestCase):
    def test_selection_rechecks_a_transient_board_mismatch_before_clicking(self):
        solver = import_module('solver')
        move = solver.Move(2, 5)
        ticks = count(step=.2)
        clock = SimpleNamespace(monotonic=lambda: next(ticks), sleep=lambda _: None)
        game = SimpleNamespace(capture=Mock(side_effect=['initial', 'different',
                                                        'initial', 'initial', 'selected']))

        def click(*_):
            self.assertEqual(game.capture.call_count, 4)

        game.click = Mock(side_effect=click)
        with (patch.object(pilot, 'time', clock),
              patch.object(pilot, 'source_point', return_value=(10, 10)),
              patch.object(pilot, 'selection_ready', side_effect=lambda frame, *_: frame == 'selected')):
            pilot.select_move(game, 'initial', move, lambda frame: frame)
        game.click.assert_called_once_with(10, 10)

    def test_selection_retries_only_on_the_same_board(self):
        solver = import_module('solver')
        move = solver.Move(2, 5)
        for changed in (False, True):
            with self.subTest(changed=changed):
                ticks = count(step=.2)
                clock = SimpleNamespace(monotonic=lambda: next(ticks), sleep=lambda _: None)
                game = SimpleNamespace(scene='initial')
                game.capture = lambda: game.scene

                def click(*_):
                    if game.click.call_count == 1:
                        if changed:
                            game.scene = 'different'
                    else:
                        game.scene = 'selected'

                game.click = Mock(side_effect=click)
                with (patch.object(pilot, 'time', clock),
                      patch.object(pilot, 'source_point', return_value=(10, 10)),
                      patch.object(pilot, 'selection_ready', side_effect=lambda frame, *_: frame == 'selected')):
                    if changed:
                        with self.assertRaises(pilot.StopPlay):
                            pilot.select_move(game, 'initial', move, lambda frame: frame)
                    else:
                        pilot.select_move(game, 'initial', move, lambda frame: frame)
                self.assertEqual(game.click.call_count, 1 if changed else 2)

    def test_next_move_revalidates_with_the_confirmed_reply(self):
        solver = import_module('solver')
        prior = solver.from_table_code('S/R-g/-cl/--E/-GL/E')
        deploy = solver.Move(-solver.WHALE, 2)
        expected = prior.next(deploy).next(solver.Move(6, 5))
        next_move = solver.Move(2, 5)
        virtual_time = count(step=.2)
        clock = SimpleNamespace(monotonic=lambda: next(virtual_time), sleep=lambda _: None)
        game = SimpleNamespace(scene='initial')
        game.capture = lambda: game.scene

        class NextSelection(Exception):
            pass

        def click(*_):
            if game.scene == 'reply':
                raise NextSelection
            game.scene = 'selection' if game.scene == 'initial' else 'reply'

        def read_position(frame, *, rows):
            if frame == 'initial':
                self.assertEqual(rows, prior.rows)
                return prior
            raise vision.VisionError('key raft obscured')

        game.click = click
        reply_modes = []

        def read_reply(frame, previous, submitted, *, relaxed_reply):
            self.assertEqual((frame, previous, submitted), ('reply', prior, deploy))
            reply_modes.append(relaxed_reply)
            if not relaxed_reply:
                raise vision.VisionError('waiting for a readable reply')
            return expected

        with (patch.object(pilot, 'time', clock),
              patch.object(pilot, 'read_position', side_effect=read_position),
              patch.object(pilot, 'next_player_position', side_effect=read_reply),
              patch.object(pilot, 'classify_screen', return_value='board'),
              patch.object(pilot, 'selection_ready', side_effect=lambda frame, *_: frame == 'selection'),
              patch.object(pilot, 'source_point', return_value=(10, 10)),
              patch.object(pilot, 'choose', side_effect=[deploy, next_move])):
            with self.assertRaises(NextSelection):
                pilot.play_match(game, 'initial', prior, Mock())
        self.assertFalse(reply_modes[0])
        self.assertTrue(reply_modes[-1])

    def test_relaxed_reply_requires_a_visible_legal_whale_deployment_and_matching_reserves(self):
        solver = import_module('solver')
        king, whale, dolphin = solver.KING, solver.WHALE, solver.DOLPHIN
        prior = solver.Position((0, 0, 0, 0, 0, king, 0, -king, 0, 0, 0, 0),
                                (dolphin,), (whale,))
        ours = solver.Move(-dolphin, 3)
        after = prior.next(ours)
        expected = after.next(solver.Move(-whale, 8))

        def observe(_frame, *, tracking, rows, relaxed_reply_squares):
            board = list(after.board)
            if 8 in relaxed_reply_squares:
                board[8] = -whale
            return [(piece,) for piece in board]

        with (patch.object(pilot, 'is_ready', return_value=True),
              patch.object(pilot, 'hand_inventory', return_value=((), ())) as hand,
              patch.object(vision, 'observe_board', side_effect=observe) as observation):
            with self.assertRaises(vision.VisionError):
                pilot.next_player_position('frame', prior, ours)
            self.assertEqual(pilot.next_player_position('frame', prior, ours, relaxed_reply=True),
                             expected)
            self.assertNotIn(5, observation.call_args.kwargs['relaxed_reply_squares'])
            hand.return_value = ((), (whale,))
            observation.reset_mock()
            with self.assertRaises(vision.VisionError):
                pilot.next_player_position('frame', prior, ours, relaxed_reply=True)
            self.assertFalse(observation.call_args.kwargs['relaxed_reply_squares'])
