# Development guide / 開發說明

> Source reference / 來源參考 [upstream/fishing/docs/DEVELOPMENT.md](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/docs/DEVELOPMENT.md). Paths and standalone commands below refer to that source tree. Holodori-Auto builds and runs from the repository root. See [program architecture](../ARCHITECTURE.md).

[English](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/README.md) · [繁體中文](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/README.zh-TW.md) · [日本語](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/README.ja.md) · [한국어](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/README.ko.md) · [Indonesian](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/README.id.md) · [简体中文](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/README.zh-CN.md)

## Environment / 環境

Windows 10 / 11 x64 and Python 3.13 x64.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe .\gui.py
```

## Single-file build / 單檔建置

```powershell
.\.venv\Scripts\Activate.ps1
.\build.ps1
```

Output: `dist\Hololive-Dreams-Fishing-Auto-v1.1.2.exe`.
The EXE includes the runtime, artwork and high-DPI manifest.
Close the previous build before overwriting it.

## Focused checks / 針對性檢查

Run the checks affected by a change. For documentation links:

```powershell
python -m unittest tests.test_readme -v
```

For the current command-line entry point and packaged icon:

```powershell
python auto_fishing.py --help
python tools/verify_icon.py dist/Hololive-Dreams-Fishing-Auto-v1.1.2.exe
```

## Artwork / 圖像素材

The EXE and Tk windows use `assets/fishing-hook.ico`. The heading uses
`assets/snowsea-angel-thumb.png`. See [ICON.md](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/assets/ICON.md) and
[NOTICE.md](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/assets/NOTICE.md) for asset details and game-artwork rights.

## Offline diagnostics / 離線診斷

```powershell
python tools/replay_recording.py "local-recording.mp4" sessions/replay --hz 10
```

Replay analyzes video without sending game input. Developer mode saves local
screenshots and traces; successful shutdown packages them into a dated ZIP and
removes packed originals only after verification. Normal mode writes no
persistent startup journal.

Do not commit recordings, screenshots, session diagnostics, account information
or credentials. Generated outputs are excluded by `.gitignore`.
