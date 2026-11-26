# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

Holodori-Auto は、*hololive Dreams* のミニゲーム **ハイ＆ロー**、**釣り**、**縄跳び**、**料理**、**いかだ将棋**を自動化する Windows 用プログラムです。ナビゲーションでモードを選ぶと、そのモードの操作と集計機能を利用できます。言語設定と開始・停止のショートカットは全モードで共通です。

## ダウンロード

[Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest) から `Holodori-Auto-v1.3.0-windows.7z` をダウンロードし、7-Zip で展開して `Holodori-Auto.exe` を実行してください。フォルダー全体を保持してください。Python や CUDA Toolkit の別途インストールは不要です。

標準版には縄跳びと料理用の DirectML が含まれます。縄跳びには DirectML または TensorRT に対応する GPU が必要です。料理は CPU にも切り替えられます。

対応する NVIDIA GPU で TensorRT を使用する場合は、[Releases](https://github.com/harrykuang-dev/Holodori-Auto/releases/latest) から `Holodori-Auto-v1.3.0-tensorrt.7z` をダウンロードします。プログラムを終了し、`Holodori-Auto.exe` と同じフォルダーに展開します。実行ファイルの隣に `accelerators/tensorrt/` ができたことを確認し、プログラムを起動し直してください。TensorRT の初回使用時に GPU 用のエンジンが作成され、次回以降に再利用されます。

## 使い方

1. ゲームを起動し、使用するミニゲームの画面を開きます。
2. Holodori-Auto を起動し、ナビゲーションから対応する機能を選びます。
3. 共通の言語と開始・停止キーを設定し、選択した機能を操作します。料理では、**開始**を押すと選択したモデルを自動的に読み込み、ウォームアップ後に開始します。読み込み中は**停止**でキャンセルできます。
4. 機能を切り替える前に実行を停止します。現在の機能の終了を待ってから、選択した機能を同じウィンドウ内に開きます。

同時に動作するのは選択した機能だけです。共通の言語とキー設定は現在の機能に適用され、機能を切り替えても引き継がれます。各画面の重複する設定欄は非表示になります。新しいキーを入力している間は、現在の機能のキー監視を一時停止し、入力完了後に再開します。

共通設定は `%LOCALAPPDATA%\HolodoriAuto\settings.json` に保存されます。初回起動時は既存の High & Low の言語とキー設定を優先して使用します。既存の設定がない場合は、繁体字中国語、開始 **F8**、停止 **INSERT** が初期値です。集計、ゲーム記録、各機能固有の設定には、元のプログラムの保存先を引き続き使用します。

Windows 10/11 x64 と Windows 版ゲームが必要です。実行中はゲーム画面が見える状態を保ち、選択したモードの解像度、画面キャプチャー、前面表示に関する要件に従ってください。

起動時のウィンドウサイズは、選択したモードの初期サイズを画面の DPI に合わせて調整します。ウィンドウのサイズを変更したり最大化したりした後も、モードを切り替えると現在の状態が維持されます。左下のバージョン表示をクリックすると Holodori-Auto のリポジトリが開きます。

### いかだ将棋

ゲーム内の「ぷかぷかファイト」のソロ画面を開き、Holodori-Auto で**いかだ将棋**を選びます。対局数の上限は 1～9999 です。勝利して結果確認を終えた対局を数えます。Normal を進め、ゲーム内で Normal 30 のクリア後に Challenge が解放されると続けてプレイします。

**エネルギーを自動回復**は既定でオフです。有効にすると、回復アイテム一つの確認を行って続行します。操作前に前面の 16:9 のゲーム画面と合法な着手先を確認します。標準の八駒の局面は、盤面、持ち駒と手番の情報で[どうぶつしょうぎのデータベース](https://dobutsu.brianhliou.com/)に照会できます。

## ソースから実行

Windows x64 と Python 3.13 を使用します。通常のクローンで五つの機能のソースコードを取得できます。

```powershell
git clone https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-build.txt
python -m pip install --force-reinstall --no-deps onnxruntime-directml==1.24.4
python tools/fetch_models.py
python main.py
```

以下の手順では DirectML を使用します。オプションの TensorRT コンポーネントについては[構成とビルドの説明](document/ARCHITECTURE.md)を参照してください。

モデルのインストールコマンドは、料理の対応リリースから `models.zip` を取得し、固定されたファイルサイズと SHA-256 を照合します。各モデルも検証してから、不足しているものだけをインストールします。既存のファイルは保持されます。既存モデルの内容が異なる場合は、そのファイルをバックアップ先へ移動してから再実行してください。料理では開始を押すと選択したモデルを自動的に読み込みます。

料理のリリースから取得済みのアーカイブを使用する場合は、`python tools/fetch_models.py --archive C:\path\models.zip` を実行します。インストール済みモデルをオフラインで検証する場合は、`python tools/fetch_models.py --check` を実行します。

## ビルド

依存関係と料理モデルをインストールした後に実行します。

```powershell
python tools/build_release.py --output dist/Holodori-Auto
```

標準の Windows ビルドには各機能のリソースと料理モデルが含まれます。実行や配布の際は、生成されたポータブルフォルダーを一式保持してください。

## 開発とメンテナンス

Holodori-Auto は `main.py` から起動します。五つの機能のソースは `components/` にあり、ナビゲーション、言語、ショートカット、Windows ビルドを共有します。一度に一つの機能を独立したプロセスで実行します。

| 機能 | 技術資料 |
| --- | --- |
| ハイ＆ロー | [OCR](document/high-low/OCR.md) · [戦略](document/high-low/STRATEGY.md) |
| 釣り | [認識と診断](document/fishing/DEVELOPMENT.md) |
| 縄跳び | [キャプチャー、タイミング、モデル](document/jump-rope/DEVELOPMENT.md) |
| 料理 | [開発と診断](document/cooking/DEVELOPMENT.md) · [推論](document/cooking/INFERENCE.md) |
| いかだ将棋 | [盤面認識と着手の追跡](document/raft-chess.md) |

[技術資料一覧](document/README.md)から[アーキテクチャーと検証手順](document/ARCHITECTURE.md)、[開発と保守の手順](document/UPDATING.md)を参照できます。GitHub Actions はソースをテストし、ポータブル版を検証します。

## 権利とライセンス

縄跳び 1.3.3 と YOLO 派生重みは **AGPL-3.0-only**、釣りは **MIT** です。ハイ＆ローと料理が参照するコンポーネントの既存 MIT 通知は保持されています。NVIDIA ランタイム、その他の依存関係、ゲーム画像にはそれぞれの条件が適用されます。[ライセンスと対応ソース](LICENSES.md). [v1.3.0 のソースアーカイブ](https://github.com/harrykuang-dev/Holodori-Auto/archive/refs/tags/v1.3.0.zip)には五つの機能のソースが含まれます。[ソースの由来](document/SOURCE-ORIGINS.json)に元のリポジトリとコミットを記録しています。
