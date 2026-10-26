"""A blocked native UI call must not hang smoke checks indefinitely."""
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SmokeWatchdogTests(unittest.TestCase):
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
