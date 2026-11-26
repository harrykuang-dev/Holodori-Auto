"""Validate the shared TensorRT component before it can affect a feature."""
import ctypes
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from holodori import accelerator


class TensorRTComponentTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        base = Path(directory)
        self.folder = base.resolve() / accelerator.TENSORRT_COMPONENT
        self.enterContext(patch.object(sys, 'executable', str(base / 'Holodori-Auto.exe')))
        self.enterContext(patch.object(sys, 'frozen', True, create=True))
        self.enterContext(patch.object(sys, 'path', sys.path.copy()))
        self.enterContext(patch.object(accelerator, '_active_root', None))
        self.enterContext(patch.object(accelerator, '_dll_handles', []))
        self.enterContext(patch.object(accelerator, '_builder_module', None))
        self.enterContext(patch.object(accelerator, 'require_tensorrt_platform'))
        self.register = self.enterContext(patch.object(accelerator.os, 'add_dll_directory', create=True))
        self.original_path = sys.path.copy()

    def write_component(self, **overrides):
        for relative in accelerator.TENSORRT_FILES:
            file = self.folder / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(b'component file')
        record = {
            'format': accelerator.TENSORRT_FORMAT,
            'python': list(accelerator.TENSORRT_PYTHON),
            'architecture': accelerator.TENSORRT_ARCHITECTURE,
            'versions': accelerator.TENSORRT_DISTRIBUTIONS,
            'files': accelerator.tensorrt_file_sizes(self.folder),
            **overrides,
        }
        (self.folder / 'component.json').write_text(json.dumps(record), encoding='utf-8')

    def test_base_reports_the_missing_optional_component(self):
        with self.assertRaisesRegex(accelerator.TensorRTUnavailable, 'next to Holodori-Auto'):
            accelerator.activate_tensorrt_component()
        self.register.assert_not_called()
        self.assertEqual(sys.path, self.original_path)

    def test_incompatible_component_does_not_register_any_dlls(self):
        self.write_component(python=[3, 12])
        with self.assertRaisesRegex(accelerator.TensorRTUnavailable, 'Incompatible'):
            accelerator.activate_tensorrt_component()
        self.register.assert_not_called()

    def test_truncated_component_does_not_register_any_dlls(self):
        self.write_component()
        (self.folder / accelerator.BUILDER_LIBRARY).write_bytes(b'partial')
        with self.assertRaisesRegex(accelerator.TensorRTUnavailable, 'incomplete or damaged'):
            accelerator.activate_tensorrt_component()
        self.register.assert_not_called()

    def test_component_is_registered_and_its_builder_dll_is_loaded_once(self):
        self.write_component()
        with patch.object(ctypes, 'WinDLL', create=True) as load:
            accelerator.load_builder_library()
            accelerator.load_builder_library()
        self.assertEqual(self.register.call_count, len(accelerator.DLL_DIRECTORIES))
        self.assertEqual(sys.path.count(str(self.folder)), 1)
        load.assert_called_once_with(str(self.folder / accelerator.BUILDER_LIBRARY))

    def test_failed_registration_rolls_back_and_can_be_retried(self):
        self.write_component()
        handle = Mock()
        self.register.side_effect = [handle, OSError('invalid directory')]
        with self.assertRaises(OSError):
            accelerator.activate_tensorrt_component()
        handle.close.assert_called_once()
        self.assertEqual(sys.path, self.original_path)
        self.register.side_effect = None
        self.assertEqual(accelerator.activate_tensorrt_component(), self.folder)
