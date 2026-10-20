# Holodori-Auto

[English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Indonesian](README.id.md) · [简体中文](README.zh-CN.md)

*hololive Dreams* の**ハイ＆ロー**、**釣り**、**縄跳び**、**料理**を一つのウィンドウにまとめた Windows 用プログラムです。言語設定と開始・停止キーを共通化し、各機能のゲームロジック、操作画面、集計、診断機能を維持しています。ナビゲーションと共通設定には同じ Fluent スタイルを使用し、各機能の既存の画像とテーマカラーを引き継いでいます。

| 機能 | 元のプログラム |
| --- | --- |
| ハイ＆ロー | [Hololive-Dreams-High-low-Auto-Personal](https://github.com/harrykuang-dev/Hololive-Dreams-High-low-Auto-Personal) |
| 釣り | [Hololive-Dreams-Fishing-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Fishing-Auto) |
| 縄跳び | [Hololive-Dreams-Jump-Rope-Auto](https://github.com/harrykuang-dev/Hololive-Dreams-Jump-Rope-Auto) |
| 料理 | [Hololie-Dreams-Collect-Cooking-Auto](https://github.com/harrykuang-dev/Hololie-Dreams-Collect-Cooking-Auto) |

## ダウンロード

[v1.0.0](https://github.com/harrykuang-dev/Holodori-Auto/releases/tag/v1.0.0) から `Holodori-Auto-v1.0.0-windows-1of3.zip`、`Holodori-Auto-v1.0.0-windows-2of3.zip`、`Holodori-Auto-v1.0.0-windows-3of3.zip` の3ファイルをすべてダウンロードします。すべてを同じ場所に展開し、内容を1つの `Holodori-Auto` フォルダーにまとめてから、中の `Holodori-Auto.exe` を実行してください。フォルダー全体を保持してください。依存ライブラリと料理モデルが含まれているため、Python の別途インストールは不要です。`SHA256SUMS.txt` に各アーカイブのチェックサムを記載しています。

## 使い方

1. ゲームを起動し、使用するミニゲームの画面を開きます。
2. Holodori-Auto を起動し、ナビゲーションから対応する機能を選びます。
3. 共通の言語と開始・停止キーを設定し、選択した機能を操作します。料理では、**モデルを読み込む**操作を行ってから**開始**してください。
4. 機能を切り替える前に実行を停止します。現在の機能の終了を待ってから、選択した機能を同じウィンドウ内に開きます。

同時に動作するのは選択した機能だけです。共通の言語とキー設定は現在の機能に適用され、機能を切り替えても引き継がれます。各画面の重複する設定欄は非表示になります。新しいキーを入力している間は、現在の機能のキー監視を一時停止し、入力完了後に再開します。

共通設定は `%LOCALAPPDATA%\HolodoriAuto\settings.json` に保存されます。初回起動時は既存の High & Low の言語とキー設定を優先して使用します。既存の設定がない場合は、繁体字中国語、開始 **F8**、停止 **INSERT** が初期値です。集計、ゲーム記録、各機能固有の設定には、元のプログラムの保存先を引き続き使用します。

Windows 10/11 x64 と Windows 版ゲームが必要です。実行中はゲーム画面を見える状態に保ち、選択した機能の解像度、画面キャプチャー、前面表示に関する要件に従ってください。各機能の詳しい操作と動作は、上記の元リポジトリの README を参照してください。

## ソースから実行

Windows x64 と Python 3.13 を使用します。リポジトリはサブモジュールを含めてクローンしてください。GitHub のソース ZIP にはサブモジュールの内容が含まれません。

```powershell
git clone --recurse-submodules https://github.com/harrykuang-dev/Holodori-Auto.git
cd Holodori-Auto
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-build.txt
python tools/fetch_models.py
python main.py
```

依存関係には CUDA 12.8 ランタイムが含まれます。料理は元の動作に従い、利用可能な NVIDIA GPU を自動で使用し、利用できない場合は CPU を使用します。

モデルのインストールコマンドは、料理の対応リリースから `models.zip` を取得し、固定されたファイルサイズと SHA-256 を照合します。各モデルも検証してから、不足しているものだけをインストールします。既存のファイルは保持されます。既存モデルの内容が異なる場合は、そのファイルをバックアップ先へ移動してから再実行してください。料理画面でのモデル読み込み操作は別途必要です。

料理のリリースから取得済みのアーカイブを使用する場合は、`python tools/fetch_models.py --archive C:\path\models.zip` を実行します。インストール済みモデルをオフラインで検証する場合は、`python tools/fetch_models.py --check` を実行します。

## ビルド

依存関係と料理モデルをインストールした後に実行します。

```powershell
python tools/build_release.py --output dist/Holodori-Auto
```

実行・配布時には、生成されたポータブルフォルダー全体を保持してください。依存関係、元のリソース、料理モデルがビルドに含まれます。

## 各機能の更新を取り込む

元の四つのリポジトリは、それぞれ独立した Git サブモジュールとして保持されています。`upstream-lock.json` は、統合版で使用する各機能のコミットとバージョンを記録します。一つの機能を更新する際に、そのゲームアルゴリズムを Holodori-Auto へコピーしたりマージしたりする必要はありません。

```powershell
python tools/sync_upstreams.py --check
python tools/sync_upstreams.py --module fishing
git add upstream/fishing upstream-lock.json
python tools/sync_upstreams.py --verify
python -m unittest discover -s tests -v
```

`--module fishing` を省略すると四つの機能をすべて更新します。マージ前に依存関係、モデルのマニフェスト、統合インターフェースの変更を確認してください。料理を更新した場合は、モデルのインストールコマンドを再実行します。

GitHub Actions は毎日および手動実行時に更新を確認し、更新用 Pull Request を作成して統合チェックを実行します。更新は内容を確認してから手動でマージします。統合インターフェースとビルド構成は[設計と保守の説明](docs/ARCHITECTURE.md)を参照してください。

## 権利とライセンス

元のソースコード、画像、ライセンスファイル、第三者に関する通知は、`upstream/` 内の各機能に保持されています。各条件と出典は元のリポジトリを参照してください。ゲーム名と画像の権利は、それぞれの権利者に帰属します。
