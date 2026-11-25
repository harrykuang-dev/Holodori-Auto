# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Holodori-Auto 是一款 Windows 自动化程序，支持 *hololive Dreams* 的**猜高低（High & Low）**、**钓鱼**、**跳绳**、**料理**和**浮排棋**。在导航栏选择模式，即可使用该模式的操作与统计功能。各模式共用语言设置及开始／停止快捷键。

## 下载

从 [Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest) 下载 `Holodori-Auto-v1.2.10-windows.7z`，使用 7-Zip 解压后运行 `Holodori-Auto.exe`。请保留完整文件夹，无需另外安装 Python 或 CUDA Toolkit。

跳绳与料理共用同一套 TensorRT 10.13、CUDA 运行库与 DirectML。兼容的 NVIDIA GPU 自动使用 TensorRT，其他受支持的 GPU 使用 DirectML。跳绳需要兼容 GPU；料理也可回退到 CPU。各功能保留独立模型与设备引擎缓存。

> **首次使用提示：** 使用兼容的 NVIDIA RTX 20 系列及更新显卡时，首次使用跳绳或料理需为本机 GPU 编译 TensorRT 引擎，预计约 **1～2 分钟**，实际时间取决于硬件与系统负载。请等待编译完成；引擎会缓存供后续使用。

## 使用方式

1. 打开游戏并进入要使用的小游戏。
2. 启动 Holodori-Auto，在导航栏选择对应功能。
3. 设置共用语言与开始／停止快捷键，再操作所选功能。料理点击**开始**后会自动加载所选模型并预热，完成后开始；加载期间可点击**停止**取消。
4. 切换功能前先停止运行。切换时会等待当前功能完成关闭，再在同一个窗口打开所选功能。

同一时间只运行所选功能。共用语言选择框及快捷键设置会应用到当前功能，切换功能后也会沿用；各页面中重复的设置行会隐藏。录入新快捷键期间，当前功能的快捷键监听会暂停，完成后恢复。

共用偏好设置保存在 `%LOCALAPPDATA%\HolodoriAuto\settings.json`。首次启动时，优先沿用已有 High & Low 的语言及快捷键；若没有已有设置，默认使用繁体中文、**F8** 开始、**INSERT** 停止。原有统计、游戏记录及各功能专属选项继续使用原程序的数据位置。

需要 Windows 10/11 x64 和 Windows 版游戏。运行期间保持游戏画面可见，并遵循所选模式对分辨率、画面捕获和前台操作的要求。

程序启动时会根据所选模式的默认窗口大小和屏幕 DPI 调整显示。手动调整大小或最大化后，切换模式会保留当前窗口状态。点击左下角版本号会打开 Holodori-Auto 仓库。

### 浮排棋

进入游戏内「浮排大战」的单人页面，然后选择 Holodori-Auto 的**浮排棋**。将**局数上限**设为 1～9999，点击**开始**，或在游戏前台按共享开始快捷键。局数以获胜且完成结算的对局计算。程序会推进可用的 Normal 关卡，并在游戏通过 Normal 第 30 关解锁 Challenge 后继续。

**自动补充能量**默认关闭。开启后，程序可确认游戏内的一瓶道具补充后继续。浮排棋会检查前台的 16:9 游戏窗口、棋盘状态和合法落点高亮。标准八子局面可以查询公开的[动物将棋棋谱库](https://dobutsu.brianhliou.com/)，查询包含棋子、候补和行棋方的抽象棋盘。

## 从源代码运行

使用 Windows x64 与 Python 3.13。克隆仓库时需要一并获取子模块；GitHub 的源代码 ZIP 不包含子模块内容。

```powershell
git clone --recurse-submodules https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-build.txt
python -m pip install --force-reinstall --no-deps onnxruntime-directml==1.24.4
python tools/fetch_models.py
python main.py
```

依赖包含共用的 TensorRT 10.13 与 DirectML 运行环境，不再需要 PyTorch。

模型安装命令会下载料理对应版本附带的 `models.zip`，核对锁定版本的文件大小与 SHA-256，再逐一验证模型后安装。只安装缺少的模型并保留已有文件；若已有模型内容不同，请先将该文件移至备份位置后重试。料理点击开始后会自动加载所选模型。

已下载料理 Release 模型压缩包时，可运行 `python tools/fetch_models.py --archive C:\path\models.zip`。只需离线核对已安装模型时，运行 `python tools/fetch_models.py --check`。

## 构建

安装依赖与料理模型后运行：

```powershell
python tools/build_release.py --output dist/Holodori-Auto
```

运行与分发时请保留生成的完整便携式文件夹。构建内容包含依赖、原始资源与料理模型。

## 开发与维护

Holodori-Auto 以 `main.py` 为统一入口。五个功能共享导航、语言、快捷键和 Windows 便携版，各功能分别管理游戏识别与诊断。

| 功能 | 技术文档 |
| --- | --- |
| 猜高低 | [奖励 OCR](document/high-low/OCR.md) · [策略](document/high-low/STRATEGY.md) |
| 钓鱼 | [识别与诊断](document/fishing/DEVELOPMENT.md) |
| 跳绳 | [捕获、时序和模型](document/jump-rope/DEVELOPMENT.md) |
| 料理 | [开发与诊断](document/cooking/DEVELOPMENT.md) · [模型推理](document/cooking/INFERENCE.md) |
| 浮排棋 | [棋盘识别与落子跟踪](document/raft-chess.md) |

[技术文档索引](document/README.md)提供[架构与验证流程](document/ARCHITECTURE.md)及[固定源代码版本的维护方式](document/UPDATING.md)。GitHub Actions 会核对源代码版本、运行测试并验证便携版。

## 声明与许可

跳绳 1.3.3 与 YOLO 衍生权重采用 **AGPL-3.0-only**，钓鱼采用 **MIT**。猜高低与料理引用组件的现有 MIT 声明继续保留；NVIDIA 运行库、其他依赖及游戏美术维持各自条款。详见[许可与对应源代码](LICENSES.md)。Release 提供包含四个锁定子模块源代码的 `Holodori-Auto-v1.2.10-source.zip`；GitHub 自动生成的源代码压缩包不含子模块。
