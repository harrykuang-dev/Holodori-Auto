import os
import unittest
import cv2
import numpy as np
import ddddocr
from reward_vision import challenge_number_image, read_challenge_number


class RewardVisionTests(unittest.TestCase):
    def test_wallet_object_does_not_expand_number_crop(self):
        image = np.zeros((300, 500, 3), dtype=np.uint8)
        yellow = (0, 220, 255)
        cv2.putText(image, '800', (70, 75), cv2.FONT_HERSHEY_SIMPLEX, 2, yellow, 5)
        without_wallet = challenge_number_image(image, (0, 0, 500, 300))
        cv2.circle(image, (220, 210), 20, yellow, -1)
        with_wallet = challenge_number_image(image, (0, 0, 500, 300))
        np.testing.assert_array_equal(with_wallet, without_wallet)

    @unittest.skipUnless(os.environ.get('HOLOLIVE_TEST_VIDEO'), 'Private video is optional and not distributed')
    def test_video_challenge_reads_800(self):
        capture = cv2.VideoCapture(os.environ['HOLOLIVE_TEST_VIDEO'])
        ocr = ddddocr.DdddOcr(show_ad=False)
        try:
            for seconds in (335.5, 336.0, 336.5):
                capture.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
                ok, frame = capture.read()
                self.assertTrue(ok)
                frame = cv2.resize(frame[163:862, 517:1759], (1920, 1080), interpolation=cv2.INTER_CUBIC)
                self.assertEqual(read_challenge_number(frame, (606, 389, 870, 253), ocr), 800)
        finally:
            capture.release()


if __name__ == '__main__':
    unittest.main()
