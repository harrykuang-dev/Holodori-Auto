# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Holodori-Auto is a Windows program that automates **High & Low**, **Fishing**, **Jump Rope**, **Cooking**, and **Raft Chess** in *hololive Dreams*. Select a mode in the navigation to use its controls and statistics. All modes share the same language setting and Start/Stop shortcuts.

## Download

Download `Holodori-Auto-v1.2.10-windows.7z` from [Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest), extract it with 7-Zip and run `Holodori-Auto.exe`. Keep the complete folder together. Python and CUDA Toolkit do not need to be installed separately.

Jump Rope and Cooking share TensorRT 10.13, CUDA runtime libraries and DirectML in one package. Compatible NVIDIA GPUs use TensorRT automatically; other supported GPUs use DirectML. Jump Rope requires a compatible GPU; Cooking can also fall back to CPU. Models and device-specific engine caches remain separate.

> **First-use tip:** On compatible NVIDIA RTX 20-series and newer GPUs, the first use of Jump Rope or Cooking compiles a TensorRT engine for your GPU. Allow about **1–2 minutes**, depending on your hardware and system load. Wait for compilation to finish; the engine is cached for subsequent use.

## Usage

1. Open the game and enter the desired minigame.
2. Run Holodori-Auto and select the matching mode from the navigation.
3. Set the shared language and Start/Stop shortcuts, then use the selected mode's controls. In Cooking, **Start** automatically loads and warms up the selected model before starting; **Stop** cancels loading.
4. Stop before switching modes. Switching waits for the current mode to finish closing, then opens the selected mode in the same window.

Only the selected mode runs. The common language selector and shortcut fields apply to the current mode and carry over when switching modes; duplicate settings rows are hidden inside each page. While capturing a shortcut, the active mode's listeners pause until capture finishes.

Shared preferences are saved in `%LOCALAPPDATA%\HolodoriAuto\settings.json`. The first run uses existing High & Low language and shortcut preferences when available; otherwise the defaults are Traditional Chinese, **F8** to start, and **INSERT** to stop. Original statistics, gameplay records, and mode-specific options keep their original data locations.

Windows 10/11 x64 and the Windows game client are required. Keep the game visible and follow the selected mode’s requirements for resolution, capture, and foreground operation.

The window opens at the selected mode’s default size, scaled for your display. Switching modes preserves any resizing or maximized state. Click the version in the lower-left corner to open the Holodori-Auto repository.

### Raft Chess

Enter the solo screen of Puka Puka Fight, then choose **Raft Chess** in Holodori-Auto. Set **Match limit** to 1–9999 and click **Start** or use the shared Start shortcut while the game is in the foreground. The limit counts completed wins. The program advances through available Normal stages and continues in Challenge once the game unlocks it after Normal 30.

**Automatically refill energy** is off by default. When enabled, the program can confirm the game's one-item refill and continue. Raft Chess checks the foreground 16:9 client and confirms board state and legal destination highlights before clicking. Standard eight-piece positions can use the public [Animal Shogi tablebase](https://dobutsu.brianhliou.com/) with the abstract board, reserves and side to move.

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

## Development and maintenance

Holodori-Auto has one entry point, `main.py`. Its five features share navigation, language, shortcuts and a portable Windows build. Gameplay and feature-specific diagnostics are organized by feature.

| Feature | Technical reference |
| --- | --- |
| High & Low | [OCR](document/high-low/OCR.md) · [Strategy](document/high-low/STRATEGY.md) |
| Fishing | [Recognition and diagnostics](document/fishing/DEVELOPMENT.md) |
| Jump Rope | [Capture, timing and model runtime](document/jump-rope/DEVELOPMENT.md) |
| Cooking | [Development and diagnostics](document/cooking/DEVELOPMENT.md) · [Inference](document/cooking/INFERENCE.md) |
| Raft Chess | [Board recognition and move tracking](document/raft-chess.md) |

Start with the [technical documentation](document/README.md) for the [architecture and validation commands](document/ARCHITECTURE.md) and [pinned source maintenance](document/UPDATING.md). GitHub Actions checks the source pins, runs the tests and verifies the portable build.

## Notices

Jump Rope 1.3.3 and its YOLO-derived weights use **AGPL-3.0-only**; Fishing uses **MIT**. Existing MIT notices for components referenced by High & Low and Cooking remain included. NVIDIA libraries, other dependencies and game artwork retain their own terms. See [licensing and corresponding source](LICENSES.md). The Release provides `Holodori-Auto-v1.2.10-source.zip` with all four pinned submodule source trees; GitHub’s automatic source archives omit submodules.
