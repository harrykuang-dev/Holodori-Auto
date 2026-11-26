# Development and maintenance / 開發與維護

Holodori-Auto maintains the canonical source of all five features under `components/`. Develop and review changes in this repository. A regular clone provides the program source.

```powershell
git clone https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
```

Install the dependencies and cooking models using the [source setup](../README.md). Change each feature in its own directory and put shared settings, interface elements and process coordination in `holodori/`. Keep the language, shortcut capture, deactivation and persisted data contracts in view when changing a feature entry point.

Before merging, run the [architecture and validation checks](ARCHITECTURE.md). Compare any recognition or gameplay changes with the relevant recorded examples and feature tests. For GPU changes, exercise DirectML and the optional TensorRT component on supported hardware. GitHub Actions exercises the source, builds the Windows package, and verifies its contents and embedded interfaces.

[Source origins](SOURCE-ORIGINS.json) records the repositories and commits used at the start of the unified source tree. Historical archives and annotation material are linked from [licensing and corresponding source](../LICENSES.md). Use the original repositories when investigating those references.

## 繁體中文

五個功能的正式原始碼都在同一個倉庫的 `components/`，一般 clone 即可取得。請在本倉庫修改及審查功能，並在 `holodori/` 維護共用設定、介面和程序管理。更動功能入口、畫面擷取或輸入時，請核對既有設定、快捷鍵、停止與切換行為。

合併前執行[架構文件中的檢查](ARCHITECTURE.md)。辨識和操作變更以對應測試及錄影片段比對。涉及加速時，以相容硬體分別檢查 DirectML 與選用的 TensorRT。GitHub Actions 會測試原始碼、建置 Windows 可攜版並檢查包體與嵌入介面。

[來源紀錄](SOURCE-ORIGINS.json)保留整合時的原始倉庫及提交。歷史封存、標註資料及授權來源見[授權與對應原始碼](../LICENSES.md)。
