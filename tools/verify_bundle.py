"""Verify the portable base, its feature files, and DirectML."""
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
            raise ValueError('Bundled runtime file differs: '+str(relative))
    if (ROOT/'document/SOURCE-ORIGINS.json').read_bytes() != (internal/'SOURCE-ORIGINS.json').read_bytes():
        raise ValueError('Bundled source provenance differs')
    directml = internal/'onnxruntime/capi/DirectML.dll'
    if not directml.is_file():
        raise ValueError('Shared DirectML library missing')
    if not (internal/'ddddocr/common_old.onnx').is_file():
        raise ValueError('The High & Low OCR model is missing')
    for path in ('torch', 'torchvision', 'scipy', 'scipy.libs', 'moderngl', 'tensorrt_libs',
                 'tensorrt_bindings', 'ddddocr/common.onnx', 'ddddocr/common_det.onnx',
                 'components/jump_rope/accelerators', 'components/cooking/annotations'):
        if (internal/path).exists():
            raise ValueError('Unexpected development or optional runtime: '+path)
    for pattern in ('nvinfer*.dll', 'cudart64*.dll', 'nvcuda.dll'):
        if next(internal.rglob(pattern), None) is not None:
            raise ValueError('Unexpected NVIDIA library in the standard package: '+pattern)
    return dict(passed=True, host_modules=verified,
                bundled_runtime_files=sum(path.parts[0] == 'components' for _, path in sources),
                directml_sha256=sha256(directml), executable_sha256=sha256(executable), game_inputs_sent=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.executable.resolve())
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('Verified the standard package, feature resources and DirectML')
