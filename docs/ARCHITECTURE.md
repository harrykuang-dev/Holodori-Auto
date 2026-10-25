# Architecture and maintenance / 架構與維護

## Integration boundary

Holodori-Auto owns navigation, shared language and Start/Stop preferences, process supervision, Windows window embedding, packaging, and upstream synchronization. The original projects own game recognition, input, strategies, model selection, counters, module-specific options, and diagnostics.

```text
Holodori-Auto / main.py
  └─ shared navigation, settings card, and module container
       └─ one active module process
            └─ original Tk interface and game implementation

upstream/
  high_low/    Hololive-Dreams-High-low-Auto-Personal
  fishing/     Hololive-Dreams-Fishing-Auto
  jump_rope/   Hololive-Dreams-Jump-Rope-Auto
  cooking/     Hololive-Dreams-Collect-Cooking-Auto
```

Each project remains an unmodified Git submodule. The adapter contract records its entry module, application class, original artwork, accent color, and settings exposed to the host. The adapter hides each page's duplicate language and shortcut rows and passes common preferences through the original controls; it does not patch game algorithms. Module execution uses a separate process and its original resource directory, preventing collisions between names such as `gui`, `vision`, and `app_locale`. The host embeds the original Tk window as a Windows child window.

Switching closes the active module through its original close handler. The host waits for its process and workers to exit before opening the next module. An unresponsive module remains visible as a closing state; it must not silently allow another automation process to start. Each new module receives the current shared language and shortcuts. Original statistics, gameplay records, and module-specific data stay in their original locations.

Each module session uses a Windows job containing its GUI and descendant processes. If the GUI exits while descendants remain, the host terminates those descendants and verifies that the job has no active processes before switching. Closing the host also waits for session cleanup. The job's kill-on-close flag prevents module processes from outliving a crashed host.

## Shared preferences

The common Fluent settings card controls `language`, `start_key`, and `stop_key`. Values are persisted in `%LOCALAPPDATA%\HolodoriAuto\settings.json` and applied to the current module and future module launches. Initial values come from existing High & Low preferences when available; otherwise they are Traditional Chinese, `F8`, and `INSERT` respectively. This settings file does not replace or migrate original statistics and gameplay records.

Shortcut capture suspends the active module's shortcut listeners until capture finishes. Modifier-only presses are ignored. Windows Tk events use `0x20000` for Alt; `0x8` is a lock-state bit and must not add Alt to a binding. Updating an upstream module requires checking that the adapter still hides its original language/shortcut rows and applies common preferences through the correct control variables and listener APIs.

## Source pins and updates

`.gitmodules` records each original repository and tracked branch. Gitlinks fix the source commit. `upstream-lock.json` records matching commits and display versions, allowing a build to reproduce the same set of modules.

`tools/sync_upstreams.py` fetches upstream changes and updates the selected submodule checkouts plus the lock. It rejects dirty module checkouts and edits to protected integration metadata. It does not copy source files or commit changes.

```powershell
# Fetch and report without changing checkouts or the lock.
python tools/sync_upstreams.py --check

# Update just one module, then review and stage the resulting pins.
python tools/sync_upstreams.py --module jump_rope
git diff --submodule=log
git add upstream/jump_rope upstream-lock.json

# Verify the staged source pins and run the integration tests.
python tools/sync_upstreams.py --verify
python -m unittest discover -s tests -v
```

After an upstream update, check its entry class, close behavior, resource paths, dependencies, native Tk embedding, and shared preference bindings. Game implementation changes normally need only a new gitlink and lock entry. Changes to the entry, lifecycle, or settings contract require adapting the host and its contract tests.

The scheduled workflow checks daily and also supports manual dispatch. It creates an update pull request and runs checks; merging remains explicit. The repository must allow GitHub Actions to create pull requests. Builds continue to use the reviewed pins until an update is merged.

## Cooking checkpoints

The cooking Git submodule contains `models-manifest.json`, which is the authority for the exact archive and checkpoint sizes and SHA-256 hashes. `tools/fetch_models.py` reads `VERSION` from the pinned `gui.py` using Python's AST without importing the module, then downloads `models.zip` from the corresponding release in the original cooking repository.

The installer verifies the complete archive fingerprint, requires archive entries to match the manifest exactly, rejects unsafe paths and symbolic links, and verifies every checkpoint in staging before publishing any model. Only missing models are installed. Existing files must already match the manifest and are never overwritten; installation failures roll back files added by that attempt. Staging uses the cooking directory so completed files can be published with filesystem hard links.

```powershell
python tools/fetch_models.py
python tools/fetch_models.py --archive C:\path\models.zip
python tools/fetch_models.py --check
```

`--check` verifies installed checkpoints offline. None of these commands imports the inference runtime, opens the game, or sends input. If an upstream release changes its version convention or model asset name, update the release URL resolver alongside that pin. Existing mismatching checkpoints must be moved to a backup location before installing the new manifest's versions.

## Packaging

Use Windows x64, Python 3.13, `requirements.txt`, and `requirements-build.txt`. Install verified cooking models before invoking `python tools/build_release.py --output dist/Holodori-Auto`.

The portable build includes the host, original module resources, shared dependencies, and model files. Preserve module license files and third-party notices. Source checkouts continue to run each original program independently.

Version 1.1.0 uses a single shared TensorRT 10.13.3.9 package, CUDA runtime 12.9.79 and ONNX Runtime DirectML 1.24.4 under `_internal`. Neither module includes a private accelerator copy, and PyTorch is excluded. Jump Rope retains its FP16/DirectML graphs and GPU-specific engine cache; Cooking retains its FP32 models and separate engine cache. The adapter redirects Cooking's standalone frozen model lookup to `upstream/cooking/models/inference`, preserving the shared `_MEIPASS` import root. Keep each original fallback policy: Jump Rope requires TensorRT or a hardware DirectML GPU; Cooking may fall back to CPU.

`ddddocr` declares the CPU `onnxruntime` distribution as a dependency. After dependency installation, reinstall `onnxruntime-directml==1.24.4` with `--force-reinstall --no-deps` to select the shared DirectML implementation. The builder refuses an environment without `DmlExecutionProvider`.

During embedded construction, the adapter records the original DPI-scaled window size and minimum size, then the host applies them once when that module becomes ready. It does not hard-code a second size table or reset a user's resize on each status update. The version footer opens a Fluent card dialog populated from `upstream-lock.json`, with the host and four original repository links.

The host remains withdrawn until the initial module's size is applied, so no temporary large window is shown. The adapter normalizes outer page padding, compensates for a visible page scrollbar, and reports the actual card gap. The host uses that gap below the shared settings card to keep the page aligned across languages and resizing.

Use `python main.py --check-jump-model-only --backend gpu --report work/jump-gpu.json` to load and warm the original jump detector with synthetic pixels. `--backend directml` checks DirectML separately. Cooking's equivalent is `python tools/check_models_runtime.py`. Both also support the packaged executable; no game capture or input is performed.

## 繁體中文

Holodori-Auto 負責共用導覽、語言及開始／停止快捷鍵、程序管理、Windows 視窗嵌入、建置與上游同步；辨識、輸入、策略、模型選擇、計數、專屬選項與診斷由原始功能負責。四個功能均以未修改的 Git 子模組保留；整合適配層隱藏各頁面重複的語言與快捷鍵列，透過原始控制介面套用共用設定，不修改遊戲演算法。

同一時間只啟動一個功能程序，並將原本的 Tk 介面嵌入主視窗。切換時呼叫目前功能的原始關閉流程，等候程序與工作結束後才啟動下一個功能。共用語言及快捷鍵會沿用至下一個功能；原有統計、遊戲紀錄及專屬資料繼續使用原本位置。

共用 Fluent 設定卡的 `language`、`start_key`、`stop_key` 儲存於 `%LOCALAPPDATA%\HolodoriAuto\settings.json`。首次使用時，優先讀取既有 High & Low 偏好設定，否則使用繁體中文、`F8` 開始、`INSERT` 停止。擷取新快捷鍵時暫停目前功能的監聽，完成後恢復；單獨按修飾鍵不會建立綁定。Windows Tk 事件的 Alt 位元是 `0x20000`，Num Lock 的 `0x8` 不得被當作 Alt。上游更新後需一併檢查設定列隱藏、控制變數與監聽介面的適配關係。

每次功能執行使用獨立的 Windows Job 管理介面與其子程序。若介面意外結束但子程序仍存活，主程式會終止殘留程序，確認全部結束後才允許切換；關閉主程式時也會等候清理完成。主程式異常退出時，Job 的關閉終止設定會清除所屬功能程序。

Git 子模組提交與 `upstream-lock.json` 共同鎖定整合版本。執行 `tools/sync_upstreams.py --module 功能名稱` 可只跟進一個功能；省略 `--module` 則更新全部。檢查變更並暫存新的子模組與鎖定檔後，以 `--verify` 核對一致性，再執行測試。若上游只修改遊戲實作，通常只需更新提交；若啟動類別、關閉流程或資源路徑改變，則需調整整合介面。

每日及手動工作流程會建立更新 Pull Request 並執行檢查，不自動合併。倉庫需開啟允許 GitHub Actions 建立 Pull Request 的設定。

料理模型以鎖定來源中的 `models-manifest.json` 為準。安裝程式從原始料理倉庫對應版本下載模型，核對壓縮包與每個模型的大小、SHA-256 及允許路徑，全部驗證後才安裝缺少的檔案。既有檔案不會被覆寫，安裝失敗時回復本次新增的模型。`--check` 可離線驗證，不載入推論程式或操作遊戲。

Windows 建置需先安裝依賴與通過驗證的料理模型，再執行 `python tools/build_release.py --output dist/Holodori-Auto`。分發時保留完整可攜式資料夾、各功能資源、授權檔與第三方聲明。

1.1.0 的跳繩與料理共用 `_internal` 中同一套 TensorRT 10.13.3.9、CUDA 執行庫 12.9.79 與 ONNX Runtime DirectML 1.24.4，不包含獨立加速器副本或 PyTorch。各功能維持原本的模型、快取與回退規則：跳繩需要 TensorRT 或硬體 DirectML GPU；料理可回退至 CPU。整合層僅重新指定料理封裝版的模型資料夾，不改動共用 `_MEIPASS` 或原始演算法。

`ddddocr` 依賴 CPU 版 `onnxruntime`，因此安裝依賴後需以 `--force-reinstall --no-deps` 重新安裝 `onnxruntime-directml==1.24.4`。建置前會檢查 DirectML 提供者，避免依賴安裝順序覆蓋 GPU 執行環境。

嵌入時記錄原始程式依 DPI 計算的預設及最小視窗尺寸，功能就緒後由主視窗套用一次；後續狀態更新不會覆寫使用者調整的大小。版本彈窗沿用 Fluent 卡片樣式，從 `upstream-lock.json` 顯示四個程式版本與倉庫連結。

主視窗在首個功能尺寸套用後才顯示，避免啟動時先大後小。整合層統一頁面外邊距並補償捲軸寬度，將實際卡片間距回傳給主視窗，作為共用設定框下方的間距；切換語言與調整視窗大小後仍保持對齊。
