"""Discover and activate the shared optional Windows TensorRT component."""
from __future__ import annotations

import ctypes
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
from threading import Lock


TENSORRT_DISTRIBUTIONS = {
    'tensorrt-cu12': '10.13.3.9.post1',
    'tensorrt-cu12-bindings': '10.13.3.9.post1',
    'tensorrt-cu12-libs': '10.13.3.9.post1',
    'nvidia-cuda-runtime-cu12': '12.9.79',
}
TENSORRT_COMPONENT = Path('accelerators/tensorrt')
TENSORRT_FORMAT = 3
TENSORRT_PYTHON = (3, 13)
TENSORRT_ARCHITECTURE = 'win_amd64'
BUILDER_LIBRARY = 'tensorrt_libs/nvinfer_builder_resource_10.dll'
TENSORRT_FILES = (
    'tensorrt/__init__.py',
    'tensorrt_bindings/__init__.py',
    'tensorrt_bindings/tensorrt.cp313-win_amd64.pyd',
    'tensorrt_libs/__init__.py',
    'tensorrt_libs/nvinfer_10.dll',
    BUILDER_LIBRARY,
    'tensorrt_libs/nvinfer_plugin_10.dll',
    'tensorrt_libs/nvonnxparser_10.dll',
    'nvidia/cuda_runtime/bin/cudart64_12.dll',
)
DLL_DIRECTORIES = ('tensorrt_libs', 'tensorrt_bindings', 'nvidia/cuda_runtime/bin')

_lock = Lock()
_active_root: Path | None = None
_dll_handles = []
_builder_module = None


class TensorRTUnavailable(RuntimeError):
    """The current process cannot use the optional accelerator."""


def require_tensorrt_platform() -> None:
    if (sys.platform != 'win32' or sys.maxsize <= 2**32
            or platform.machine().lower() not in {'amd64', 'x86_64'}
            or sys.version_info[:2] != TENSORRT_PYTHON):
        raise TensorRTUnavailable('TensorRT requires Windows x64 with Python 3.13')


def tensorrt_file_sizes(folder: Path) -> dict[str, int]:
    sizes = {}
    for relative in TENSORRT_FILES:
        path = folder / relative
        size = path.stat().st_size if path.is_file() else 0
        if size <= 0:
            raise TensorRTUnavailable(f'TensorRT component is incomplete: {relative}')
        sizes[relative] = size
    return sizes


def validate_tensorrt_component(folder: Path) -> None:
    """Validate the receipt and check file sizes before registering DLL paths."""
    try:
        record = json.loads((folder / 'component.json').read_text(encoding='utf-8'))
    except FileNotFoundError as error:
        raise TensorRTUnavailable('Install the TensorRT component next to Holodori-Auto') from error
    except (OSError, ValueError) as error:
        raise TensorRTUnavailable('Cannot read the TensorRT component receipt') from error
    if (not isinstance(record, dict)
            or record.get('format') != TENSORRT_FORMAT
            or record.get('python') != list(TENSORRT_PYTHON)
            or record.get('architecture') != TENSORRT_ARCHITECTURE
            or record.get('versions') != TENSORRT_DISTRIBUTIONS):
        raise TensorRTUnavailable('Incompatible TensorRT component for this version of Holodori-Auto')
    if record.get('files') != tensorrt_file_sizes(folder):
        raise TensorRTUnavailable('TensorRT component is incomplete or damaged')


def activate_tensorrt_component() -> Path:
    """Make TensorRT importable in the current feature process."""
    global _active_root
    with _lock:
        if _active_root is not None:
            return _active_root

        require_tensorrt_platform()
        frozen = getattr(sys, 'frozen', False)
        base = Path(sys.executable).resolve().parent if frozen else Path(__file__).resolve().parents[1]
        folder = base / TENSORRT_COMPONENT
        use_addon = frozen or folder.exists()
        if use_addon:
            validate_tensorrt_component(folder)
        else:
            spec = importlib.util.find_spec('tensorrt')
            if spec is None or not spec.origin:
                raise TensorRTUnavailable('Install the optional TensorRT dependencies')
            folder = Path(spec.origin).resolve().parents[1]
            tensorrt_file_sizes(folder)

        handles = []
        try:
            for relative in DLL_DIRECTORIES:
                handles.append(os.add_dll_directory(str(folder / relative)))
        except OSError:
            for handle in reversed(handles):
                handle.close()
            raise

        if use_addon:
            sys.path.insert(0, str(folder))
        _dll_handles.extend(handles)
        _active_root = folder
        return folder


def load_builder_library() -> None:
    """Load the resource DLL before TensorRT's delayed builder lookup."""
    folder = activate_tensorrt_component()
    global _builder_module
    with _lock:
        if _builder_module is None:
            _builder_module = ctypes.WinDLL(str(folder / BUILDER_LIBRARY))
