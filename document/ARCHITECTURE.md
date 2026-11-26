# Architecture and validation / 架構與驗證

## Program structure

Holodori-Auto is a Windows program with five features. `main.py` starts the shared window and dispatches feature processes. `holodori/` owns navigation, language, shortcuts, Windows process supervision and the shared UI. The game recognition, models, controls and diagnostics are in `components/`.

```text
main.py
holodori/               shared settings, window and process management
components/high_low/    High & Low
components/fishing/     Fishing
components/jump_rope/   Jump Rope
components/cooking/     Cooking
components/puka_puka/   Raft Chess
```

The program runs one feature at a time and embeds its Tk window as a Windows child window. During a switch it waits for the active feature to close and for its Windows Job to become empty before starting the next feature. The job's kill-on-close flag ends any remaining feature processes if the main program exits unexpectedly. This boundary also isolates libraries with the same Python module name and releases capture, input and GPU resources when leaving a feature.

The shared preferences file at `%LOCALAPPDATA%\HolodoriAuto\settings.json` stores `language`, `start_key` and `stop_key`. The first launch can adopt existing High & Low preferences. Defaults are Traditional Chinese, `F8` and `INSERT`. Feature statistics, records, preferences and engine caches keep their existing storage locations. During shortcut capture the active feature suspends its shortcut listener. Modifier-only presses are ignored. In Tk events `0x20000` represents Alt and `0x8` is a lock-state bit.

The host records the embedded feature's starting window size and minimum size, then applies them when the first feature is ready. Later tab changes preserve manual resizing and maximization. The version in the lower-left corner opens the Holodori-Auto repository. The program's own window sizing and each feature's game-window capture are separate responsibilities.

## Source and models

Clone the main repository to get all five features. [Source origins](SOURCE-ORIGINS.json) records the commits that the feature source was imported from. [Maintenance](UPDATING.md) describes changes to the canonical source and how to find historical training or diagnostic references.

`components/cooking/models-manifest.json` pins the upstream `models.zip` and each checkpoint by size and SHA-256. The installer verifies the archive and the manifest's exact entries, rejects unsafe paths and links, and verifies every model in staging before installing missing files. To keep an existing conflicting model, move it to a backup location before running the installer again.

```powershell
python tools/fetch_models.py
python tools/fetch_models.py --archive C:\path\models.zip
python tools/fetch_models.py --check
```

## Build and accelerator layout

Use Windows x64 and Python 3.13. The README gives the setup for the standard build. After installing runtime and build requirements, reinstall `onnxruntime-directml==1.24.4` with `--force-reinstall --no-deps` to select the DirectML implementation because the OCR dependency also declares a CPU ONNX Runtime distribution.

```powershell
python tools/build_release.py --output dist/Holodori-Auto
```

The standard folder contains the executable, `_internal/`, feature resources and the cooking models. DirectML is the standard GPU backend. To build the optional NVIDIA component in a compatible build environment, install `requirements-nvidia.txt` and select a fresh output folder.

```powershell
python -m pip install -r requirements-nvidia.txt
python tools/build_tensorrt_component.py --output dist/nvidia/accelerators/tensorrt
python tools/build_tensorrt_component.py --output dist/nvidia/accelerators/tensorrt --verify
```

The builder verifies the component format, Python ABI, architecture, dependency versions and sizes of required files. The optional archive supplies `accelerators/tensorrt/` next to `Holodori-Auto.exe`. Jump Rope and Cooking share this component on supported NVIDIA hardware. They use different models and keep separate device-specific engine caches. Jump Rope requires a hardware GPU backend. Cooking can fall back to CPU.

## Verification

```powershell
python -m unittest discover -s tests -v
python tools/check_models_runtime.py --report work/source-model-runtime.json
python tools/smoke_test.py --report work/source-ui.json
python tools/verify_bundle.py dist/Holodori-Auto/Holodori-Auto.exe --report work/packaged-contents.json
python tools/check_models_runtime.py --executable dist/Holodori-Auto/Holodori-Auto.exe --report work/packaged-model-runtime.json
python tools/smoke_test.py --executable dist/Holodori-Auto/Holodori-Auto.exe --report work/packaged-ui.json
```

The UI checks cover all five features with temporary preferences and without game input. GitHub Actions retries a native Tk event-loop watchdog timeout in a fresh process. Assertions and exhausted retries fail the workflow. Run the GPU preflights on supported hardware. For example, `python main.py --check-jump-model-only --backend directml --report work/jump-directml.json` uses synthetic pixels without opening the game.

## 繁體中文

Holodori-Auto 的五個功能都在 `components/` 維護，共用 `main.py` 入口、導覽、語言、快捷鍵與 Windows 建置。程式一次使用一個功能程序。切換前等待既有功能和 Windows Job 內的程序關閉，以釋放畫面擷取、輸入及 GPU 資源。共用設定存於 `%LOCALAPPDATA%\HolodoriAuto\settings.json`，現有紀錄、功能設定與模型快取沿用原路徑。

程式啟動時依顯示器 DPI 和首個功能的預設大小配置視窗。切換功能時保留使用者手動調整的大小與最大化狀態。點擊左下角的版本號可開啟 Holodori-Auto 倉庫。

標準版提供 DirectML。NVIDIA 使用者可另外安裝 TensorRT 元件到執行檔旁的 `accelerators/tensorrt/`。跳繩需要相容的硬體 GPU。料理可回退至 CPU。兩個功能共用加速元件，各自保留模型和快取。料理模型由 `tools/fetch_models.py` 下載並按大小、SHA-256 與 manifest 核對。

請用上方命令執行單元測試、模型預檢與五個功能的原始碼及可攜版介面檢查。測試會使用暫存設定，介面檢查不操作遊戲。來源提交與開發流程收錄於[來源紀錄](SOURCE-ORIGINS.json)及[維護文件](UPDATING.md)。
