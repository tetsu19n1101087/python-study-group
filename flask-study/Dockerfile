# Python 3.11 の公式イメージを使用
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存パッケージのインストール
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# アプリケーションをコピー
COPY . .

# 環境変数を設定（Docker環境であることを示す）
ENV DOCKER_ENV=true
ENV FLASK_APP=main.py

# ポート5000を公開
EXPOSE 5000

# アプリケーションを起動
CMD ["python", "main.py"]
