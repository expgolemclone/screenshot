# Books

Kindle等のスクリーンショットを連続撮影し、MEGAにアップロードするツール。

## セットアップ

[uv][uv] が必要です。

```bash
git clone https://github.com/expgolemclone/books.git
cd books
python scripts/setup.py
```

または手動で:

```bash
uv sync
```

## 使い方

### スクリーンショット撮影 (screenshot.py)

```bash
uv run python scripts/screenshot.py
```

1. 保存フォルダの英語名を入力
2. ページ送り操作を選択（左/右矢印キー or カスタム座標クリック）
3. 10秒後に自動撮影開始（開始前に対象ウィンドウをアクティブにしてください）
4. 前回と同じスクリーンショットになったらリトライし、それでも同じなら終了
5. MEGAへのアップロードを選択可能

オプション:

```bash
uv run python scripts/screenshot.py --max 50
```

### 既存フォルダのアップロード (upload.py)

contents/ 内のスクショ済みフォルダを番号で選択してMEGAにアップロードできます。

```bash
uv run python scripts/upload.py
uv run python scripts/upload.py --dest /book
uv run python scripts/upload.py --folder permutation_city
uv run python scripts/upload.py --skip-if-exists
```

## MEGAへのアップロードについて

bookフォルダにコンテンツを追加してくれる方は編集権限を渡しますので、メールアドレスをLINEで教えてください。

### MEGAコマンド（ターミナルから使用可能）

```bash
mega-transfers        # アップロード進捗確認
mega-ls /book         # アップロード済みファイル一覧
mega-whoami           # ログイン状態確認
mega-login email pass # MEGAにログイン
```

## ファイル構成

```
books/
├── contents/           # 本ごとのスクショ画像フォルダ
│   └── {book_name}/
├── scripts/
│   ├── setup.py        # セットアップ
│   ├── screenshot.py   # スクリーンショット撮影
│   └── upload.py       # MEGAアップロード
├── pyproject.toml
├── uv.lock
└── README.md
```

## 必要環境

- Python 3.10以上
- [uv][uv]
- MEGAcmd（アップロード機能を使う場合）

## ライセンス

MIT License

[uv]: https://docs.astral.sh/uv/
