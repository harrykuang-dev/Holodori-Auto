# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

A Windows program that brings **High & Low**, **Fishing**, **Jump Rope**, and **Cooking** for *hololive Dreams* into one window. The four modules share language and Start/Stop shortcuts while keeping their original game logic, controls, statistics, and diagnostics. Navigation and shared settings follow the same Fluent visual style and use each module's original artwork and accent color.

| Module | Original program |
| --- | --- |
| High & Low | [Hololive-Dreams-High-low-Auto-Personal](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal) |
| Fishing | [Hololive-Dreams-Fishing-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto) |
| Jump Rope | [Hololive-Dreams-Jump-Rope-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto) |
| Cooking | [Hololie-Dreams-Collect-Cooking-Auto](https://github.com/harrykuang-dev/Hololie-Dreams-Collect-Cooking-Auto) |

## Usage

1. Open the game and enter the desired minigame.
2. Run Holodori-Auto and select its module from the navigation.
3. Set the shared language and Start/Stop shortcuts, then use the selected module's controls. Cooking requires **Load model** before **Start**.
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
python tools/fetch_models.py
python main.py
```

Dependencies include the CUDA 12.8 runtime; cooking uses an available NVIDIA GPU automatically and falls back to CPU, preserving its original behavior.

The model command downloads the cooking release's `models.zip` and verifies its pinned size and SHA-256, then verifies every checkpoint before installation. It installs missing models and preserves existing files. If an existing model differs, move it to a backup location before retrying. Model loading remains an explicit action in the cooking interface.

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

Original source, artwork, license files, and third-party notices remain with their respective modules under `upstream/`. See the original repositories for their terms and attribution. Game names and artwork belong to their respective rights holders.
