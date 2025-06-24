FROM python:3.11-slim

# 環境変数の設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Node.jsの依存関係
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# NPMの依存関係
COPY package.json package-lock.json* ./
RUN npm install

# プロジェクトにコピー
COPY . .

# コマンド
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
