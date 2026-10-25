# Licensing and corresponding source

This distribution contains components under different licenses. Including them in Holodori-Auto does not replace their copyright notices or grant one license over every file, model, dependency or game asset.

| Component | Included version | License and notices |
| --- | --- | --- |
| High & Low | 1.1.1 | Retain `upstream/high_low/licenses/poker-core-MIT.txt` (Totarou Oriki) and `jump-rope-MIT.txt` (harrykuang-dev). These notices cover the referenced components; the pinned repository does not declare a separate project-wide license. |
| Fishing | 1.1.2 | MIT, copyright 2026 harrykuang-dev: `upstream/fishing/LICENSE`. Artwork is excluded as described in `assets/NOTICE.md`. |
| Jump Rope and YOLO-derived weights | 1.3.0 | GNU Affero General Public License, version 3 only (`AGPL-3.0-only`): `upstream/jump_rope/LICENSE`, `NOTICE.md`, and `models/AGPL-3.0.txt`. The model derives from Ultralytics YOLO26. The historical `archive/v1.2.1` source retains its MIT License. |
| Cooking | 1.1.0 | Retain `upstream/cooking/third-party/README.md`, the MIT notice for the copied Fishing shortcut components, and inference dependency notices. These notices do not declare a project-wide MIT license for Cooking. |

The original Holodori-Auto integration code has no separate project-wide license grant declared in this repository. This index documents the included grants; it does not relicense the integration code or upstream material.

## Obtain the source

The release includes `Holodori-Auto-v1.1.0-source.zip`, containing the integration source and all four pinned Git submodule source trees, including Jump Rope's model checkpoint, export/training scripts and notices. GitHub's automatically generated source archives do not include submodule contents; use the attached complete source archive or clone recursively:

```sh
git clone --recurse-submodules --branch v1.1.0 https://github.com/harrykuang-dev/Holodori-Auto.git
```

`upstream-lock.json` identifies the exact source commit and repository for each component. The cooking ONNX model archive is available from the pinned Cooking release and is installed and verified by `tools/fetch_models.py`. Build instructions are in the README and `docs/ARCHITECTURE.md`.

## Runtime dependencies and artwork

TensorRT and the NVIDIA CUDA runtime retain their NVIDIA license terms; ONNX Runtime, DirectML and the remaining libraries retain their own licenses and third-party notices. The portable program preserves these in `_internal/*dist-info/`, `_internal/upstream/cooking/third-party/` and `_internal/upstream/jump_rope/third_party/`. These components are not relicensed as AGPL or MIT by this repository. NVIDIA's system display driver is not included.

Game names, characters, screenshots and artwork remain the property of their respective rights holders, including COVER and QualiArts. Jump Rope annotation coordinates and masks have their own CC BY 4.0 terms in `upstream/jump_rope/annotations/NOTICE.md`; that grant does not cover the underlying game screenshots. Cooking annotation material retains its own upstream notices. A code license does not grant rights to third-party game assets.

## 繁體中文

本發行包包含不同授權的組件。跳繩 1.3.0 與 YOLO 衍生權重採 AGPL-3.0-only；釣魚採 MIT。比大小引用程式碼及料理引用的快捷鍵組件保留原有 MIT 聲明，不能據此將整個比大小或料理程式標為 MIT。舊版跳繩的 MIT 授權繼續保留。

本倉庫尚未為 Holodori-Auto 原創整合碼另行宣告整體授權；本索引不重新授權整合碼、上游程式或第三方素材。

Release 附帶的 `Holodori-Auto-v1.1.0-source.zip` 包含整合碼與四個鎖定版本的完整 Git 子模組來源，包括跳繩模型檢查點、匯出及訓練工具。亦可使用上方遞迴複製命令取得；GitHub 自動產生的原始碼壓縮包不含子模組內容。各功能來源與提交記錄於 `upstream-lock.json`，料理 ONNX 模型由對應上游 Release 提供。

NVIDIA 執行庫及其他第三方依賴保留各自條款；遊戲美術與截圖的權利歸各權利人。標註資料的授權不代表取得底層遊戲圖像的授權。
