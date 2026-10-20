# 更新原始程式

Holodori-Auto 以四個 Git submodule 保留原始程式，整合層負責共用視窗、導覽、語言與開始／停止快捷鍵。原始演算法及介面檔案直接來自各自倉庫；各頁面重複的語言與快捷鍵列由適配層隱藏。每個正式整合版本由 submodule commit 與 `upstream-lock.json` 共同固定，不會在使用者啟動時下載或更換程式碼。

共用偏好設定的 `language`、`start_key`、`stop_key` 儲存於 `%LOCALAPPDATA%\HolodoriAuto\settings.json`，並套用至目前及後續開啟的功能。首次啟動優先沿用既有 High & Low 偏好，否則使用繁體中文、`F8` 開始、`INSERT` 停止。原有統計與遊戲紀錄維持原位置。

## 初次取得原始碼

```powershell
git clone --recurse-submodules https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
python tools/sync_upstreams.py --verify
```

一般 clone 後補齊 submodule，或切換整合版本後還原該版本的原始程式：

```powershell
git submodule sync --recursive
git submodule update --init --recursive
```

Git submodule URL 變更時，先檢查 `.gitmodules` 的來源，再執行 `git submodule sync --recursive`。

## 檢查及更新

只檢查遠端 `main`：

```powershell
python tools/sync_upstreams.py --check
python tools/sync_upstreams.py --check --module fishing
```

`--check` 會 fetch 原始倉庫的遠端參照並顯示 commit 差異，不變更任何 checkout、Git index 或 lock 檔案。加上 `--json` 可取得機器可讀報告。檢查成功的結束碼為 0；有更新時仍為 0，可從報告的 `changed` 欄位判斷。

更新全部或指定程式：

```powershell
python tools/sync_upstreams.py
python tools/sync_upstreams.py --module fishing
python tools/sync_upstreams.py --module high_low --module jump_rope
```

可選名稱是 `high_low`、`fishing`、`jump_rope`、`cooking`。工具從 `.gitmodules` 讀取來源和追蹤分支，fetch 完成後將所選 submodule 切到該分支的確切 commit，並更新 lock。工具不修改原始程式、不自動 commit、push 或發布。原始倉庫若發生歷史重寫，檢查結果仍會顯示新舊 commit，更新前應檢閱差異。

更新前，所選 submodule、`.gitmodules` 及 lock 的既有修改必須先處理。原始程式內的未追蹤檔案也會阻止更新；整合倉庫其他檔案的工作會保留。若新版本要追蹤本機已有的 ignored 檔案，工具會拒絕覆寫。所有遠端取得完成後才切換 checkout；fetch 失敗不會留下部分程式已更新的狀態。

## 驗證及提交

工具將更新留在工作目錄，讓修改可以先檢閱。確認內容後，將 gitlink 與 lock 一起 stage，再驗證：

```powershell
git diff --submodule=log
git diff -- upstream-lock.json
git add upstream upstream-lock.json
python tools/sync_upstreams.py --verify
python -m pip install -r requirements.txt -r requirements-build.txt
python -m compileall -q holodori tools upstream
python -m unittest discover -s tests -v
python tools/fetch_models.py
python tools/check_models_runtime.py
python tools/smoke_test.py
python tools/build_release.py --output dist/Holodori-Auto
python tools/check_models_runtime.py --executable dist/Holodori-Auto/Holodori-Auto.exe
python tools/smoke_test.py --executable dist/Holodori-Auto/Holodori-Auto.exe
```

`--verify` 不需要網路，會確認四個 checkout、Git index 內的 gitlink、lock 的 commit、來源、分支及宣告版本完全一致。檢查原始碼中的版本常數時只解析文字，不執行原始程式；來源沒有可辨識的版本常數時記錄 `null`，commit 仍是版本依據。

Windows 整合檢查涵蓋四個原始介面的載入。上游更新後應另檢查共用語言是否套用至目前及後續功能、原設定列是否隱藏、快捷鍵擷取期間監聽是否暫停，以及完成後是否恢復。單獨按修飾鍵應被忽略；Num Lock 的 `0x8` 不得被當作 Alt 的 `0x20000`。演算法或介面入口如有不相容變更，修改 `holodori/` 的整合適配層，讓原始倉庫繼續獨立維護。合併前也應在實際遊戲中檢查需要的功能。

`--write-lock` 僅供首次建立整合倉庫使用：由四個現有且已 stage 的 submodule pin 建立 lock，不連線，也不覆寫既有 lock。正常更新不需要使用這個選項。

## 自動更新 Pull Request

`Check upstream updates` workflow 每天 02:15 UTC（UTC+8 為 10:15）檢查四個倉庫，也可以在 Actions 手動執行並選擇一個程式。只有出現 commit 差異時，才更新 `automation/sync-upstreams` 分支並建立或更新 Pull Request；此分支由 workflow 維護，不應放置人工修改。

自動更新會執行離線 Git 測試，接著呼叫 Windows 驗證 workflow，檢查 lock、Python 原始碼、整合測試、四個原始倉庫的測試、四個原始介面及完整 portable build。原始測試各自使用獨立程序和暫存使用者資料，跳繩測試也包含其原始 GUI 測試。建置結果以 Actions artifact 保留 14 天。workflow 不自動合併、不建立 release。

倉庫需啟用 Actions，並在 Actions 的 Workflow permissions 允許 GitHub Actions 建立 Pull Request。workflow 只對整合倉庫使用 `contents: write` 和 `pull-requests: write`；不寫入四個原始倉庫。若此設定未開啟，更新流程會明確失敗，維護者仍可按上述步驟手動更新。

## 還原更新

尚未提交時，先保留需要的本機修改，再把 lock 與所選 gitlink 還原到目前整合版本，然後讓 checkout 回到 pin：

```powershell
git restore --staged --worktree upstream-lock.json upstream/fishing
git submodule update --init --recursive upstream/fishing
python tools/sync_upstreams.py --verify
```

此例只還原釣魚。若同次更新多個程式，應將同次修改的所有 gitlink 與完整 lock 一起還原。已提交的更新則 revert 該整合 commit，並執行 `git submodule update --init --recursive`。
