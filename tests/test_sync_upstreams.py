"""Offline Git integration tests; no GitHub account or network is used."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import sync_upstreams as sync


class SyncUpstreamsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="holodori-sync-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / "integration"
        self.root.mkdir()
        self.command(self.root, "init", "-b", "main")
        self.command(self.root, "config", "core.autocrlf", "false")
        self.remotes = {}
        for name, (filename, constant) in sync.MODULES.items():
            remote = self.base / name
            remote.mkdir()
            self.command(remote, "init", "-b", "main")
            self.command(remote, "config", "core.autocrlf", "false")
            (remote / filename).write_text(f"{constant} = '1.0.0'\n", encoding="utf-8")
            (remote / ".gitignore").write_text("local-cache.txt\n", encoding="utf-8")
            self.commit(remote, "Initial upstream")
            self.command(self.root, "-c", "protocol.file.allow=always", "submodule", "add", "-b", "main", str(remote), f"upstream/{name}")
            self.command(self.root / "upstream" / name, "config", "core.autocrlf", "false")
            self.remotes[name] = remote
        (self.root / "README.md").write_text("Local integration\n", encoding="utf-8")
        sync.synchronize(self.root, list(sync.MODULES), initial_lock=True)
        self.commit(self.root, "Initial integration")

    def command(self, directory, *args):
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        result = subprocess.run(["git", "-C", str(directory), *args],
                                text=True, encoding="utf-8", errors="replace",
                                capture_output=True, check=False, env=env)
        if result.returncode:
            self.fail(f"Git fixture command failed: {args}: {result.stderr}")
        return result.stdout.strip()

    def commit(self, directory, message):
        self.command(directory, "add", ".")
        self.command(directory, "-c", "user.name=Offline test", "-c", "user.email=test@example.invalid",
                     "-c", "commit.gpgsign=false", "commit", "-m", message)
        return self.command(directory, "rev-parse", "HEAD")

    def advance(self, name, version="1.1.0"):
        filename, constant = sync.MODULES[name]
        (self.remotes[name] / filename).write_text(f"{constant} = '{version}'\n", encoding="utf-8")
        return self.commit(self.remotes[name], "New upstream version")

    def lock(self):
        return json.loads((self.root / sync.LOCK_NAME).read_text(encoding="utf-8"))

    def head(self, name):
        return self.command(self.root / "upstream" / name, "rev-parse", "HEAD")

    def test_initial_lock_records_exact_pins_and_literal_versions(self):
        report = sync.synchronize(self.root, list(sync.MODULES), verify=True)
        self.assertFalse(report["changed"])
        for name in sync.MODULES:
            entry = self.lock()["modules"][name]
            self.assertEqual(entry["commit"], self.head(name))
            self.assertEqual(entry["version"], "1.0.0")
            self.assertEqual(entry["branch"], "main")
        with self.assertRaisesRegex(sync.SyncError, "already exists"):
            sync.synchronize(self.root, list(sync.MODULES), initial_lock=True)

    def test_check_fetches_but_preserves_checkouts_index_lock_and_local_edits(self):
        old = self.head("fishing")
        new = self.advance("fishing")
        note = self.root / "upstream/fishing/my-note.txt"
        note.write_text("Keep this note", encoding="utf-8")
        before_status = self.command(self.root, "status", "--porcelain")
        before_index = self.command(self.root, "ls-files", "--stage")
        before_lock = (self.root / sync.LOCK_NAME).read_bytes()
        report = sync.synchronize(self.root, ["fishing"], check=True)
        self.assertTrue(report["changed"])
        self.assertEqual(report["modules"][0]["after"], new)
        self.assertEqual(self.head("fishing"), old)
        self.assertEqual(self.command(self.root, "status", "--porcelain"), before_status)
        self.assertEqual(self.command(self.root, "ls-files", "--stage"), before_index)
        self.assertEqual((self.root / sync.LOCK_NAME).read_bytes(), before_lock)
        self.assertEqual(note.read_text(encoding="utf-8"), "Keep this note")

    def test_update_only_selected_preserves_unrelated_root_edits_and_leaves_unstaged(self):
        old_high_low = self.head("high_low")
        new_fishing = self.advance("fishing", "1.2.3")
        self.advance("high_low")
        (self.root / "README.md").write_text("My unrelated work\n", encoding="utf-8")
        (self.root / "my-note.txt").write_text("Keep me", encoding="utf-8")
        before_index = self.command(self.root, "ls-files", "--stage")
        report = sync.synchronize(self.root, ["fishing"])
        self.assertTrue(report["changed"])
        self.assertEqual(self.head("fishing"), new_fishing)
        self.assertEqual(self.head("high_low"), old_high_low)
        self.assertEqual(self.lock()["modules"]["fishing"]["version"], "1.2.3")
        self.assertEqual(self.command(self.root, "ls-files", "--stage"), before_index)
        self.assertEqual((self.root / "README.md").read_text(encoding="utf-8"), "My unrelated work\n")
        self.assertEqual((self.root / "my-note.txt").read_text(encoding="utf-8"), "Keep me")
        with self.assertRaises(sync.SyncError):
            sync.synchronize(self.root, list(sync.MODULES), verify=True)
        self.command(self.root, "add", "upstream/fishing", sync.LOCK_NAME)
        sync.synchronize(self.root, list(sync.MODULES), verify=True)

    def test_update_refuses_tracked_or_untracked_submodule_edits(self):
        self.advance("fishing")
        previous = self.head("fishing")
        for filename in ["gui.py", "my-untracked-note.txt"]:
            with self.subTest(filename=filename):
                target = self.root / "upstream/fishing" / filename
                original = target.read_bytes() if target.exists() else None
                target.write_text("Local changes\n", encoding="utf-8")
                with self.assertRaises(sync.SyncError):
                    sync.synchronize(self.root, ["fishing"])
                self.assertEqual(self.head("fishing"), previous)
                self.assertEqual(target.read_text(encoding="utf-8"), "Local changes\n")
                if original is None:
                    target.unlink()
                else:
                    target.write_bytes(original)

    def test_update_refuses_lock_edits_without_overwriting_them(self):
        self.advance("fishing")
        path = self.root / sync.LOCK_NAME
        edited = path.read_text(encoding="utf-8") + "\n"
        path.write_text(edited, encoding="utf-8")
        with self.assertRaises(sync.SyncError):
            sync.synchronize(self.root, ["fishing"])
        self.assertEqual(path.read_text(encoding="utf-8"), edited)

    def test_verify_detects_wrong_commit_or_version_without_fetching(self):
        lock = self.lock()
        lock["modules"]["fishing"]["version"] = "9.9.9"
        sync.write_lock(self.root, lock)
        with self.assertRaisesRegex(sync.SyncError, "does not match"):
            sync.synchronize(self.root, list(sync.MODULES), verify=True)

    def test_no_change_update_keeps_lock_bytes(self):
        before = (self.root / sync.LOCK_NAME).read_bytes()
        report = sync.synchronize(self.root, list(sync.MODULES))
        self.assertFalse(report["changed"])
        self.assertEqual((self.root / sync.LOCK_NAME).read_bytes(), before)
        self.assertEqual(self.command(self.root, "status", "--porcelain"), "")

    def test_failed_fetch_does_not_partly_update_any_checkout(self):
        self.advance("high_low")
        self.command(self.root / "upstream/fishing", "remote", "set-url", "origin", str(self.base / "missing"))
        before = {name: self.head(name) for name in sync.MODULES}
        before_lock = (self.root / sync.LOCK_NAME).read_bytes()
        with self.assertRaises(sync.SyncError):
            sync.synchronize(self.root, ["high_low", "fishing"])
        self.assertEqual({name: self.head(name) for name in sync.MODULES}, before)
        self.assertEqual((self.root / sync.LOCK_NAME).read_bytes(), before_lock)

    def test_update_does_not_overwrite_ignored_files(self):
        child = self.root / "upstream/fishing"
        ignored = child / "local-cache.txt"
        ignored.write_text("Local cache that must survive", encoding="utf-8")
        remote = self.remotes["fishing"]
        (remote / "local-cache.txt").write_text("New tracked file", encoding="utf-8")
        self.command(remote, "add", "--force", "local-cache.txt")
        self.commit(remote, "Track former cache path")
        before = self.head("fishing")
        with self.assertRaises(sync.SyncError):
            sync.synchronize(self.root, ["fishing"])
        self.assertEqual(self.head("fishing"), before)
        self.assertEqual(ignored.read_text(encoding="utf-8"), "Local cache that must survive")

    def test_later_checkout_failure_rolls_back_earlier_commit_and_branch(self):
        self.advance("high_low")
        child = self.root / "upstream/fishing"
        (child / "local-cache.txt").write_text("Preserved local cache", encoding="utf-8")
        remote = self.remotes["fishing"]
        (remote / "local-cache.txt").write_text("Tracked upstream file", encoding="utf-8")
        self.command(remote, "add", "--force", "local-cache.txt")
        self.commit(remote, "Track former cache path")
        before = {name: self.head(name) for name in sync.MODULES}
        branch = self.command(self.root / "upstream/high_low", "symbolic-ref", "--short", "HEAD")
        before_lock = (self.root / sync.LOCK_NAME).read_bytes()
        with self.assertRaises(sync.SyncError):
            sync.synchronize(self.root, ["high_low", "fishing"])
        self.assertEqual({name: self.head(name) for name in sync.MODULES}, before)
        self.assertEqual(self.command(self.root / "upstream/high_low", "symbolic-ref", "--short", "HEAD"), branch)
        self.assertEqual((self.root / sync.LOCK_NAME).read_bytes(), before_lock)


if __name__ == "__main__":
    unittest.main()
