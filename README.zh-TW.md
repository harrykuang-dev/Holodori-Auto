# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Holodori-Auto 是一款 Windows 自動化程式，支援 *hololive Dreams* 的**比大小（High & Low）**、**釣魚**、**跳繩**、**料理**與**浮台棋**。在導覽列選擇模式，即可使用該模式的操作與統計功能。各模式共用語言設定及開始／停止快捷鍵。

## 下載

從 [Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest) 下載 `Holodori-Auto-v1.3.0-windows.7z`，使用 7-Zip 解壓後執行 `Holodori-Auto.exe`。請保留完整資料夾，無須另外安裝 Python 或 CUDA Toolkit。

標準版內含 DirectML，供跳繩與料理使用。跳繩需要支援 DirectML 或 TensorRT 的 GPU。料理也可回退至 CPU。

相容的 NVIDIA GPU 可使用選用的 TensorRT 元件。在 [Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest) 下載 `Holodori-Auto-v1.3.0-tensorrt.7z`。關閉程式並將壓縮檔解到 `Holodori-Auto.exe` 所在的資料夾。確認 `accelerators/tensorrt/` 位於執行檔旁，再重新啟動程式。首次使用 TensorRT 會為本機 GPU 建立引擎並保留快取。

## 使用方式

1. 開啟遊戲並進入要使用的小遊戲。
2. 啟動 Holodori-Auto，在導覽列選擇對應功能。
3. 設定共用語言與開始／停止快捷鍵，再操作所選功能。料理按下**開始**後會自動載入所選模型並暖機，完成後開始；載入期間可按**停止**取消。
4. 切換功能前先停止執行。切換時會等候目前功能完成關閉，再於同一個視窗開啟所選功能。

同一時間只會執行所選功能。共用語言選單及快捷鍵欄位會套用至目前功能，切換功能後也會沿用；各頁面內重複的設定列會隱藏。擷取新快捷鍵期間，目前功能的快捷鍵監聽會暫停，完成後恢復。

共用偏好設定儲存於 `%LOCALAPPDATA%\HolodoriAuto\settings.json`。首次啟動時，優先沿用既有 High & Low 的語言及快捷鍵；若沒有既有設定，預設為繁體中文、**F8** 開始、**INSERT** 停止。原有統計、遊戲紀錄及各功能專屬選項繼續使用原程式的資料位置。

需要 Windows 10/11 x64 與 Windows 版遊戲。執行期間保持遊戲畫面可見，並遵循所選模式對解析度、擷取與前景操作的要求。

程式啟動時會依所選模式的預設視窗大小與螢幕 DPI 調整顯示。手動調整大小或最大化後，切換模式會保留目前的視窗狀態。點擊左下角版本號會開啟 Holodori-Auto 倉庫。

### 浮台棋

先進入遊戲內「漂漂大亂鬥」的單人頁，再選擇 Holodori-Auto 的**浮台棋**。將**局數上限**設為 1～9999，點擊**開始**，或在遊戲前景按共用開始快捷鍵。局數以已獲勝並完成結算的對局計算。程式會推進可遊玩的 Normal 關卡，遊戲在 Normal 第 30 關後解鎖 Challenge 時會接續遊玩。

**自動補充能量**預設關閉。開啟後，程式可確認遊戲內的一瓶道具補充並繼續。浮台棋會自動辨識四欄三列和四欄四列的棋盤，並在點擊前確認合法落點高亮。三列棋盤的標準八子局面可查詢公開的[動物將棋棋譜庫](https://dobutsu.brianhliou.com/)，查詢內容包含棋子、候補和行棋方的抽象盤面。四列棋盤使用本機搜尋。

## 從原始碼執行

使用 Windows x64 與 Python 3.13。一般 clone 即可取得五個功能的原始碼。

```powershell
git clone https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-build.txt
python -m pip install --force-reinstall --no-deps onnxruntime-directml==1.24.4
python tools/fetch_models.py
python main.py
```

以下步驟使用 DirectML。選用的 TensorRT 元件請參閱[架構與建置說明](document/ARCHITECTURE.md)。

模型安裝命令會下載料理版本附帶的 `models.zip`，核對鎖定版本的檔案大小與 SHA-256，再逐一驗證模型後安裝。只安裝缺少的模型並保留既有檔案；若既有模型內容不同，請先將該檔移至備份位置後重試。料理按下開始後會自動載入所選模型。

已下載料理 Release 模型壓縮包時，可執行 `python tools/fetch_models.py --archive C:\path\models.zip`。只需離線核對已安裝模型時，執行 `python tools/fetch_models.py --check`。

## 建置

安裝依賴與料理模型後執行：

```powershell
python tools/build_release.py --output dist/Holodori-Auto
```

標準 Windows 建置包含各功能資源與料理模型。執行或分發時請保留產生的完整可攜式資料夾。

## 開發與維護

Holodori-Auto 以 `main.py` 為統一入口。五個功能的原始碼皆位於 `components/`，共用導覽、語言、快捷鍵與 Windows 建置。程式一次在獨立程序中執行一個功能。

| 功能 | 技術文件 |
| --- | --- |
| 比大小 | [獎勵 OCR](document/high-low/OCR.md) · [策略](document/high-low/STRATEGY.md) |
| 釣魚 | [辨識與診斷](document/fishing/DEVELOPMENT.md) |
| 跳繩 | [擷取、時序與模型](document/jump-rope/DEVELOPMENT.md) |
| 料理 | [開發與診斷](document/cooking/DEVELOPMENT.md) · [模型推論](document/cooking/INFERENCE.md) |
| 浮台棋 | [棋盤辨識與落子追蹤](document/raft-chess.md) |

[技術文件索引](document/README.md)提供[架構與驗證流程](document/ARCHITECTURE.md)及[開發維護流程](document/UPDATING.md)。GitHub Actions 會測試原始碼並驗證可攜版。

## 聲明與授權

跳繩 1.3.3 與 YOLO 衍生權重採 **AGPL-3.0-only**，釣魚採 **MIT**。比大小與料理引用組件的既有 MIT 聲明繼續保留；NVIDIA 執行庫、其他依賴及遊戲美術維持各自條款。詳見[授權與對應原始碼](LICENSES.md)。[v1.3.0 原始碼壓縮檔](https://github.com/harrykuang-dev/Holodori-Auto/archive/refs/tags/v1.3.0.zip)包含五個功能的原始碼。[來源紀錄](document/SOURCE-ORIGINS.json)保留原始倉庫及提交。
