"""Keep IPC atomic when Windows briefly locks the destination file."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from holodori.channel import read_json, write_json


class ChannelTests(unittest.TestCase):
    def test_transient_lock_retries_without_exposing_partial_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'status.json'
            write_json(path, {'state': 'previous'})
            replace = Path.replace
            locked = [True, True, False]

            def replace_after_read(source, target):
                self.assertEqual(read_json(target), {'state': 'previous'})
                if locked.pop(0):
                    raise PermissionError('reader holds the destination')
                return replace(source, target)

            with patch.object(Path, 'replace', replace_after_read), patch('holodori.channel.time.sleep'):
                write_json(path, {'state': 'ready', 'request': 7})
            self.assertEqual(read_json(path), {'state': 'ready', 'request': 7})
            self.assertFalse(path.with_suffix('.pending').exists())

    def test_persistent_lock_raises_and_preserves_previous_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'status.json'
            write_json(path, {'state': 'previous'})
            with patch.object(Path, 'replace', side_effect=PermissionError('locked')), \
                    patch('holodori.channel.time.sleep'):
                with self.assertRaises(PermissionError):
                    write_json(path, {'state': 'ready'})
            self.assertEqual(read_json(path), {'state': 'previous'})

    def test_other_filesystem_errors_are_not_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(Path, 'replace', side_effect=FileNotFoundError('missing')) as replace, \
                    patch('holodori.channel.time.sleep') as sleep:
                with self.assertRaises(FileNotFoundError):
                    write_json(Path(directory) / 'status.json', {'state': 'ready'})
            replace.assert_called_once()
            sleep.assert_not_called()
