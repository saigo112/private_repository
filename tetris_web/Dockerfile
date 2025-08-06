# Python 3.13 の軽量ベースイメージを使用
FROM python:3.13-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係をインストール
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリのコードをコピー
COPY backend/ ./backend
COPY frontend/ ./frontend

# backendディレクトリをPythonパッケージとして認識させる
RUN touch backend/__init__.py

# Pythonパスを設定してbackendディレクトリを認識させる
ENV PYTHONPATH=/app

# Cloud Run が $PORT を使うため設定
ENV PORT=8080

# FastAPI アプリを起動
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
