"""Install the pinned cooking release's verified models, or check them offline."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from typing import BinaryIO
import urllib.error
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
COOKING_ROOT = ROOT / "upstream" / "cooking"
RELEASE_BASE = (
    "https://github.com/harrykuang-dev/"
    "Hololive-Dreams-Collect-Cooking-Auto/releases/download"
)
CHUNK_SIZE = 1024 * 1024


class ModelError(ValueError):
    """A model, manifest, or release archive did not match the pinned source."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_fingerprint(value: object, label: str) -> None:
    if not isinstance(value, dict):
        raise ModelError(f"Invalid fingerprint: {label}")
    if type(value.get("bytes")) is not int or value["bytes"] <= 0:
        raise ModelError(f"Invalid byte count: {label}")
    if not re.fullmatch(r"[0-9a-f]{64}", str(value.get("sha256", ""))):
        raise ModelError(f"Invalid SHA-256: {label}")


def _safe_name(name: object) -> str:
    if not isinstance(name, str) or not name:
        raise ModelError("Invalid model path")
    path = PurePosixPath(name)
    if (
        path.is_absolute()
        or "\\" in name
        or any(character in '<>:"|?*' or ord(character) < 32 for character in name)
        or path.as_posix() != name
        or any(part in {".", ".."} or part.endswith((".", " ")) for part in path.parts)
        or len(path.parts) < 3
        or path.parts[0] != "outputs"
        or path.parts[1] not in {"kitchen-bot", "kitchen-labeler"}
        or path.suffix != ".pt"
    ):
        raise ModelError(f"Unsafe model path: {name!r}")
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update(f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10))
    if any(part.split(".")[0].upper() in reserved for part in path.parts):
        raise ModelError(f"Reserved model path: {name!r}")
    return name


def load_manifest(cooking_root: Path = COOKING_ROOT) -> dict:
    manifest_path = cooking_root / "models-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ModelError(f"Cannot read {manifest_path}; initialize the submodules first") from error
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict) or not manifest["files"]:
        raise ModelError("The cooking manifest has no checkpoint files")
    _validate_fingerprint(
        {"bytes": manifest.get("archive_bytes"), "sha256": manifest.get("archive_sha256")},
        "models.zip",
    )
    folded_paths = set()
    for name, expected in manifest["files"].items():
        _safe_name(name)
        if name.casefold() in folded_paths:
            raise ModelError(f"Duplicate model path on Windows: {name}")
        folded_paths.add(name.casefold())
        _validate_fingerprint(expected, name)
    return manifest


def _destination(cooking_root: Path, name: str) -> Path:
    root = cooking_root.resolve()
    target = root.joinpath(*PurePosixPath(_safe_name(name)).parts)
    if not target.resolve().is_relative_to(root):
        raise ModelError(f"Model destination leaves the cooking directory: {name}")
    current = target
    while current != root:
        if current.is_symlink():
            raise ModelError(f"Model destination is a symbolic link: {name}")
        current = current.parent
    return target


def _verify_file(path: Path, expected: dict, label: str) -> None:
    if not path.is_file():
        raise ModelError(f"Missing model: {label}")
    if path.stat().st_size != expected["bytes"]:
        raise ModelError(f"Size mismatch: {label}")
    if sha256_file(path) != expected["sha256"]:
        raise ModelError(f"SHA-256 mismatch: {label}")


def check_models(cooking_root: Path = COOKING_ROOT) -> int:
    """Verify installed checkpoints without network access or game input."""
    manifest = load_manifest(cooking_root)
    for name, expected in manifest["files"].items():
        _verify_file(_destination(cooking_root, name), expected, name)
    return len(manifest["files"])


def verify_existing_models(cooking_root: Path, manifest: dict) -> None:
    for name, expected in manifest["files"].items():
        target = _destination(cooking_root, name)
        if target.exists():
            try:
                _verify_file(target, expected, name)
            except ModelError as error:
                raise ModelError(f"Existing model differs; move it to a backup location first: {name}") from error


def model_release_url(cooking_root: Path = COOKING_ROOT) -> str:
    """Read the release version without importing the cooking program."""
    try:
        module = ast.parse((cooking_root / "gui.py").read_text(encoding="utf-8-sig"))
    except (OSError, SyntaxError) as error:
        raise ModelError("Cannot read the pinned cooking program version") from error
    for statement in module.body:
        if isinstance(statement, ast.Assign):
            targets = statement.targets
        elif isinstance(statement, ast.AnnAssign):
            targets = [statement.target]
        else:
            continue
        if any(isinstance(target, ast.Name) and target.id == "VERSION" for target in targets):
            if isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                version = statement.value.value
                if re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?", version):
                    return f"{RELEASE_BASE}/v{version}/models.zip"
    raise ModelError("The pinned cooking source has no supported VERSION value")


def _copy_verified(source: BinaryIO, target: BinaryIO, expected: dict, label: str) -> None:
    digest = hashlib.sha256()
    copied = 0
    for chunk in iter(lambda: source.read(CHUNK_SIZE), b""):
        copied += len(chunk)
        if copied > expected["bytes"]:
            raise ModelError(f"Download or archive entry exceeds its pinned size: {label}")
        digest.update(chunk)
        target.write(chunk)
    if copied != expected["bytes"] or digest.hexdigest() != expected["sha256"]:
        raise ModelError(f"Size or SHA-256 mismatch: {label}")
    target.flush()
    os.fsync(target.fileno())


def download_archive(url: str, destination: Path, manifest: dict) -> None:
    expected = {"bytes": manifest["archive_bytes"], "sha256": manifest["archive_sha256"]}
    request = urllib.request.Request(url, headers={"User-Agent": "Holodori-Auto model installer"})
    created = False
    try:
        with urllib.request.urlopen(request, timeout=60) as source:
            with destination.open("xb") as target:
                created = True
                _copy_verified(source, target, expected, "models.zip")
    except BaseException:
        if created:
            destination.unlink(missing_ok=True)
        raise


def install_archive(archive: Path, cooking_root: Path = COOKING_ROOT) -> int:
    """Verify the entire archive before installing only missing checkpoints.

    Existing checkpoints must already match. Hard links publish complete staged
    files without replacing an existing destination, including concurrent writes.
    """
    manifest = load_manifest(cooking_root)
    _verify_file(
        archive,
        {"bytes": manifest["archive_bytes"], "sha256": manifest["archive_sha256"]},
        "models.zip",
    )
    targets = {name: _destination(cooking_root, name) for name in manifest["files"]}
    verify_existing_models(cooking_root, manifest)
    installed = []
    with tempfile.TemporaryDirectory(prefix=".holodori-models-", dir=cooking_root) as temporary:
        staged_root = Path(temporary)
        with zipfile.ZipFile(archive) as bundle:
            entries = bundle.infolist()
            if len(entries) != len(targets) or {entry.filename for entry in entries} != set(targets):
                raise ModelError("Unexpected, missing, or duplicate archive paths")
            for entry in entries:
                expected = manifest["files"][entry.filename]
                if entry.is_dir() or stat.S_ISLNK(entry.external_attr >> 16) or entry.flag_bits & 1:
                    raise ModelError(f"Unsupported archive entry: {entry.filename}")
                if entry.file_size != expected["bytes"]:
                    raise ModelError(f"Archive entry size mismatch: {entry.filename}")
                staged = staged_root / entry.filename
                staged.parent.mkdir(parents=True, exist_ok=True)
                with bundle.open(entry) as source, staged.open("xb") as target:
                    _copy_verified(source, target, expected, entry.filename)
        try:
            for name, target in targets.items():
                # Recheck containment immediately before creating destinations.
                target = _destination(cooking_root, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    os.link(staged_root / name, target)
                except FileExistsError:
                    _verify_file(target, manifest["files"][name], name)
                else:
                    installed.append(target)
        except BaseException:
            for target in reversed(installed):
                target.unlink(missing_ok=True)
            raise
    return len(manifest["files"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--check", action="store_true", help="Verify installed model files offline")
    source.add_argument("--archive", type=Path, help="Install an already downloaded models.zip")
    args = parser.parse_args(argv)
    try:
        if args.check:
            count = check_models()
            print(f"Verified {count} cooking models.")
            return 0
        if args.archive:
            count = install_archive(args.archive)
        else:
            try:
                count = check_models()
            except ModelError:
                manifest = load_manifest()
                verify_existing_models(COOKING_ROOT, manifest)
                url = model_release_url()
                print(f"Downloading {url} ({manifest['archive_bytes']:,} bytes)...")
                with tempfile.TemporaryDirectory(prefix="holodori-model-download-") as temporary:
                    archive = Path(temporary) / "models.zip"
                    download_archive(url, archive, manifest)
                    count = install_archive(archive)
        print(f"Ready: {count} cooking models.")
        return 0
    except (ModelError, OSError, urllib.error.URLError, zipfile.BadZipFile) as error:
        print(f"Model setup failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
