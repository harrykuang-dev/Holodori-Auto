# 開發說明

> Current source / 目前原始碼 [components/cooking](../../components/cooking/). [Original reference / 原始文件](https://github.com/harrykuang-dev/Hololive-Dreams-Collect-Cooking-Auto/blob/90c09a242fe335284588d895482a25efe17c3ba6/docs/DEVELOPMENT.md) describes the historical standalone layout and commands. For the current program, use the [shared build and validation instructions](../ARCHITECTURE.md).

Holodori-Auto 標準版包含 DirectML 與 CPU 備援。TensorRT 以選用元件提供。模型格式、FP32 精度、快取與自動切換機制見[模型推論說明](INFERENCE.md)。

## 環境、模型與預檢

依[原始碼安裝說明](../../README.md)準備 Windows x64 與 Python 3.13。在倉庫根目錄執行：

```powershell
python tools/fetch_models.py
python tools/check_models_runtime.py
python main.py
```

安裝工具按 [manifest](../../components/cooking/models-manifest.json) 檢查壓縮包與模型。模型預檢會載入並暖機標準、進階兩個模型，並回報實際後端。封裝後傳入 `--executable dist/Holodori-Auto/Holodori-Auto.exe` 可驗證可攜版。預檢不擷取或操作遊戲。

## 診斷格式

GUI開發者模式在正常停止或例外結束後產生ZIP，每個ZIP硬上限20,000,000位元組（包含ZIP檔頭、索引及中繼資料）。事件、決策及逐局結果完整保留；結算圖與一般截圖共同按容量淘汰較早圖片。純文字超限時分成多個獨立ZIP，全部解壓到同一資料夾；若出現 `NAME.parts/000001` 等檔案，按編號順序以原始位元組串接以重建NAME，分段可能切開UTF-8字元或JSON行。完整JSONL原檔始終保留在本機。內容包含：

- `diagnostic.json`：版本、模型、環境、動作與等待原因統計、各食材累計分析耗時及刪減計數。
- `trace.jsonl`：完整辨識、規劃與耗時紀錄，以 `stream` 區分每局來源。
- `inputs.jsonl`：完整輸入、補點及過場紀錄，以 `stream` 區分每局來源。
- `round-results.jsonl`：每局實際分數、完成料理數、確認狀態、執行時間、實際後端、點擊數、等待原因及耗時摘要。無法確認數字時保存null及原因，不用內部估計或歷史最佳分數代替。
- `image-index.json`：原畫面參照、JPEG路徑、原尺寸與儲存尺寸。
- `round-screenshots/`：逐局結算截圖，立即寫入磁碟，與一般截圖共用100張／10 MB容量限制，較早圖片先淘汰。逐局文字中的圖片路徑是原始參照，可能指向已淘汰的圖片；現存圖片以 `image-index.json` 為準。
- `screenshots/`：近期採樣畫面及失敗追蹤畫面，與結算圖共用容量限制。
- `metadata/`：逐局摘要、執行檔案與模型指紋、擷取效能摘要。
- `launcher-tail.txt`：近期啟動紀錄。

截圖最長邊1536像素，以JPEG壓縮。一般畫面最多每2秒保留一張；超出張數、記憶體或ZIP預算時先淘汰較早截圖。詳細內容以 `outputs/kitchen-bot/diagnostic_store.py` 的容量設定為準。診斷包不包含完整影片、權重、原始碼副本或設定檔；Windows帳號路徑會替換為匿名參照。

一般模式不保存詳細截圖或辨識紀錄，結束後移除該次暫存資料。開發者模式的JSONL每筆寫入磁碟，打包後仍保留原檔；結算圖獨立寫入磁碟，容量淘汰時也會移除對應原檔。強制結束時，已寫入資料仍可讀取；尚在記憶體的一般截圖不保證保留。程式不會自動清除此模式的歷史明細。

開發用直接CLI保留完整記錄入口：

```powershell
python components/cooking/outputs/kitchen-bot/standalone.py --point-model components/cooking/models/inference/point-classifier-resnet18.onnx --games 5
```

此入口預設保存原生尺寸錄影及完整逐幀資料，容量需求與GUI診斷包不同。
