"""Offline model installation tests. No game or upstream runtime is imported."""
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

from tools import fetch_models


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "cooking"
        self.root.mkdir()
        self.contents = {
            "outputs/kitchen-bot/icon-classifier.pt": b"icon checkpoint",
            "outputs/kitchen-labeler/point-classifier-resnet18.pt": b"point checkpoint",
        }
        self.archive = Path(self.temporary.name) / "models.zip"
        self.write_archive()

    def fingerprint(self, content):
        return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}

    def write_archive(self, entries=None, expected_contents=None):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.archive, "w") as bundle:
                for name, content in (entries or list(self.contents.items())):
                    bundle.writestr(name, content)
        archive = self.fingerprint(self.archive.read_bytes())
        self.manifest = {
            "runtime_version": "test",
            "archive_bytes": archive["bytes"],
            "archive_sha256": archive["sha256"],
            "files": {
                name: self.fingerprint(content)
                for name, content in (expected_contents or self.contents).items()
            },
        }
        self.write_manifest()

    def write_manifest(self):
        (self.root / "models-manifest.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def install_one(self, content=None):
        name = next(iter(self.contents))
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.contents[name] if content is None else content)
        return target

    def test_install_and_check_preserve_matching_existing_models(self):
        existing = self.install_one()
        before = existing.stat().st_mtime_ns
        self.assertEqual(fetch_models.install_archive(self.archive, self.root), 2)
        self.assertEqual(fetch_models.check_models(self.root), 2)
        self.assertEqual(existing.stat().st_mtime_ns, before)
        self.assertEqual(fetch_models.install_archive(self.archive, self.root), 2)
        self.assertEqual(list(self.root.glob(".holodori-models-*")), [])

    def test_existing_mismatch_preserved_and_no_other_model_installed(self):
        existing = self.install_one(b"personal checkpoint")
        with self.assertRaises(fetch_models.ModelError):
            fetch_models.install_archive(self.archive, self.root)
        self.assertEqual(existing.read_bytes(), b"personal checkpoint")
        self.assertFalse((self.root / list(self.contents)[1]).exists())

    def test_archive_fingerprint_checked_before_mutation(self):
        self.archive.write_bytes(self.archive.read_bytes() + b"changed")
        with self.assertRaises(fetch_models.ModelError):
            fetch_models.install_archive(self.archive, self.root)
        self.assertFalse((self.root / "outputs").exists())

    def test_bad_checkpoint_preserves_existing_and_installs_nothing(self):
        existing = self.install_one()
        wrong = list(self.contents.items())
        wrong[1] = (wrong[1][0], b"bad checkpoint!!")
        self.write_archive(wrong)
        with self.assertRaises(fetch_models.ModelError):
            fetch_models.install_archive(self.archive, self.root)
        self.assertEqual(existing.read_bytes(), self.contents[wrong[0][0]])
        self.assertFalse((self.root / wrong[1][0]).exists())

    def test_extra_and_duplicate_entries_rejected(self):
        for extra in ("../escaped.pt", "outputs/kitchen-bot/icon-classifier.pt"):
            with self.subTest(extra=extra):
                self.write_archive(list(self.contents.items()) + [(extra, b"untrusted")])
                with self.assertRaises(fetch_models.ModelError):
                    fetch_models.install_archive(self.archive, self.root)
                self.assertFalse((self.root / "outputs").exists())

    def test_unsafe_manifest_paths_rejected(self):
        for name in (
            "../outside.pt", "C:/outside.pt", "outputs/kitchen-bot/../outside.pt",
            "outputs/kitchen-bot\\outside.pt", "outputs/kitchen-bot/CON.pt",
            "outputs/kitchen-bot/folder./outside.pt", "outputs//kitchen-bot/outside.pt",
        ):
            with self.subTest(name=name):
                self.manifest["files"] = {name: self.fingerprint(b"model")}
                self.write_manifest()
                with self.assertRaises(fetch_models.ModelError):
                    fetch_models.load_manifest(self.root)

    def test_case_collisions_rejected_on_all_platforms(self):
        name = next(iter(self.contents))
        self.manifest["files"][name.replace("icon-classifier", "ICON-CLASSIFIER")] = (
            self.manifest["files"][name]
        )
        self.write_manifest()
        with self.assertRaises(fetch_models.ModelError):
            fetch_models.load_manifest(self.root)

    def test_archive_symlink_rejected(self):
        first = next(iter(self.contents))
        info = zipfile.ZipInfo(first)
        info.create_system = 3
        info.external_attr = 0o120777 << 16
        entries = [(info, self.contents[first]), list(self.contents.items())[1]]
        self.write_archive(entries)
        with self.assertRaises(fetch_models.ModelError):
            fetch_models.install_archive(self.archive, self.root)
        self.assertFalse((self.root / "outputs").exists())

    def test_offline_check_reports_missing_and_corrupted_files(self):
        with self.assertRaisesRegex(fetch_models.ModelError, "Missing model"):
            fetch_models.check_models(self.root)
        fetch_models.install_archive(self.archive, self.root)
        self.install_one(b"x" * len(next(iter(self.contents.values()))))
        with self.assertRaisesRegex(fetch_models.ModelError, "SHA-256 mismatch"):
            fetch_models.check_models(self.root)

    def test_install_failure_rolls_back_only_new_files(self):
        original_link = fetch_models.os.link
        calls = 0

        def fail_second(source, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("simulated disk failure")
            return original_link(source, destination)

        with mock.patch.object(fetch_models.os, "link", side_effect=fail_second):
            with self.assertRaises(OSError):
                fetch_models.install_archive(self.archive, self.root)
        self.assertTrue(all(not (self.root / name).exists() for name in self.contents))

    def test_version_read_without_importing_game_program(self):
        (self.root / "gui.py").write_text("VERSION = '2.3.4'\nraise RuntimeError('must not execute')\n", encoding="utf-8")
        self.assertTrue(fetch_models.model_release_url(self.root).endswith("/v2.3.4/models.zip"))

    def test_download_rejects_truncated_or_oversized_data(self):
        expected = self.fingerprint(b"archive")
        manifest = {"archive_bytes": expected["bytes"], "archive_sha256": expected["sha256"]}
        destination = Path(self.temporary.name) / "download.zip"
        for content in (b"short", b"archive" * 2):
            with self.subTest(content=content):
                with mock.patch.object(fetch_models.urllib.request, "urlopen", return_value=io.BytesIO(content)):
                    with self.assertRaises(fetch_models.ModelError):
                        fetch_models.download_archive("https://example.invalid/models.zip", destination, manifest)
                self.assertFalse(destination.exists())

    def test_download_does_not_replace_an_existing_archive(self):
        destination = Path(self.temporary.name) / "download.zip"
        destination.write_bytes(b"keep this archive")
        with mock.patch.object(fetch_models.urllib.request, "urlopen", return_value=io.BytesIO(b"archive")):
            with self.assertRaises(FileExistsError):
                fetch_models.download_archive("https://example.invalid/models.zip", destination, self.manifest)
        self.assertEqual(destination.read_bytes(), b"keep this archive")


if __name__ == "__main__":
    unittest.main()
