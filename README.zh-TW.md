# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md)

Holodori-Auto 是 *hololive Dreams* 的 Windows 自動化程式，支援**比大小**、**釣魚**、**蹦蹦大跳繩**、**食材妙廚房**與**漂漂大亂鬥**。
五個功能共用語言設定及開始與停止快捷鍵。

## 下載與使用

使用 Windows 10 或 11（x64）及 Windows 遊戲客戶端。**僅支援 16:9 的遊戲視窗。** 請保持遊戲視窗可見。

1. 從[發行頁面](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest)下載 `Holodori-Auto-v1.3.1-windows.7z`，使用 7-Zip 解壓縮，再從解壓縮的資料夾執行 `Holodori-Auto.exe`。
2. 進入 *hololive Dreams* 的小遊戲，選擇 Holodori-Auto 中對應的功能，點擊**開始**或按共用開始快捷鍵。切換功能前先點擊**停止**。

標準版內建 DirectML。**蹦蹦大跳繩**需要支援 DirectML 或 TensorRT 的 GPU，**食材妙廚房**可回退至 CPU。相容的 NVIDIA 顯示卡可從發行頁面下載選用的 `Holodori-Auto-v1.3.1-tensorrt.7z`。先關閉程式，解壓縮後將 `accelerators/tensorrt/` 放在 `Holodori-Auto.exe` 旁，再重新啟動。首次使用 TensorRT 會為該 GPU 建立引擎，供後續使用。

## 從原始碼執行與建置

使用 Windows x64 與 Python 3.13。模型下載指令會驗證固定版本的**食材妙廚房**模型，再進行安裝。

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

在同一份原始碼中執行下列指令，即可建置並驗證 DirectML 可攜版。每次建置請選用新的輸出目錄。

```powershell
& $python tools/build_release.py --output dist/Holodori-Auto
& $python tools/verify_bundle.py dist/Holodori-Auto/Holodori-Auto.exe --report work/packaged-contents.json
```

## 開發與維護

五個功能都在 `components/` 維護。共用視窗、語言和快捷鍵由 `holodori/` 維護，各功能以獨立程序執行。GitHub Actions 驗證原始碼與 Windows 可攜版。

[技術文件](document/README.md) · [建置與驗證](document/ARCHITECTURE.md) · [維護流程](document/UPDATING.md) · [遊戲用詞](document/GAME-TERMS.md)

## 聲明與授權

Holodori-Auto 是獨立專案。遊戲名稱、截圖和美術由各權利人保有。

Holodori-Auto 原創程式碼和文件採用 [MIT 授權](LICENSE)。**蹦蹦大跳繩**的實作與 YOLO 衍生權重沿用 [AGPL-3.0-only](components/jump_rope/LICENSE)。第三方內容依各自的條款使用。詳見[授權與對應原始碼](LICENSES.md)和[第三方聲明](THIRD_PARTY_NOTICES.md)。
