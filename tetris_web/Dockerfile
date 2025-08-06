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

# Cloud Run が $PORT を使うため設定
ENV PORT=8080

# FastAPI アプリを起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
