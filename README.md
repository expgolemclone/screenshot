# Screenshot Tool

矢印キー入力または指定座標クリックでページを進め、アクティブウィンドウのスクリーンショットを連続撮影するツールです。
同じ画像になったら自動終了し、MEGAにアップロードできます。

## セットアップ方法

### 方法1: GitHubからクローン
```bash
git clone https://github.com/expgolemclone/screenshot.git
cd screenshot
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

### 方法2: 手動ダウンロード
1. このリポジトリをダウンロード（Code → Download ZIP）
2. 解凍してPCの任意の場所に配置
3. `setup.ps1` を右クリックして「PowerShellで実行」
4. 依存パッケージが自動でインストールされます

### PowerShellの実行がブロックされる場合
一時的に許可して実行できます。

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
powershell -ExecutionPolicy Bypass -File .\run.ps1
powershell -ExecutionPolicy Bypass -File .\run_tracker.ps1
```

## 使い方

### スクリーンショット撮影 (click_and_screenshot.py)

`run.ps1` を右クリックして「PowerShellで実行」

1. 保存フォルダの英語名を入力
2. ページ送り操作を選択（左/右矢印キー or カスタム座標クリック）
3. 10秒後に自動撮影開始（開始前に対象ウィンドウをアクティブにしてください）
4. 前回と同じスクリーンショットになったらリトライし、それでも同じなら終了
5. MEGAへのアップロードを選択可能

オプション例:

- `powershell -ExecutionPolicy Bypass -File .\run.ps1 --max 50` （最大50回）

### 既存フォルダのアップロード (upload.py)

スクショ済みフォルダを番号で選択して MEGA にアップロードできます。

```powershell
# 例: 仮想環境 (setup.ps1 済みの場合)
.\.venv\Scripts\python.exe upload.py

# 送信先を指定
.\.venv\Scripts\python.exe upload.py --dest /book

# フォルダ名/パスを指定（番号選択をスキップ）
.\.venv\Scripts\python.exe upload.py --folder permutation_city

# 既に存在するフォルダはスキップ
.\.venv\Scripts\python.exe upload.py --skip-if-exists
```

### マウス座標確認 (mouse_tracker.py)

`run_tracker.ps1` を右クリックして「PowerShellで実行」

- リアルタイムでマウス座標を表示
- Enterキーで座標を記録
- Escキーで終了

## 必要環境

- Windows 10/11
- Python 3.8以上（インストール時にPATHに追加）
- MEGAcmd（アップロード機能を使う場合）

## MEGAへのアップロードについて

bookフォルダにコンテンツを追加してくれる方は編集権限を渡しますので、メールアドレスをLINEで教えてください。

### MEGAコマンド（ターミナルから使用可能）

セットアップ後、以下のコマンドがターミナルから使えます：

```bash
# アップロード進捗確認
mega-transfers

# アップロード済みファイル一覧
mega-ls /book

# ログイン状態確認
mega-whoami

# MEGAにログイン
mega-login メールアドレス パスワード
```

## ファイル構成

```
screenshot/
├── setup.ps1            # セットアップ用
├── run.ps1              # メインスクリプト実行用
├── run_tracker.ps1      # マウストラッカー実行用
├── requirements.txt     # 依存パッケージ
├── click_and_screenshot.py
├── mouse_tracker.py
├── upload.py
└── README.md
```

## ライセンス

MIT License
