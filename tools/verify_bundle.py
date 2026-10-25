"""Verify frozen host code, unchanged upstream files and shared GPU libraries."""
from __future__ import annotations
import argparse
import hashlib
import json
import marshal
from pathlib import Path
import sys
from PyInstaller.archive.readers import CArchiveReader
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.build_release import ROOT, runtime_sources, sha256


def verify(executable: Path) -> dict:
    bundle = executable.parent
    internal = bundle/'_internal'
    archive = CArchiveReader(str(executable))
    modules = archive.open_embedded_archive('PYZ.pyz')
    verified = []
    for source in [ROOT/'main.py', *sorted((ROOT/'holodori').glob('*.py'))]:
        relative = source.relative_to(ROOT)
        name = '.'.join(relative.with_suffix('').parts)
        if source.name == '__init__.py':
            name = source.parent.name
        frozen = marshal.loads(archive.extract('main')) if name == 'main' else modules.extract(name)
        expected = compile(source.read_text(encoding='utf-8'), frozen.co_filename, 'exec', dont_inherit=True)
        if frozen != expected:
            raise ValueError('Frozen host differs: '+name)
        verified.append(name)
    sources = runtime_sources()
    for source, relative in sources:
        if sha256(source) != sha256(internal/relative):
            raise ValueError('Bundled upstream differs: '+str(relative))
    if (ROOT/'upstream-lock.json').read_bytes() != (internal/'upstream-lock.json').read_bytes():
        raise ValueError('Bundled source pins differ')
    shared = {}
    for name in ('nvinfer_10.dll', 'nvinfer_builder_resource_10.dll', 'cudart64_12.dll'):
        matches = list(internal.rglob(name))
        if len(matches) != 1:
            raise ValueError(f'Expected one shared {name}, found {len(matches)}')
        shared[name] = {'path': matches[0].relative_to(internal).as_posix(), 'sha256': sha256(matches[0])}
    if not (internal/'onnxruntime/capi/DirectML.dll').is_file():
        raise ValueError('Shared DirectML library missing')
    for path in ('torch', 'torchvision', 'upstream/jump_rope/accelerators', 'upstream/cooking/annotations'):
        if (internal/path).exists():
            raise ValueError('Unexpected development/runtime copy: '+path)
    if list(internal.rglob('nvcuda.dll')):
        raise ValueError('System NVIDIA driver must not be bundled')
    for pattern in ('tensorrt_cu12_libs-*.dist-info/LICENSE.txt', 'nvidia_cuda_runtime_cu12-*.dist-info/licenses/*'):
        if not list(internal.glob(pattern)):
            raise ValueError('Missing dependency license: '+pattern)
    return dict(passed=True, host_modules=verified, unchanged_upstream_files=len(sources),
                shared_libraries=shared, executable_sha256=sha256(executable), game_inputs_sent=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.executable.resolve())
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('Verified frozen host, upstream resources and one shared GPU runtime')
