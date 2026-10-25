"""Resource-layout regression checks; no upstream runtime or game is started."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from tools import build_release
from holodori import runtime


class BuildAssetTests(unittest.TestCase):
    def test_runtime_excludes_training_and_adjacent_gpu_copies(self):
        for path in ('annotations/images/game.png', 'training/train.py', 'archive/main_ui.py',
                     'accelerators/tensorrt/tensorrt_libs/nvinfer_10.dll', 'models/rope.pt',
                     'models/rope.engine', 'outputs/kitchen-bot/segmenter.py'):
            with self.subTest(path=path):
                self.assertFalse(build_release.runtime_file(Path(path)))
        for path in ('models/rope.fp16.onnx', 'models/rope.directml.onnx',
                     'models/inference/icon-classifier.onnx', 'third_party/AGPL-3.0.txt'):
            with self.subTest(path=path):
                self.assertTrue(build_release.runtime_file(Path(path)))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="holodori-build-assets-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.root = self.directory / "project"
        self.root.mkdir()
        self.contents = {
            "upstream/high_low/main_ui.py": b"# original high-low interface\n",
            "upstream/high_low/auto_bot.py": b"# original recognition and strategy\n",
            "upstream/high_low/assets/high-low-title.png": b"original title bitmap\x00\xff",
            "upstream/high_low/assets/nested/icon.png": b"original nested bitmap\x00\xfe",
            "upstream/high_low/templates/icons/tw/start_tw.png": b"original Traditional Chinese template\x00\xfd",
            "upstream/high_low/templates/ranks/a.png": b"original rank template\x00\xfc",
            "upstream/high_low/icon.ico": b"original Windows icon\x00\xfb",
            "upstream/high_low/icon_transparent.png": b"original transparent icon\x00\xfa",
            "upstream/high_low/licenses/NOTICE.txt": b"Original required notice\n",
            "upstream/fishing/gui.py": b"# independent fishing interface\n",
            "upstream/fishing/assets/fishing-hook.png": b"fishing icon\x00\xf9",
        }
        self.sources = []
        for relative, content in self.contents.items():
            source = self.root / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(content)
            self.sources.append((source, Path(relative)))

    def test_stage_adds_original_high_low_resource_layout(self):
        stage = self.directory / "stage"
        with mock.patch.object(build_release, "ROOT", self.root):
            data = build_release.stage_data(stage, self.sources)
        for relative, original in self.contents.items():
            self.assertEqual((stage / relative).read_bytes(), original)
        aliases = (
            "assets/high-low-title.png", "assets/nested/icon.png",
            "templates/icons/tw/start_tw.png", "templates/ranks/a.png",
            "icon.ico", "icon_transparent.png",
        )
        for alias in aliases:
            with self.subTest(alias=alias):
                self.assertEqual((stage / alias).read_bytes(), self.contents["upstream/high_low/" + alias])
                self.assertIn((str(stage / alias), Path(alias).parent.as_posix()), data)
        # Python namespaces and unrelated component artwork stay isolated.
        for flattened in ("main_ui.py", "auto_bot.py", "gui.py", "assets/fishing-hook.png"):
            self.assertFalse((stage / flattened).exists())

    def test_staging_does_not_modify_original_source_or_artwork(self):
        before = {source: (source.read_bytes(), source.stat().st_mtime_ns) for source, _ in self.sources}
        with mock.patch.object(build_release, "ROOT", self.root):
            build_release.stage_data(self.directory / "stage", self.sources)
        for source, expected in before.items():
            with self.subTest(source=source):
                self.assertEqual((source.read_bytes(), source.stat().st_mtime_ns), expected)

    def test_current_high_low_assets_and_sources_match_staged_bytes(self):
        sources = [(source, relative) for source, relative in build_release.runtime_sources()
                   if relative.parts[:2] == ("upstream", "high_low")]
        self.assertTrue(sources, "The checked-out High & Low source is required")
        before = {source: (build_release.sha256(source), source.stat().st_mtime_ns)
                  for source, _ in sources}
        stage = self.directory / "actual-stage"
        build_release.stage_data(stage, sources)
        alias_count = 0
        for source, relative in sources:
            with self.subTest(source=relative):
                digest, modified = before[source]
                self.assertEqual(build_release.sha256(stage / relative), digest)
                self.assertEqual((build_release.sha256(source), source.stat().st_mtime_ns), (digest, modified))
                local = Path(*relative.parts[2:])
                if local.parts[0] in ("assets", "templates") or local.name in ("icon.ico", "icon_transparent.png"):
                    self.assertEqual(build_release.sha256(stage / local), digest)
                    alias_count += 1
        self.assertGreater(alias_count, 2, "Original templates and artwork need bundle-root aliases")

    def test_high_low_activation_preserves_frozen_import_root(self):
        source = self.root / "upstream/high_low"
        module = SimpleNamespace(path=source, entry="main_ui")
        bundle_root = str(self.directory / "frozen-runtime")
        with (
            mock.patch.dict(runtime.BY_ID, {"high_low": module}, clear=True),
            mock.patch.object(runtime.sys, "frozen", True, create=True),
            mock.patch.object(runtime.sys, "_MEIPASS", bundle_root, create=True),
            mock.patch.object(runtime.sys, "path", list(sys.path)),
            mock.patch.object(runtime.os, "chdir"),
        ):
            self.assertIs(runtime.activate_source("high_low"), module)
            self.assertEqual(runtime.sys._MEIPASS, bundle_root)
            self.assertEqual(runtime.sys.path[0], str(source))


if __name__ == "__main__":
    unittest.main()
