# テトリスWebゲーム - ローカル起動ガイド

## 🚀 簡単起動方法

### 方法1: 自動起動スクリプト（推奨）

```bash
# tetris_webディレクトリで実行
python3 run_local.py
```

このスクリプトは以下を自動で行います：
- 依存関係のインストール
- サーバーの起動
- ブラウザの自動起動

### 方法2: 手動起動

```bash
# 1. tetris_webディレクトリに移動
cd tetris_web

# 2. 依存関係をインストール
cd backend
pip3 install -r requirements.txt

# 3. サーバーを起動
python3 main.py
```

## 🌐 アクセス方法

サーバー起動後、ブラウザで以下のURLにアクセス：
```
http://localhost:8080
```

## 📱 スマートフォンからのアクセス

### 1. PCのIPアドレスを確認
```bash
# macOS
ifconfig | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig | findstr "IPv4"
```

### 2. スマートフォンからアクセス
```
http://[PCのIPアドレス]:8080
```

例：`http://192.168.1.100:8080`

## 🎮 操作方法

### PC（キーボード）
- **←→**: 左右移動
- **↑**: 回転
- **↓**: 落下
- **Space**: ハードドロップ
- **B**: 爆弾ピース生成
- **P**: ポーズ/再開
- **+/-**: 速度調整

### スマートフォン（タッチ）
- 画面下部の操作ボタンを使用
- ゲームボードをタップして爆弾を配置

## 🔧 トラブルシューティング

### ポート8080が使用中の場合
```bash
# 使用中のプロセスを確認
lsof -i :8080

# プロセスを終了
kill -9 [プロセスID]
```

### 依存関係のインストールエラー
```bash
# pipをアップグレード
pip3 install --upgrade pip

# 仮想環境を使用
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows
pip3 install -r requirements.txt
```

### 静的ファイルが見つからない場合
- `tetris_web`ディレクトリで実行していることを確認
- `frontend`ディレクトリが存在することを確認

## 📁 ディレクトリ構造

```
tetris_web/
├── backend/
│   ├── main.py          # サーバーコード
│   ├── game.py          # ゲームロジック
│   └── requirements.txt # 依存関係
├── frontend/
│   ├── index.html       # メインHTML
│   ├── style.css        # スタイルシート
│   ├── script.js        # JavaScript
│   └── assets/          # 画像・音声ファイル
├── run_local.py         # 自動起動スクリプト
└── README_LOCAL.md      # このファイル
```

## 🎯 機能

- ✅ クラシックテトリスゲームプレイ
- ✅ 爆弾システム（10ライン削除で爆弾獲得）
- ✅ 速度調整機能
- ✅ スマートフォン対応
- ✅ 美しいOP画面
- ✅ 音声効果
- ✅ リアルタイムWebSocket通信

## 🛑 停止方法

サーバーを停止するには、ターミナルで `Ctrl+C` を押してください。 