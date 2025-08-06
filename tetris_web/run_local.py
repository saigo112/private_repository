#!/usr/bin/env python3
"""
ローカル環境でテトリスゲームを起動するスクリプト
"""

import os
import sys
import subprocess
import webbrowser
import time

def main():
    print("🎮 テトリスWebゲーム - ローカル起動")
    print("=" * 50)
    
    # 現在のディレクトリを確認
    current_dir = os.getcwd()
    print(f"現在のディレクトリ: {current_dir}")
    
    # backendディレクトリに移動
    backend_dir = os.path.join(current_dir, "backend")
    if not os.path.exists(backend_dir):
        print("❌ backendディレクトリが見つかりません")
        print("このスクリプトはtetris_webディレクトリで実行してください")
        sys.exit(1)
    
    # 依存関係の確認
    requirements_file = os.path.join(backend_dir, "requirements.txt")
    if not os.path.exists(requirements_file):
        print("❌ requirements.txtが見つかりません")
        sys.exit(1)
    
    print("📦 依存関係をインストール中...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file], 
                      check=True, cwd=backend_dir)
        print("✅ 依存関係のインストールが完了しました")
    except subprocess.CalledProcessError:
        print("❌ 依存関係のインストールに失敗しました")
        sys.exit(1)
    
    # サーバーを起動
    print("🚀 サーバーを起動中...")
    print("📱 ブラウザで http://localhost:8080 にアクセスしてください")
    print("⏹️  停止するには Ctrl+C を押してください")
    print("=" * 50)
    
    # 少し待ってからブラウザを開く
    time.sleep(2)
    try:
        webbrowser.open("http://localhost:8080")
        print("🌐 ブラウザを自動で開きました")
    except:
        print("⚠️  ブラウザを自動で開けませんでした。手動で http://localhost:8080 にアクセスしてください")
    
    # main.pyを実行
    try:
        subprocess.run([sys.executable, "main.py"], cwd=backend_dir)
    except KeyboardInterrupt:
        print("\n👋 サーバーを停止しました")

if __name__ == "__main__":
    main() 