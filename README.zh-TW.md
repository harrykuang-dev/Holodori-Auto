# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

將 *hololive Dreams* 的 **High & Low**、**釣魚**、**跳繩**與**料理**整合至同一個視窗的 Windows 程式。四個功能共用語言與開始／停止快捷鍵，並保留原本的遊戲邏輯、操作介面、統計與診斷功能。導覽及共用設定沿用相同的 Fluent 美術風格，並使用各功能原有的圖示與主題色。

| 功能 | 原始程式 |
| --- | --- |
| High & Low | [Hololive-Dreams-High-low-Auto-Personal](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal) |
| 釣魚 | [Hololive-Dreams-Fishing-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto) |
| 跳繩 | [Hololive-Dreams-Jump-Rope-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto) |
| 料理 | [Hololie-Dreams-Collect-Cooking-Auto](https://github.com/harrykuang-dev/Hololie-Dreams-Collect-Cooking-Auto) |

## 下載

從 [v1.0.0](https://github.com/harrykuang-dev/Holodori-Auto/releases/tag/v1.0.0) 下載全部三個 `Holodori-Auto-v1.0.0-windows-1of3.zip`、`Holodori-Auto-v1.0.0-windows-2of3.zip` 與 `Holodori-Auto-v1.0.0-windows-3of3.zip` 壓縮檔。將三個檔案解壓至同一個位置，使內容合併為一個 `Holodori-Auto` 資料夾，再執行其中的 `Holodori-Auto.exe`。請保留完整資料夾。套件已包含依賴與料理模型，無須另行安裝 Python。`SHA256SUMS.txt` 提供壓縮檔校驗碼。

## 使用方式

1. 開啟遊戲並進入要使用的小遊戲。
2. 啟動 Holodori-Auto，在導覽列選擇對應功能。
3. 設定共用語言與開始／停止快捷鍵，再操作所選功能。料理需先按下**載入模型**，再按下**開始**。
4. 切換功能前先停止執行。切換時會等候目前功能完成關閉，再於同一個視窗開啟所選功能。

同一時間只會執行所選功能。共用語言選單及快捷鍵欄位會套用至目前功能，切換功能後也會沿用；各頁面內重複的設定列會隱藏。擷取新快捷鍵期間，目前功能的快捷鍵監聽會暫停，完成後恢復。

共用偏好設定儲存於 `%LOCALAPPDATA%\HolodoriAuto\settings.json`。首次啟動時，優先沿用既有 High & Low 的語言及快捷鍵；若沒有既有設定，預設為繁體中文、**F8** 開始、**INSERT** 停止。原有統計、遊戲紀錄及各功能專屬選項繼續使用原程式的資料位置。

需要 Windows 10/11 x64 與 Windows 版遊戲。執行期間保持遊戲可見，並遵循所選功能對解析度、擷取與前景操作的要求。各功能的完整操作與行為說明請見上方原始倉庫的 README。

## 從原始碼執行

使用 Windows x64 與 Python 3.13。複製倉庫時需一併取得子模組；GitHub 的原始碼 ZIP 不包含子模組內容。

```powershell
git clone --recurse-submodules https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-build.txt
python tools/fetch_models.py
python main.py
```

依賴包含 CUDA 12.8 執行環境；料理會自動使用可用的 NVIDIA GPU，否則使用 CPU，沿用原本的運作方式。

模型安裝命令會下載料理版本附帶的 `models.zip`，核對鎖定版本的檔案大小與 SHA-256，再逐一驗證模型後安裝。只安裝缺少的模型並保留既有檔案；若既有模型內容不同，請先將該檔移至備份位置後重試。料理介面仍需手動載入模型。

已下載料理 Release 模型壓縮包時，可執行 `python tools/fetch_models.py --archive C:\path\models.zip`。只需離線核對已安裝模型時，執行 `python tools/fetch_models.py --check`。

## 建置

安裝依賴與料理模型後執行：

```powershell
python tools/build_release.py --output dist/Holodori-Auto
```

執行與分發時請保留產生的完整可攜式資料夾。建置內容包含依賴、原始資源與料理模型。

## 跟進各功能更新

四個原始倉庫以獨立 Git 子模組保留，`upstream-lock.json` 記錄整合版本所使用的各功能提交與版本。更新單一功能時，無須將遊戲演算法複製或合併至 Holodori-Auto。

```powershell
python tools/sync_upstreams.py --check
python tools/sync_upstreams.py --module fishing
git add upstream/fishing upstream-lock.json
python tools/sync_upstreams.py --verify
python -m unittest discover -s tests -v
```

省略 `--module fishing` 可更新全部四個功能。合併前應檢查依賴、模型清單與整合介面的變更；料理更新後請重新執行模型安裝命令。

GitHub Actions 每日及手動執行時檢查上游更新，建立更新 Pull Request 並執行整合檢查。更新需經檢查後手動合併。整合介面與建置結構請見[架構與維護說明](docs/ARCHITECTURE.md)。

## 聲明與授權

原始碼、美術資源、授權檔與第三方聲明保留於 `upstream/` 對應功能中，各自條款與出處請見原始倉庫。遊戲名稱及美術資源屬於各權利人。
