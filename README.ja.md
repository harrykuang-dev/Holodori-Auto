# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md)

Holodori-Auto は、ゲーム画面の画像認識を使う *hololive Dreams* の Windows 向け自動化プログラムです。**ハイ&ロー**、**さかな釣り**、**ホッピン・ロープ**、**そろえてクッキング**、**ぷかぷかファイト**に対応しています。
言語設定と開始・停止のショートカットは、5つの機能で共通です。

## ダウンロードと使い方

Windows 10 または 11（x64）と Windows 版のゲームクライアントを使用してください。**ゲームウィンドウはアスペクト比 16:9 のみ対応しています。** ゲームウィンドウは表示したままにしてください。

1. [リリース](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest)から `Holodori-Auto-v1.3.1-windows.7z` をダウンロードし、7-Zip で展開します。展開先のフォルダーから `Holodori-Auto.exe` を実行します。
2. *hololive Dreams* でミニゲームを開き、Holodori-Auto で対応する機能を選びます。**開始**をクリックするか、共通の開始ショートカットを押します。機能を切り替える前に**停止**をクリックしてください。

標準版には DirectML が含まれます。**ホッピン・ロープ**には DirectML または TensorRT 対応の GPU が必要です。**そろえてクッキング**は CPU でも実行できます。対応する NVIDIA GPU で TensorRT を使う場合は、リリースから `Holodori-Auto-v1.3.1-tensorrt.7z` をダウンロードします。プログラムを終了し、`accelerators/tensorrt/` が `Holodori-Auto.exe` の隣に来るよう展開してから再起動します。初回使用時に GPU 用のエンジンを作成し、次回から再利用します。

## ソースからの実行とビルド

Windows x64 と Python 3.13 を使用します。モデルの取得コマンドは、指定バージョンの**そろえてクッキング**用モデルを検証してからインストールします。

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

同じチェックアウトから以下のコマンドを実行すると、DirectML 対応のポータブル版をビルドして検証できます。ビルドごとに新しい出力先を指定してください。

```powershell
& $python tools/build_release.py --output dist/Holodori-Auto
& $python tools/verify_bundle.py dist/Holodori-Auto/Holodori-Auto.exe --report work/packaged-contents.json
```

## 開発とメンテナンス

五つの機能は `components/` で管理しています。共通ウィンドウ、言語、およびショートカットは `holodori/` で管理しており、各機能は独立したプロセスで動作します。GitHub Actions でソースと Windows ポータブル版を検証します。

[技術文書](document/README.md) · [ビルドと検証](document/ARCHITECTURE.md) · [メンテナンス手順](document/UPDATING.md) · [ゲーム内の用語](document/GAME-TERMS.md)

## 注意事項とライセンス

Holodori-Auto は独立したプロジェクトです。ゲーム名、スクリーンショット、アートワークの権利はそれぞれの権利者に帰属します。

Holodori-Auto のオリジナルコードと文書には [MIT ライセンス](LICENSE)が適用されます。**ホッピン・ロープ**の実装と YOLO 由来のモデル重みには引き続き [AGPL-3.0-only](components/jump_rope/LICENSE) が適用されます。第三者の素材には個別の条件が適用されます。[ライセンスと対応ソース](LICENSES.md)と[第三者の通知](THIRD_PARTY_NOTICES.md)をご覧ください。
