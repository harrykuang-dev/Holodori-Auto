"""Build a portable Windows folder containing all four original runtimes.

Run from an environment containing requirements.txt and requirements-build.txt.
The upstream source files are copied as data, rather than merged into one Python
module namespace. Each component is imported by its isolated child process.
"""
from __future__ import annotations

import argparse
import ast
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ("high_low", "fishing", "jump_rope", "cooking")
SKIP_DIRECTORIES = {
    ".git", ".github", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "tests", "docs", "tools", "build", "dist",
}
SKIP_SUFFIXES = {".pyc", ".pyo", ".zip", ".7z", ".log", ".spec"}
REQUIRED_MODULES = (
    "PyInstaller", "cv2", "numpy", "PIL", "tkinter", "win32api", "win32event",
    "win32gui", "win32ui", "pygetwindow", "mss", "pydirectinput", "ddddocr",
    "onnxruntime", "numba", "llvmlite", "dxcam", "torch", "torchvision",
    "scipy", "moderngl",
)
RUNTIME_DISTRIBUTIONS = (
    "numpy", "opencv-python", "Pillow", "pywin32", "PyGetWindow", "mss",
    "PyDirectInput", "ddddocr", "onnxruntime", "numba", "llvmlite", "dxcam",
    "torch", "torchvision", "scipy", "moderngl", "comtypes", "PyInstaller",
    "pyinstaller-hooks-contrib",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def runtime_file(relative: Path) -> bool:
    """Keep original runtime bytes and notices; omit development artifacts."""
    name = relative.name.lower()
    if "license" in name or "notice" in name or name == "copying":
        return ".git" not in relative.parts
    if any(part in SKIP_DIRECTORIES for part in relative.parts):
        return False
    if relative.suffix.lower() in SKIP_SUFFIXES:
        return False
    return not name.startswith(".git")


def runtime_sources() -> list[tuple[Path, Path]]:
    sources = []
    for component in COMPONENTS:
        directory = ROOT / "upstream" / component
        entry = "gui.py" if component in {"fishing", "cooking"} else "main_ui.py"
        if not (directory / entry).is_file():
            raise ValueError(f"Missing upstream source: {directory}. Run tools/sync_upstreams.py first.")
        for source in sorted(directory.rglob("*")):
            relative = source.relative_to(directory)
            if source.is_file() and not source.is_symlink() and runtime_file(relative):
                sources.append((source, Path("upstream") / component / relative))
    return sources


def external_imports(sources: list[tuple[Path, Path]]) -> list[str]:
    """Discover dependencies without freezing colliding upstream module names."""
    python_files = [source for source, _ in sources if source.suffix == ".py"]
    local_names = {source.stem for source in python_files}
    local_names.update(source.parent.name for source in python_files if source.name == "__init__.py")
    imports = {
        "PIL.ImageTk", "tkinter.font", "tkinter.ttk", "tkinter.messagebox",
        "onnxruntime", "llvmlite.binding", "torchvision", "dxcam", "moderngl",
    }
    for source in python_files:
        tree = ast.parse(source.read_text(encoding="utf-8-sig"), filename=str(source))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                imports.add(node.module)
    return sorted(name for name in imports if name.split(".")[0] not in local_names | {"__future__"})


def validate_environment() -> None:
    if sys.platform != "win32":
        raise ValueError("Build the Windows release on Windows with 64-bit Python 3.13.")
    if sys.maxsize <= 2**32:
        raise ValueError("A 64-bit Python interpreter is required.")
    missing = [name for name in REQUIRED_MODULES if importlib.util.find_spec(name) is None]
    if missing:
        raise ValueError("Missing build/runtime modules: " + ", ".join(missing)
                         + ". Install requirements.txt and requirements-build.txt in this environment.")


def validate_models() -> None:
    cooking = ROOT / "upstream" / "cooking"
    manifest = json.loads((cooking / "models-manifest.json").read_text(encoding="utf-8"))
    failures = []
    for relative, expected in manifest["files"].items():
        model = cooking / relative
        if not model.is_file():
            failures.append(f"missing {relative}")
        elif model.stat().st_size != expected["bytes"] or sha256(model) != expected["sha256"]:
            failures.append(f"verification failed: {relative}")
    if failures:
        raise ValueError("Cooking model checkpoints are incomplete: " + "; ".join(failures)
                         + ". Install the verified upstream model archive before building.")


def stage_data(directory: Path, sources: list[tuple[Path, Path]]) -> list[tuple[str, str]]:
    staged = list(sources)
    # High & Low resolves bundled artwork/templates from the bundle root.
    # Keep that original resource layout alongside its unchanged source tree;
    # changing sys._MEIPASS would break PyInstaller's package import paths.
    for source, relative in sources:
        parts = relative.parts
        if len(parts) > 2 and parts[:2] == ('upstream', 'high_low'):
            local = Path(*parts[2:])
            if local.parts[0] in ('assets', 'templates') or local.name in ('icon.ico', 'icon_transparent.png'):
                staged.append((source, local))
    for source in sorted(ROOT.iterdir()):
        if source.is_file() and (source.suffix.lower() == ".json" or "license" in source.name.lower()
                                 or "notice" in source.name.lower()):
            staged.append((source, Path(source.name)))
    assets = ROOT / "assets"
    if assets.is_dir():
        staged.extend((source, source.relative_to(ROOT)) for source in sorted(assets.rglob("*"))
                      if source.is_file() and runtime_file(source.relative_to(assets)))
    data = []
    for source, relative in staged:
        destination = directory / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        data.append((str(destination), relative.parent.as_posix()))
    return data


def make_spec(path: Path, data: list[tuple[str, str]], hidden_imports: list[str]) -> None:
    source = f'''# Generated by tools/build_release.py; upstream programs remain filesystem sources.
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

datas = {data!r}
binaries = []
hiddenimports = {hidden_imports!r}

def production_module(name):
    return not any(part in {{'test', 'tests', 'testing'}} for part in name.split('.'))

# OCR includes ONNX model assets; capture includes its dynamically selected backends.
for package in ('ddddocr', 'dxcam'):
    package_data, package_binaries, package_imports = collect_all(
        package, filter_submodules=production_module)
    datas += package_data
    binaries += package_binaries
    hiddenimports += package_imports

# Numba loads compiler implementations dynamically when the original poker_core is imported.
hiddenimports += collect_submodules('numba', filter=production_module)
for distribution in {RUNTIME_DISTRIBUTIONS!r}:
    try:
        datas += copy_metadata(distribution)
    except Exception:
        pass  # Optional transitive metadata can be absent; modules are checked before building.

a = Analysis(
    [{str(ROOT / 'main.py')!r}], pathex=[{str(ROOT)!r}],
    binaries=binaries, datas=datas, hiddenimports=sorted(set(hiddenimports)),
    hookspath=[], hooksconfig={{}}, runtime_hooks=[],
    excludes=['pytest', 'matplotlib', 'IPython', 'tensorflow', 'tensorboard', 'pandas', 'sympy.testing'],
    noarchive=False, optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name='Holodori-Auto',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False,
    icon={str(ROOT / 'assets' / 'holodori.ico')!r},
)
collect = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Holodori-Auto')
'''
    path.write_text(source, encoding="utf-8")


def package_versions() -> dict[str, str]:
    versions = {}
    for name in RUNTIME_DISTRIBUTIONS:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            pass
    return versions


def write_checksums(directory: Path) -> None:
    lines = [f"{sha256(path)}  {path.relative_to(directory).as_posix()}"
             for path in sorted(directory.rglob("*"))
             if path.is_file() and path.name != "SHA256SUMS.txt"]
    (directory / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def archive_bundle(directory: Path) -> Path:
    archive = directory.with_suffix(".zip")
    if archive.exists():
        raise ValueError(f"Archive already exists: {archive}")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                         allowZip64=True) as bundle:
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                bundle.write(path, (Path(directory.name) / path.relative_to(directory)).as_posix())
    archive.with_name(archive.name + ".sha256").write_text(
        f"{sha256(archive)}  {archive.name}\n", encoding="ascii")
    return archive


def build(output: Path, *, spec_only: bool, create_zip: bool) -> None:
    if not spec_only:
        if output.exists():
            raise ValueError(f"Output already exists: {output}. Choose a fresh --output directory.")
        if not (ROOT / "main.py").is_file():
            raise ValueError(f"Missing application entry point: {ROOT / 'main.py'}")
        validate_environment()
        validate_models()
    sources = runtime_sources()
    imports = external_imports(sources)
    work = ROOT / "work"
    work.mkdir(exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="release-", dir=work))
    try:
        data = stage_data(staging / "data", sources)
        spec = staging / "Holodori-Auto.spec"
        make_spec(spec, data, imports)
        if spec_only:
            print(f"Generated unchecked build specification: {spec}")
            print(f"Original runtime files: {len(sources)}; external imports: {len(imports)}")
            return
        subprocess.run([
            sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm",
            "--distpath", str(staging / "dist"), "--workpath", str(staging / "build"), str(spec),
        ], cwd=ROOT, check=True)
        bundle = staging / "dist" / "Holodori-Auto"
        runtime = bundle / "_internal"
        for original, relative in sources:
            copied = runtime / relative
            if not copied.is_file() or sha256(original) != sha256(copied):
                raise ValueError(f"Bundled upstream file differs: {relative}")
        info = {
            "built_at_utc": datetime.now(timezone.utc).isoformat(),
            "python": sys.version,
            "packages": package_versions(),
            "upstream_runtime_files": len(sources),
            "upstream_sources_verified": True,
        }
        (bundle / "build-info.json").write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
        write_checksums(bundle)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(bundle), str(output))
        print(f"Built and verified: {output / 'Holodori-Auto.exe'}")
        if create_zip:
            print(f"Portable archive: {archive_bundle(output)}")
    finally:
        if not spec_only:
            # This directory was created uniquely by this invocation under ROOT/work.
            resolved = staging.resolve()
            if resolved.parent == work.resolve() and resolved.name.startswith("release-"):
                shutil.rmtree(resolved)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / "Holodori-Auto",
                        help="Fresh destination folder for the portable program.")
    parser.add_argument("--spec-only", action="store_true",
                        help="Generate a persistent specification in work/ without building or validating dependencies/models.")
    parser.add_argument("--zip", action="store_true", help="Also create a portable ZIP and its SHA-256 file.")
    args = parser.parse_args()
    try:
        build(args.output.resolve(), spec_only=args.spec_only, create_zip=args.zip)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
