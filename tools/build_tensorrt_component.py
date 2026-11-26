"""Stage the separately distributed NVIDIA TensorRT runtime."""
from __future__ import annotations

import argparse
from importlib import metadata
import json
from pathlib import Path
import shutil
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from holodori.accelerator import (
    TENSORRT_ARCHITECTURE,
    TENSORRT_DISTRIBUTIONS,
    TENSORRT_FORMAT,
    TENSORRT_PYTHON,
    require_tensorrt_platform,
    tensorrt_file_sizes,
    validate_tensorrt_component,
)


def copy_distribution(name: str, version: str, folder: Path) -> None:
    distribution = metadata.distribution(name)
    if distribution.version != version:
        raise ValueError(f'Expected {name}=={version}, found {distribution.version}')
    for relative in distribution.files or ():
        top = relative.parts[0]
        if (top not in {'tensorrt', 'tensorrt_bindings', 'tensorrt_libs'}
                and not top.endswith('.dist-info')
                and tuple(relative.parts[:3]) != ('nvidia', 'cuda_runtime', 'bin')):
            continue
        if '__pycache__' in relative.parts or relative.suffix in {'.pyc', '.pyo'}:
            continue
        source = distribution.locate_file(relative)
        target = folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def build(output: Path) -> None:
    require_tensorrt_platform()
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='holodori-tensorrt-', dir=output.parent) as temporary:
        folder = Path(temporary) / 'tensorrt'
        folder.mkdir()
        for name, version in TENSORRT_DISTRIBUTIONS.items():
            copy_distribution(name, version, folder)
        record = {
            'format': TENSORRT_FORMAT,
            'python': list(TENSORRT_PYTHON),
            'architecture': TENSORRT_ARCHITECTURE,
            'versions': TENSORRT_DISTRIBUTIONS,
            'files': tensorrt_file_sizes(folder),
        }
        (folder / 'component.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
        validate_tensorrt_component(folder)
        folder.rename(output)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Target accelerators/tensorrt directory')
    parser.add_argument('--verify', action='store_true', help='Validate an existing component without modifying it')
    args = parser.parse_args()
    try:
        if args.verify:
            validate_tensorrt_component(args.output)
        else:
            build(args.output)
    except (OSError, ValueError, RuntimeError, metadata.PackageNotFoundError) as error:
        print(f'TensorRT component: {error}', file=sys.stderr)
        return 1
    print(f'Verified TensorRT component: {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
