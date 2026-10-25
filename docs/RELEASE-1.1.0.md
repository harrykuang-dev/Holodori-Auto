## English

- Updated High & Low to **1.1.1**, Fishing to **1.1.2**, Jump Rope to **1.3.0**, and Cooking to **1.1.0**.
- Jump Rope and Cooking share one TensorRT 10.13 and DirectML runtime. PyTorch is no longer included; each module retains its own models, engine cache, and fallback behavior.
- Matched each module’s default window size to its standalone program, with DPI scaling. Fixed the window resizing visibly during startup.
- Aligned module cards with the shared settings card and matched the spacing between them.
- Clicking the version in the lower-left corner opens a Fluent dialog showing each program’s version and repository link.
- Preserved Jump Rope’s stop score when switching modules and corrected Cooking’s bundled model paths.
- Updated licensing notices for Jump Rope’s **AGPL-3.0-only** program and YOLO-derived weights. Existing MIT notices and NVIDIA dependency terms remain included.

Download `Holodori-Auto-v1.1.0-windows.7z`, extract it with 7-Zip, and run `Holodori-Auto.exe`. Keep the complete folder together.

Windows 10/11 x64 is required. Jump Rope requires a compatible GPU. The first TensorRT load may take longer while building the engine cache.

`Holodori-Auto-v1.1.0-source.zip` includes the integration code and all four pinned submodule source trees. GitHub’s automatically generated source archives do not include submodules. See [licensing and corresponding source](https://github.com/harrykuang-dev/Holodori-Auto/blob/v1.1.0/LICENSES.md).

## 繁體中文

- 更新比大小至 **1.1.1**、釣魚至 **1.1.2**、跳繩至 **1.3.0**、料理至 **1.1.0**。
- 跳繩與料理共用一套 TensorRT 10.13 與 DirectML 執行環境，不再包含 PyTorch；各功能保留獨立模型、引擎快取與原有回退規則。
- 各模式沿用獨立版的預設視窗大小，並依螢幕 DPI 縮放；修正啟動時視窗先大後小的問題。
- 各模式的內容卡片與共用設定框左右對齊，上下卡片間距保持一致。
- 點擊左下角版本號，可開啟 Fluent 風格彈窗，查看各程式版本與倉庫連結。
- 切換模式後保留跳繩停止分數設定，修正料理封裝版的模型路徑。
- 更新跳繩程式與 YOLO 衍生權重的 **AGPL-3.0-only** 聲明，保留既有 MIT 聲明與 NVIDIA 依賴條款。

下載 `Holodori-Auto-v1.1.0-windows.7z`，使用 7-Zip 解壓後執行 `Holodori-Auto.exe`，並保留完整資料夾。

適用於 Windows 10/11 x64。跳繩需要相容 GPU；首次使用 TensorRT 時需建立引擎快取，載入時間較長。

`Holodori-Auto-v1.1.0-source.zip` 包含整合碼與四個鎖定子模組來源。GitHub 自動產生的原始碼壓縮包不含子模組。詳見[授權與對應原始碼](https://github.com/harrykuang-dev/Holodori-Auto/blob/v1.1.0/LICENSES.md)。
