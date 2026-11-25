"""A blocked native UI call must not hang smoke checks indefinitely."""
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import smoke_test


ROOT = Path(__file__).resolve().parents[1]


class SmokeWatchdogTests(unittest.TestCase):
    def test_retry_is_limited_to_native_tk_watchdog_timeouts(self):
        timeout = 'Timeout (0:02:00)!\n  File "C:/Python/Lib/tkinter/__init__.py", line 1479 in update\n'
        for failure, has_report, calls, passes in (
            (timeout, False, 2, True),
            (timeout, True, 1, False),
            ('Timeout (0:02:00)!\n  File "smoke_test.py", line 89 in ready\n', False, 1, False),
        ):
            with self.subTest(failure=failure, has_report=has_report), tempfile.TemporaryDirectory() as folder:
                args = SimpleNamespace(report=Path(folder) / 'ui.json', executable=None, screenshot=None,
                                       timeout=45, wall_timeout=120, retry_native_timeout=2)
                attempts = []

                def run(command, **_):
                    attempts.append(command)
                    passed = len(attempts) > 1
                    if passed or has_report:
                        Path(command[-1]).write_text(json.dumps({'passed': passed}), encoding='utf-8')
                    return subprocess.CompletedProcess(command, 0 if passed else 1, '' if passed else failure)

                with patch.object(smoke_test.subprocess, 'run', side_effect=run), redirect_stdout(StringIO()):
                    self.assertEqual(smoke_test.run_smoke_attempts(args), 0 if passes else 1)
                self.assertEqual(len(attempts), calls)
                self.assertEqual(json.loads(args.report.read_text(encoding='utf-8'))['passed'], passes)
                self.assertEqual((args.report.parent / 'ui-attempt-1.log').read_text(encoding='utf-8'), failure)

    def run_probe(self, exercise):
        code = f'''
import sys, time
from tools import smoke_test
def exercise(**kwargs):
{exercise}
smoke_test.exercise = exercise
sys.argv = ['smoke_test.py', '--wall-timeout', '0.25']
code = smoke_test.main()
time.sleep(0.5)
raise SystemExit(code)
'''
        return subprocess.run([sys.executable, '-c', code], cwd=ROOT,
                              capture_output=True, text=True, timeout=10)

    @unittest.skipUnless(sys.platform == 'win32', 'Windows native UI watchdog')
    def test_native_block_exits_with_stack_instead_of_hanging(self):
        result = self.run_probe('    import ctypes\n    ctypes.windll.kernel32.Sleep(30000)')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Timeout', result.stderr)
        self.assertIn('in exercise', result.stderr)

    def test_success_cancels_watchdog_before_returning(self):
        result = self.run_probe("    return {'passed': True}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('Timeout', result.stderr)


if __name__ == '__main__':
    unittest.main()
