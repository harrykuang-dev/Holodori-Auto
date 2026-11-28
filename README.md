# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md)

Holodori-Auto is a Windows automation program for *hololive Dreams* that uses visual recognition of the game screen. It supports **High & Low**, **Fishing**, **Hoppin' Rope**, **Collect Cooking**, and **Puka Puka Fight**.
All five features share the language setting and Start/Stop shortcuts.

## Download and use

Use Windows 10 or 11 (x64) with the Windows game client. **Only 16:9 game windows are supported.** Keep the game window visible.

1. Download `Holodori-Auto-v1.3.1-windows.7z` from [Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest), extract it with 7-Zip, and run `Holodori-Auto.exe` from the extracted folder.
2. Enter the minigame in *hololive Dreams*. Select the matching feature in Holodori-Auto and click **Start** or press the shared Start shortcut. Click **Stop** before switching features.

The standard package includes DirectML. **Hoppin' Rope** requires a GPU that supports DirectML or TensorRT. **Collect Cooking** can fall back to the CPU. On a compatible NVIDIA GPU, you can install the optional [Holodori-Auto-v1.3.1-tensorrt.7z](https://github.com/harrykuang-dev/Holodori-Auto/releases/download/v1.3.1/Holodori-Auto-v1.3.1-tensorrt.7z) from Releases. Close the program, extract the add-on so `accelerators/tensorrt/` sits beside `Holodori-Auto.exe`, then reopen the program. The first TensorRT run builds a GPU-specific engine for later reuse.

## Run and build from source

Use Windows x64 and Python 3.13. The model download command verifies the pinned **Collect Cooking** models before installing them.

```powershell
git clone https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
py -3.13 -m venv .venv
$python = ".\.venv\Scripts\python.exe"
& $python -m pip install -r requirements.txt -r requirements-build.txt
& $python -m pip install --force-reinstall --no-deps onnxruntime-directml==1.24.4
& $python tools/fetch_models.py
& $python main.py
```

To build and verify the DirectML portable package, run the following from the same checkout. Choose a fresh output directory for each build.

```powershell
& $python tools/build_release.py --output dist/Holodori-Auto
& $python tools/verify_bundle.py dist/Holodori-Auto/Holodori-Auto.exe --report work/packaged-contents.json
```

## Development and maintenance

All five features live in `components/`. The shared window, language, and shortcuts are maintained in `holodori/`. Each feature runs in its own process. GitHub Actions checks the source and the Windows portable build.

[Technical documentation](document/README.md) · [Build and validation](document/ARCHITECTURE.md) · [Maintenance workflow](document/UPDATING.md) · [In-game terminology](document/GAME-TERMS.md)

## Notices and licenses

Holodori-Auto is an independent project. Game names, screenshots, and artwork belong to their respective rights holders.

Original Holodori-Auto code and documentation use the [MIT License](LICENSE). The **Hoppin' Rope** implementation and its YOLO-derived weights retain [AGPL-3.0-only](components/jump_rope/LICENSE). Third-party materials follow their respective terms. See [licensing and corresponding source](LICENSES.md) and [third-party notices](THIRD_PARTY_NOTICES.md).
