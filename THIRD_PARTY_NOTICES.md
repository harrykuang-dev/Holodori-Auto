# Source programs and notices

Holodori-Auto loads these original programs at the commits recorded in `upstream-lock.json`:

| Function | Source | Included notices |
| --- | --- | --- |
| High & Low | [Hololive-Dreams-High-low-Auto-Personal](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal) | `upstream/high_low/licenses/` |
| Fishing | [Hololive-Dreams-Fishing-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto) | Original repository license and `assets/NOTICE.md` |
| Jump Rope | [Hololive-Dreams-Jump-Rope-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto) | AGPL-3.0: `upstream/jump_rope/LICENSE`, `NOTICE.md`, `models/AGPL-3.0.txt`, `third_party/` |
| Cooking | [Hololive-Dreams-Collect-Cooking-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Collect-Cooking-Auto) | `upstream/cooking/third-party/` |

Source notices, resource notices, model manifests and bundled dependency license files are retained in portable builds. Each original program, model and dependency remains subject to its own terms.

Jump Rope 1.3.0 and its YOLO26-derived model use AGPL-3.0. The exact corresponding source is identified by the repository and commit in `upstream-lock.json`; its public training and annotation material remains available in the original repository.

TensorRT 10.13.3.9, CUDA runtime 12.9.79 and ONNX Runtime DirectML 1.24.4 are shared by the two GPU modules. Their package licenses and notices are retained with the shared runtime. NVIDIA's system display driver is not redistributed.
