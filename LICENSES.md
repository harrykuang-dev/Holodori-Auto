# Licensing and corresponding source

Holodori-Auto distributes source, models and dependencies with their respective licenses and notices.

| Feature | Source origin | License and notices |
| --- | --- | --- |
| High & Low | 1.1.4 | [Poker core MIT notice](components/high_low/licenses/poker-core-MIT.txt) (Totarou Oriki) and [Jump Rope MIT notice](components/high_low/licenses/jump-rope-MIT.txt) (harrykuang-dev) apply to the referenced components. The source repository declares no separate project-wide license. |
| Fishing | 1.1.2 | [MIT](components/fishing/LICENSE), copyright 2026 harrykuang-dev. The [artwork notice](components/fishing/assets/NOTICE.md) describes the excluded artwork. |
| Jump Rope and YOLO-derived weights | 1.3.3 | [AGPL-3.0-only](components/jump_rope/LICENSE). See the [source notice](components/jump_rope/NOTICE.md) and [model license](components/jump_rope/models/AGPL-3.0.txt). The model derives from Ultralytics YOLO26. |
| Cooking | 1.1.2 | [Third-party notices](components/cooking/third-party/README.md) and [MIT notice for the copied Fishing shortcut components](components/cooking/third-party/Hololive-Dreams-Fishing-Auto-LICENSE.txt). These grants apply to the specified third-party material. |

The original Holodori-Auto integration code has no separate project-wide license grant declared in this repository. This index records the existing grants for the material included here.

## Obtain the source

The [v1.3.0 source archive](https://github.com/harrykuang-dev/Holodori-Auto/archive/refs/tags/v1.3.0.zip) includes the five feature implementations, Jump Rope's model checkpoint and training and export tools, and the build scripts. The same source is available from Git.

```sh
git clone --branch v1.3.0 https://github.com/harrykuang-dev/Holodori-Auto.git
```

[Source origins](document/SOURCE-ORIGINS.json) records the original repositories and commits used for the unified source tree. See [build instructions](document/ARCHITECTURE.md) for installing the separately distributed Cooking ONNX models from the Cooking release. The [Cooking manifest](components/cooking/models-manifest.json) identifies the exact archive and checkpoints.

## Historical material

- The [Jump Rope v1.2.1 archive](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto/tree/6cd4610b6370fac1b98a17d27562a2d9bb658b3c/archive/v1.2.1) retains its original MIT License.
- Jump Rope's human annotation coordinates and masks use CC BY 4.0 under the [dataset notice](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto/blob/6cd4610b6370fac1b98a17d27562a2d9bb658b3c/annotations/NOTICE.md). Cooking annotation material remains in its [original repository](https://github.com/harrykuang-dev/Hololive-Dreams-Collect-Cooking-Auto/tree/90c09a242fe335284588d895482a25efe17c3ba6/annotations).
- Underlying screenshots, game names, characters and artwork remain the property of their respective rights holders, including COVER and QualiArts.

## Runtime dependencies

The standard portable build includes ONNX Runtime and DirectML. The optional TensorRT component includes NVIDIA's TensorRT and CUDA runtime libraries. Each distribution retains its own license and notices. NVIDIA's display driver is supplied by the system. See the [third-party notices index](THIRD_PARTY_NOTICES.md).

## 繁體中文

跳繩與 YOLO 衍生權重沿用 AGPL-3.0-only，釣魚沿用 MIT。比大小與料理保留所引用元件的既有 MIT 聲明。各授權適用範圍見上表。本倉庫尚未另行宣告 Holodori-Auto 原創整合碼的整體授權。

[v1.3.0 原始碼壓縮包](https://github.com/harrykuang-dev/Holodori-Auto/archive/refs/tags/v1.3.0.zip)包含五個功能的原始碼、跳繩模型檢查點、訓練及匯出工具和建置程式。也可用上方命令取得。[來源紀錄](document/SOURCE-ORIGINS.json)保留各原始倉庫與提交。料理模型由原始料理 Release 提供，版本由模型 manifest 固定。

歷史版跳繩保留原有 MIT 授權。跳繩人工標註坐標和遮罩的 CC BY 4.0 授權範圍見原始資料集聲明。遊戲截圖、名稱、角色及美術的權利由各權利人保有。標準版的 ONNX Runtime 和 DirectML，以及選用 TensorRT 元件包含的 NVIDIA 函式庫，都沿用各自的授權及聲明。
