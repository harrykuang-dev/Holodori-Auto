# Development guide / 開發說明

> Current source / 目前原始碼 [components/fishing](../../components/fishing/). [Original reference / 原始文件](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/docs/DEVELOPMENT.md) describes the historical standalone layout and commands. For the current program, use the [shared build and validation instructions](../ARCHITECTURE.md).

[English](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/README.md) · [繁體中文](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/README.zh-TW.md) · [日本語](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/README.ja.md) · [한국어](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/README.ko.md) · [Indonesian](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/README.id.md) · [简体中文](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/README.zh-CN.md)

## Source and validation / 原始碼與驗證

Use the [shared source setup](../../README.md) and run `python main.py` from the repository root. Select Fishing to validate the embedded interface. The [root validation workflow](../ARCHITECTURE.md) checks all five tabs and the standard Windows package.

## Artwork / 圖像素材

The feature artwork is in `components/fishing/assets/`. See [ICON.md](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/assets/ICON.md) and
[NOTICE.md](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto/blob/dbc1aee9227d5d7bfecfa542cf424ffaa4a0a2ab/assets/NOTICE.md) for asset details and game-artwork rights.

## Offline diagnostics / 離線診斷

```powershell
python components/fishing/tools/replay_recording.py "local-recording.mp4" sessions/replay --hz 10
```

Replay analyzes video without sending game input. Developer mode saves local
screenshots and traces; successful shutdown packages them into a dated ZIP and
removes packed originals only after verification. Normal mode writes no
persistent startup journal.

Do not commit recordings, screenshots, session diagnostics, account information
or credentials. Generated outputs are excluded by `.gitignore`.
