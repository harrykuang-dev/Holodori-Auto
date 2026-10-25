## English

- Updated High & Low to 1.1.1, Fishing to 1.1.2, Jump Rope to 1.3.0 and Cooking to 1.1.0.
- Jump Rope and Cooking share one TensorRT 10.13 and DirectML runtime. PyTorch is no longer included. Each module keeps its original models, engine cache and fallback behavior.
- Each module opens at its standalone program's default window size, scaled for display DPI.
- Clicking the version in the lower-left corner opens a Fluent dialog with the four program versions and repository links.
- Preserved Jump Rope's stop score when switching modules. Updated the cooking ONNX model installer and bundled model resource paths.

Download `Holodori-Auto-v1.1.0-windows.7z`, extract it with 7-Zip and run `Holodori-Auto.exe`. Keep the complete folder together. Windows 10/11 x64 is required; Jump Rope requires a compatible GPU.

## 繁體中文

- 更新比大小至 1.1.1、釣魚至 1.1.2、跳繩至 1.3.0、料理至 1.1.0。
- 跳繩與料理共用一套 TensorRT 10.13 與 DirectML 執行環境，不再包含 PyTorch。各功能保留原本的模型、引擎快取與回退規則。
- 各模式沿用獨立版的預設視窗大小，並依螢幕 DPI 縮放。
- 點擊左下角版本號，開啟 Fluent 風格彈窗，查看四個程式的版本與倉庫連結。
- 切換模式後保留跳繩停止分數設定，更新料理 ONNX 模型安裝與封裝資源路徑。

下載 `Holodori-Auto-v1.1.0-windows.7z`，使用 7-Zip 解壓後執行 `Holodori-Auto.exe`，並保留完整資料夾。適用於 Windows 10/11 x64；跳繩需要相容 GPU。
