# 開發說明

> Current source / 目前原始碼 [components/jump_rope](../../components/jump_rope/). [Original reference / 原始文件](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto/blob/5af7b2ffea905776902b295642dd3a7cc020d147/docs/DEVELOPMENT.md) describes the historical standalone layout and commands. For the current program, use the [shared build and validation instructions](../ARCHITECTURE.md).

跳繩的程式、控制器與 YOLO 衍生權重沿用 AGPL-3.0-only。原始倉庫保留舊版 MIT 原始碼和人工標註，連結見[授權與對應原始碼](../../LICENSES.md)。本倉庫的 `components/jump_rope/training/` 保留訓練和匯出工具。

## 啟動

從倉庫根目錄執行 `python main.py` 後選擇跳繩。必須點擊開始或按開始快捷鍵才會操作遊戲。滑條中央為預設策略，範圍−40～+40ms，連續調整；負值提早，正值推遲，點0或中央歸零。

停止分數預設「不限」。選擇自訂選鈕後可輸入1–999；達標後僅停止本局跳躍，等待遊戲自然結算，再依目標局數繼續。分數來自HUD數字而非點擊次數，使用小型模板比對、連續兩張可信觀察與分數增量檢查。不確定畫面不推定達標；接近門檻時逐幀核對，其他時間每100ms核對。不限時不建立讀數器、不做額外分數辨識。達標後取消預約並釋放按鍵，保留停止／失焦／擷取異常處理；直到結算都不再執行模型或送出跳躍。

獨立環境需要Windows x64、Python3.13與支援DirectX12／DirectML的硬體顯示卡。共用建置使用 `requirements.txt` 中的 ONNX Runtime DirectML。套件安裝順序見[建置說明](../ARCHITECTURE.md)。TensorRT為選用加速：NVIDIA與CUDA／TensorRT環境可用時優先採用，初始化或暖機失敗時在擷取之前轉用DirectML。沒有可用硬體GPU或DirectML失敗時報錯停止，不使用CPU推論。局內推論錯誤停止，不中途切換。

兩種後端均取消固定畫面年齡上限（frame_validity_ms=null），不加5ms呼叫餘量。控制器以實際 now-stamp 扣減過繩倒數；不重寫stamp，也不把推論完成時間冒充擷取時間。停止、失焦、尺寸改變、畫面被取代、擷取中斷，以及既有過繩時間窗、角色狀態、遮擋預測期限仍有效。處理過慢仍會錯過時機，不保證低性能GPU的成績。

```powershell
python main.py
python main.py --check-jump-model-only --backend directml --report work/jump-directml.json
python main.py --check-jump-model-only --backend gpu --report work/jump-tensorrt.json
```

這些模型預檢只載入及暖機模型，不擷取遊戲畫面或輸入。第二個預檢使用已安裝的選用 TensorRT 環境與相容 NVIDIA GPU。

## 模型與執行

`models/rope.onnx`為FP32可攜模型；`models/rope.fp16.onnx`為已測引擎使用的同一混合精度圖。輸入完整客戶區，單次letterbox至640×640，一個模型識別可見繩框與主角三角。`models/control.json`是數值時序參考，沒有遊戲模型、材質、Shader或影片。

`models/rope.directml.onnx`保留全部204個初始化項目，只將固定輸出頭的整數Mod改成有界、精確的Cast／Div／Floor／Mul／Sub運算。`tools/prepare_directml_model.py`核對原圖雜湊與整數範圍0–16799，`models/directml-graph.json`記錄轉換。沒有重新訓練或更改類別、信心門檻與控制參考。

`detector.py`透過 CUDA Driver API 核對 GPU 名稱、運算能力、驅動 API、TensorRT 10.13、實際模型圖、精度及引擎雜湊。FP16 使用原混合精度圖，FP32 比較使用原 FP32 圖；兩者強型別並關閉 TF32。不讀取舊 11.4 engine；每台機器建立對應快取。首次準備可能需數分鐘，支援進度取消；開始擷取及輸入前才會完成載入。引擎不納入發行包。

`cuda_driver.py`直接管理 primary context、固定頁面 host memory、device memory 與 CUDA stream；沒有 PyTorch、CuPy 或其他訓練框架。原 OpenCV letterbox、RGB 轉換不變，GPU 單一 PTX kernel 將 uint8 HWC 轉成 FP32 NCHW 並乘 1/255；整條非同步串流只在取回結果後同步。模型呼叫有鎖、context push/pop 與明確 close／錯誤清理。NVIDIA 的 nvcuda.dll 由系統驅動提供，不隨程式再分發。TensorRT 延遲載入 builder DLL 時以受控完整路徑預載，避免 AddDllDirectory 與原生 LoadLibrary 搜尋規則不同造成失敗。

`model_runtime.py`預設 TensorRT 10.13 FP16；精度比較工具可建立 FP32 引擎，不增加前端選項。DirectML 繼續使用 ORT_SEQUENTIAL、關閉 memory pattern、禁止模型節點 CPU 回退及 EP 重試。其前後處理與視窗／控制仍在 CPU，模型在硬體 GPU。硬體列舉、GPU 選擇及 DirectML Session 鎖保持不變。

DirectML會話建立時暫時隔離CUDA_VISIBLE_DEVICES並在finally恢復，避免本機NVIDIA在CUDA=-1遮罩下原生崩潰；不改系統環境，亦不影響TensorRT的CUDA可用性判定。

`controller/`處理多形態相位、真實時間差、速度、主角落地和有限遮擋預約。`timing_control.py`只偏移掃地和圓周lead，其他門檻及25ms按壓保持。`jump_rope_bot.py`負責單一擷取、來源畫面編號與操作狀態檢查；`input_pulse.py`及`input_timer.py`負責可中斷放開，按住時繼續觀察。`window_control.py`處理還原最小化、前景等待及選單；`focus_recovery.py`在每批執行期間最多嘗試切回一次，恢復前放開輸入、清除過時預測並重建擷取，開發者模式另記錄失焦視窗與程序及恢復事件；`vision.py`使用DXGI擷取可見客戶區，不枚舉或攔截覆蓋視窗；保持前景、未最小化、螢幕範圍與擷取前後幾何一致性檢查。覆蓋部分仍會出現在擷取像素中。

## 診斷與打包

開發者模式關閉時，不匯入診斷模組或寫入畫面。開啟後，每次開始至結束的所有局數共用一份 `diagnostics.json`（schema 3）及一個 `diagnostics.zip`；JSON 包含系統與顯卡清單、驅動、選卡規則、後端初始化與回退錯誤、模型雜湊、觀察、判斷原因、實際 DOWN/UP、失焦視窗、逐局效能與最終停止原因。初始化未取得畫面也會產生診斷。圖片依局數分資料夾，ZIP 僅包含這份 JSON 與保留的圖片，不包含影片、不自動上傳。

`session_diagnostics.py` 串流追加 JSON；原生輸入回呼只將時間戳放入記憶體佇列，由既有背景診斷工作執行緒寫入。硬體查詢只在初始化進行，CIM 查詢上限8秒，失敗本身也記錄。記錄超量時明確統計省略數量：觀察追蹤上限128MiB原文／約8MiB壓縮資料、其他事件2MiB原文、圖片8MiB；圖片優先保留近期失誤。時間分位數採最近10000筆，總次數與判斷原因覆蓋全程。超過20MiB的ZIP不發布，保留JSON並在介面提示。編碼／寫入失敗會停止輸入並保留資料。

可攜版保留 `_internal/`。標準版使用 DirectML。相容的選用元件位於 EXE 旁的 `accelerators/tensorrt/`，共用載入器驗證元件格式、Python ABI、架構、依賴版本與必要檔案大小，再設定模組及 DLL 搜尋路徑。元件初始化失敗時，跳繩會在開始擷取前嘗試 DirectML。引擎快取在本機建立。

## 介面

頁面使用共用導覽、語言及快捷鍵。程式主視窗的尺寸、切換與版本連結見[架構說明](../ARCHITECTURE.md)。

## 公開資料與模型

原創人工標註採 CC BY 4.0。遊戲截圖保留第三方權利，詳見[資料集聲明](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto/blob/6cd4610b6370fac1b98a17d27562a2d9bb658b3c/annotations/NOTICE.md)。672 筆可訓練、3 筆未確定排除；來源像素產生的三角不稱為人工標註。訓練切分依錄製群組隔離，保存完整遮罩與標籤轉換品質。models/rope.pt 提供來源權重，training/recipe.json、train.py、export_model.py 和 tools/prepare_fp16_model.py 提供訓練與匯出。

## 發布資產

Holodori-Auto 的發行方式見[組件建置與發行配置](../ARCHITECTURE.md)。訓練與匯出使用 [training/ 的獨立環境](../../components/jump_rope/training/)。

原生輸入在呼叫開始前核對來源畫面編號、前景、尺寸與停止狀態；預設沒有固定畫面年齡限制。明確帶有限期的內部決策仍檢查其期限。保存呼叫開始／返回時間，函式返回不代表遊戲實際收到輸入的時刻。25ms放開計時不變。
