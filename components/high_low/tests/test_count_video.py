"""Optional regression against the user's September 21 recording."""
import os
import unittest
import cv2
import auto_bot as bot
from phased_strategy import PhasedStrategy
from settlement import SettlementReader


@unittest.skipUnless(os.environ.get('HOLOLIVE_COUNT_VIDEO'), 'Private September 21 video not supplied')
class CountVideoTests(unittest.TestCase):
    def setUp(self):
        self.capture = cv2.VideoCapture(os.environ['HOLOLIVE_COUNT_VIDEO'])

    def tearDown(self):
        self.capture.release()

    def frame(self, seconds):
        self.capture.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
        ok, image = self.capture.read()
        self.assertTrue(ok)
        return cv2.resize(image[120:904, 430:1822], (1920, 1080), interpolation=cv2.INTER_CUBIC)

    def observe(self, policy, seconds):
        frame = self.frame(seconds)
        state = bot.detect_game_state(frame)
        if state == 'ASK_CHALLENGE':
            success = bot.is_success_prompt(frame)
            if policy.base_cash is None:
                self.assertFalse(success)
                policy.start_round(bot.read_screen_number(frame, bot.REWARD_ZONE) // 2,
                                   12800 if policy.stage == 1 else 0)
            elif success:
                policy.confirm_success()
        elif state == 'HIGH_LOW':
            policy.guess_clicked()
        elif state == 'RESULT':
            policy.begin_settlement(False)
        return state

    def test_maximum_first_round_and_correct_12800_credit(self):
        policy = PhasedStrategy()
        for seconds in (985, 989, 993, 993, 996.5, 998.5, 1002.5,
                        1004.5, 1008, 1010.5, 1013.5, 1016.5):
            self.observe(policy, seconds)
        self.assertEqual((policy.base_cash, policy.successes, policy.expected_cash), (400, 5, 12800))
        reader = SettlementReader()
        credited = None
        for i in range(14):
            seconds = 1016.5 + i * .25
            amount = bot.read_result_number(self.frame(seconds), bot.RESULT_REWARD_ZONE)
            credited = reader.observe(amount, seconds, policy.expected_cash)
            if credited is not None:
                break
        self.assertEqual(credited, 12800)
        self.assertEqual(policy.stage_after_credit(credited), 1)

    def test_second_round_stops_at_third_success_5600(self):
        policy = PhasedStrategy(1)
        for seconds in (1358, 1360.5, 1363, 1363, 1366, 1370.5, 1370.5, 1373.5, 1375):
            self.observe(policy, seconds)
            self.assertEqual(policy.decide(), 'challenge')
        self.observe(policy, 1376)
        self.assertEqual((policy.successes, policy.expected_cash, policy.decide()), (3, 5600, 'cashout'))

    def test_old_crop_loses_digits_but_new_crop_does_not(self):
        for seconds, old_amount, correct in ((1019, 2800, 12800), (1384, 200, 11200)):
            frame = self.frame(seconds)
            self.assertEqual(bot.read_result_number(frame, (1044, 337, 450, 97)), old_amount)
            self.assertEqual(bot.read_result_number(frame, bot.RESULT_REWARD_ZONE), correct)


if __name__ == '__main__':
    unittest.main()
