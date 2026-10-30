## English

- Updated Jump Rope to **1.3.2**, including the revised YOLO26n rope-detection model with late-game rope annotations.
- Limited Jump Rope focus recovery to one attempt per batch.
- Consolidated Jump Rope developer diagnostics into one JSON per run, including GPU and driver details, initialization errors, performance and input records. The diagnostic ZIP includes the JSON and retained images.
- Updated component versions in the version dialog, all six README languages and licensing notices. High & Low remains **1.1.2**, Fishing **1.1.2** and Cooking **1.1.1**.

Download `Holodori-Auto-v1.1.2-windows.7z`, extract it with 7-Zip, and run `Holodori-Auto.exe`. Keep the complete folder together. Existing settings and records are preserved.

Jump Rope and Cooking share TensorRT and DirectML. Updated Jump Rope weights require a matching local TensorRT engine; the first load may take longer while it is compiled.

`Holodori-Auto-v1.1.2-source.zip` includes the integration code and all four pinned submodule source trees. GitHub's automatically generated source archives do not include submodules. See [licensing and corresponding source](https://github.com/harrykuang-dev/Holodori-Auto/blob/v1.1.2/LICENSES.md).

## 繁體中文

- 更新跳繩至 **1.3.2**，同步加入後段繩子標註的新版 YOLO26n 繩子辨識模型。
- 跳繩每批最多嘗試恢復遊戲焦點一次。
- 跳繩開發者診斷整合為每次執行一份 JSON，包含顯卡與驅動、初始化錯誤、效能及輸入記錄。診斷 ZIP 包含該份 JSON 與保留的圖片。
- 同步更新版本彈窗、六語 README 與授權說明中的組件版本。比大小維持 **1.1.2**、釣魚 **1.1.2**、料理 **1.1.1**。

下載 `Holodori-Auto-v1.1.2-windows.7z`，使用 7-Zip 解壓後執行 `Holodori-Auto.exe`，並保留完整資料夾。既有設定與記錄會保留。

跳繩與料理共用 TensorRT 和 DirectML。新版跳繩權重需要對應的本機 TensorRT 引擎，首次載入時需重新編譯，可能需要較長時間。

`Holodori-Auto-v1.1.2-source.zip` 包含整合碼與四個鎖定子模組來源。GitHub 自動產生的原始碼壓縮包不含子模組。詳見[授權與對應原始碼](https://github.com/harrykuang-dev/Holodori-Auto/blob/v1.1.2/LICENSES.md)。
