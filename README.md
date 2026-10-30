# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

A Windows program that brings **High & Low**, **Fishing**, **Jump Rope**, and **Cooking** for *hololive Dreams* into one window. The four modules share language and Start/Stop shortcuts while keeping their original game logic, controls, statistics, and diagnostics. Navigation and shared settings follow the same Fluent visual style and use each module's original artwork and accent color.

| Module | Original program |
| --- | --- |
| High & Low | [Hololive-Dreams-High-low-Auto-Personal](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal) |
| Fishing | [Hololive-Dreams-Fishing-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto) |
| Jump Rope | [Hololive-Dreams-Jump-Rope-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto) |
| Cooking | [Hololive-Dreams-Collect-Cooking-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Collect-Cooking-Auto) |

Version **1.1.2** includes High & Low **1.1.2**, Fishing **1.1.2**, Jump Rope **1.3.2** and Cooking **1.1.1**. Click the version in the lower-left corner to see each program’s version and repository link. The initial window uses the selected standalone program’s default size, scaled for the display DPI. After resizing or maximizing, switching modes preserves the current window size and state.

## Download

Download `Holodori-Auto-v1.1.2-windows.7z` from [Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest), extract it with 7-Zip and run `Holodori-Auto.exe`. Keep the complete folder together. Python and CUDA Toolkit do not need to be installed separately.

Jump Rope and Cooking share TensorRT 10.13, CUDA runtime libraries and DirectML in one package. Compatible NVIDIA GPUs use TensorRT automatically; other supported GPUs use DirectML. Jump Rope requires a compatible GPU; Cooking can also fall back to CPU. Models and device-specific engine caches remain separate.

> **First-use tip:** On compatible NVIDIA RTX 20-series and newer GPUs, the first use of Jump Rope or Cooking compiles a TensorRT engine for your GPU. Allow about **1–2 minutes**, depending on your hardware and system load. Wait for compilation to finish; the engine is cached for subsequent use.

## Usage

1. Open the game and enter the desired minigame.
2. Run Holodori-Auto and select its module from the navigation.
3. Set the shared language and Start/Stop shortcuts, then use the selected module's controls. In Cooking, **Start** automatically loads and warms up the selected model before starting; **Stop** cancels loading.
4. Stop before switching modules. Switching waits for the current module to finish closing, then opens the selected module in the same window.

Only the selected module runs. The common language selector and shortcut fields apply to the current module and carry over when switching modules; duplicate settings rows are hidden inside each page. While capturing a shortcut, the active module's listeners pause until capture finishes.

Shared preferences are saved in `%LOCALAPPDATA%\HolodoriAuto\settings.json`. The first run uses existing High & Low language and shortcut preferences when available; otherwise the defaults are Traditional Chinese, **F8** to start, and **INSERT** to stop. Original statistics, gameplay records, and module-specific options keep their original data locations.

Windows 10/11 x64 and the Windows game client are required. Keep the game visible and follow the selected module's requirements for resolution, capture, and foreground operation. The original READMEs linked above describe its controls and behavior.

## Run from source

Use Windows x64 and Python 3.13. Clone with submodules; GitHub's source ZIP does not include them.

```powershell
git clone --recurse-submodules https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-build.txt
python -m pip install --force-reinstall --no-deps onnxruntime-directml==1.24.4
python tools/fetch_models.py
python main.py
```

Dependencies include the shared TensorRT 10.13 and DirectML runtime; PyTorch is no longer required.

The model command downloads the cooking release's `models.zip` and verifies its pinned size and SHA-256, then verifies every checkpoint before installation. It installs missing models and preserves existing files. If an existing model differs, move it to a backup location before retrying. Cooking automatically loads the selected model when Start is pressed.

To install an archive already downloaded from the cooking release, use `python tools/fetch_models.py --archive C:\path\models.zip`. To verify installed models without network access, use `python tools/fetch_models.py --check`.

## Build

With dependencies and cooking models installed:

```powershell
python tools/build_release.py --output dist/Holodori-Auto
```

Keep the generated portable folder together when distributing or running the program. Dependencies, original resources, and cooking models are included in the build.

## Keep modules current

The original repositories remain independent Git submodules. `upstream-lock.json` records the exact commit and version included for each one. Updating one module does not require copying or merging its game algorithms into Holodori-Auto.

```powershell
python tools/sync_upstreams.py --check
python tools/sync_upstreams.py --module fishing
git add upstream/fishing upstream-lock.json
python tools/sync_upstreams.py --verify
python -m unittest discover -s tests -v
```

Omit `--module fishing` to update all four. Review changes to dependencies, model manifests, and the integration contract before merging. When cooking changes, run the model installer again.

GitHub Actions checks for upstream changes daily and on manual runs, opens an update pull request, and runs integration checks. Updates are reviewed and merged explicitly. See [architecture and maintenance](docs/ARCHITECTURE.md) for the integration contract and build layout.

## Notices

Jump Rope 1.3.2 and its YOLO-derived weights use **AGPL-3.0-only**; Fishing uses **MIT**. Existing MIT notices for components referenced by High & Low and Cooking remain included. NVIDIA libraries, other dependencies and game artwork retain their own terms. See [licensing and corresponding source](LICENSES.md). The Release provides `Holodori-Auto-v1.1.2-source.zip` with all four pinned submodule source trees; GitHub’s automatic source archives omit submodules.
