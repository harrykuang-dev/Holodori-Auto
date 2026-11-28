# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md)

Holodori-Auto 是一款基于画面识别的 *hololive Dreams* Windows 自动化程序，支持**猜高低**、**钓鱼**、**跳跳大绳**、**拼配厨房**和**浮排大战**。
五个功能共用语言设置和开始、停止快捷键。

## 下载和使用

使用 Windows 10 或 11（x64）及 Windows 游戏客户端。**仅支持 16:9 的游戏窗口。** 请保持游戏窗口可见。

1. 从[发布页面](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest)下载 `Holodori-Auto-v1.3.1-windows.7z`，用 7-Zip 解压，然后从解压后的文件夹运行 `Holodori-Auto.exe`。
2. 进入 *hololive Dreams* 中的小游戏，选择 Holodori-Auto 中对应的功能，点击**开始**或按共用开始快捷键。切换功能前先点击**停止**。

标准版内置 DirectML。**跳跳大绳**需要支持 DirectML 或 TensorRT 的 GPU，**拼配厨房**也可使用 CPU。使用兼容 NVIDIA 显卡时，可从发布页面下载可选的 [Holodori-Auto-v1.3.1-tensorrt.7z](https://github.com/harrykuang-dev/Holodori-Auto/releases/download/v1.3.1/Holodori-Auto-v1.3.1-tensorrt.7z)。关闭程序，解压后将 `accelerators/tensorrt/` 放在 `Holodori-Auto.exe` 旁，再重新启动。首次使用 TensorRT 会为该 GPU 创建引擎，供后续运行复用。

## 从源码运行与构建

使用 Windows x64 和 Python 3.13。模型下载命令会验证固定版本的**拼配厨房**模型，再进行安装。

```powershell
git clone https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
py -3.13 -m venv .venv
$python = ".\.venv\Scripts\python.exe"
& $python -m pip install -r requirements.txt -r requirements-build.txt
& $python -m pip install --force-reinstall --no-deps onnxruntime-directml==1.24.4
& $python tools/fetch_models.py
& $python main.py
```

在同一份源码中运行以下命令，可构建并验证 DirectML 便携版。每次构建请使用新的输出目录。

```powershell
& $python tools/build_release.py --output dist/Holodori-Auto
& $python tools/verify_bundle.py dist/Holodori-Auto/Holodori-Auto.exe --report work/packaged-contents.json
```

## 开发与维护

五个功能都在 `components/` 维护。共享窗口、语言和快捷键由 `holodori/` 维护，各功能在独立进程中运行。GitHub Actions 验证源码和 Windows 便携版。

[技术文档](document/README.md) · [构建与验证](document/ARCHITECTURE.md) · [维护流程](document/UPDATING.md) · [游戏用词](document/GAME-TERMS.md)

## 声明与许可

Holodori-Auto 是独立项目。游戏名称、截图和美术归各权利人所有。

Holodori-Auto 原创代码和文档采用 [MIT 许可](LICENSE)。**跳跳大绳**的实现及 YOLO 派生权重沿用 [AGPL-3.0-only](components/jump_rope/LICENSE)。第三方内容适用各自的条款。详见[许可与对应源码](LICENSES.md)和[第三方声明](THIRD_PARTY_NOTICES.md)。
