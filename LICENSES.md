# Licensing and corresponding source / 授權與對應原始碼

## Project license / 專案授權

The original code and documentation maintained in Holodori-Auto use the [MIT License](LICENSE), except for the implementation and related material covered by the AGPL notice below.

Holodori-Auto 自行維護的原創程式碼與文件採用 [MIT 授權](LICENSE)。下述實作及相關資料適用各自的 AGPL 授權。

## AGPL-covered material / 適用 AGPL 的項目

The Hoppin' Rope program and controller, training and export tools, and YOLO-derived weights retain [AGPL-3.0-only](components/jump_rope/LICENSE). See the [component notice](components/jump_rope/NOTICE.md), [model license](components/jump_rope/models/AGPL-3.0.txt), [source checkpoint](components/jump_rope/models/rope.pt), and [training and export source](components/jump_rope/training/).

蹦蹦大跳繩的程式與控制器、訓練及匯出工具，以及衍生自 YOLO 的權重，沿用 [AGPL-3.0-only](components/jump_rope/LICENSE)。上方連結提供授權聲明、原始模型檢查點和訓練及匯出原始碼。

## Third-party terms / 第三方授權

External code, models, dependencies, and game material follow their respective licenses and rights. The separate dataset's [human annotation coordinates and masks](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto/blob/6cd4610b6370fac1b98a17d27562a2d9bb658b3c/annotations/NOTICE.md) use CC BY 4.0. Game names, images, characters, and artwork remain with their respective rights holders, including COVER and QualiArts. See the [official game credits](https://hololive.hololivepro.com/en/news/20260723-01-401/). Holodori-Auto is an independent project. See the [third-party notices](THIRD_PARTY_NOTICES.md) for credits and retained notices.

外部程式碼、模型、相依套件及遊戲素材均沿用各自的授權與權利聲明。另行提供的[人工標註座標和遮罩](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto/blob/6cd4610b6370fac1b98a17d27562a2d9bb658b3c/annotations/NOTICE.md)採用 CC BY 4.0。遊戲名稱、影像、角色及美術權利由 COVER、QualiArts 等各權利人保有。Holodori-Auto 為獨立專案。外部來源與保留聲明列在[第三方來源與聲明](THIRD_PARTY_NOTICES.md)。

## Source for release builds / 發行版對應原始碼

Use the source archive listed with the matching version on [GitHub Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases), or check out the corresponding Git tag. The [build instructions](README.md#run-and-build-from-source) and [model manifest](components/cooking/models-manifest.json) document the separately downloaded ONNX assets.

請從 [GitHub Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases) 下載與執行檔版本相同的原始碼壓縮檔，或切換至對應的 Git 標籤。需另外下載的 ONNX 檔案見[建置說明](README.zh-TW.md#從原始碼執行與建置)及[模型清單](components/cooking/models-manifest.json)。
