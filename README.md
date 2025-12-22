# Screenshot Tool

指定座標を自動クリックしてスクリーンショットを連続撮影するツールです。
同じ画像になったら自動終了し、MEGAにアップロードできます。

## セットアップ方法

### 方法1: GitHubからクローン
```bash
git clone https://github.com/expgolemclone/screenshot.git
cd screenshot
setup.bat
```

### 方法2: 手動ダウンロード
1. このリポジトリをダウンロード（Code → Download ZIP）
2. 解凍してPCの任意の場所に配置
3. `setup.bat` をダブルクリックして実行
4. 依存パッケージが自動でインストールされます

## 使い方

### スクリーンショット撮影 (click_and_screenshot.py)

`run.bat` をダブルクリック

1. 保存フォルダの英語名を入力
2. クリック位置を選択（プリセットまたはカスタム座標）
3. 3秒後に自動撮影開始
4. 前回と同じスクリーンショットになったら自動終了
5. MEGAへのアップロードを選択可能

### マウス座標確認 (mouse_tracker.py)

`run_tracker.bat` をダブルクリック

- リアルタイムでマウス座標を表示
- Enterキーで座標を記録
- Escキーで終了

## 必要環境

- Windows 10/11
- Python 3.8以上（インストール時にPATHに追加）
- MEGAcmd（アップロード機能を使う場合）

## MEGAへのアップロードについて

bookフォルダにコンテンツを追加してくれる方は編集権限を渡しますので、メールアドレスをLINEで教えてください。

## ファイル構成

```
screenshot/
├── setup.bat            # セットアップ用
├── run.bat              # メインスクリプト実行用
├── run_tracker.bat      # マウストラッカー実行用
├── requirements.txt     # 依存パッケージ
├── click_and_screenshot.py
├── mouse_tracker.py
└── README.md
```

## ライセンス

MIT License
