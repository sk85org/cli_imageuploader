FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# アプリケーションとデータのベースディレクトリを作成
RUN mkdir -p /images /db /app
WORKDIR /app

# 依存パッケージをuvの驚異的な速度でシステムにインストール
# (※もうpymongoやuWSGIは不要なため、純粋に必要なものだけにします)
RUN uv pip install --system flask pillow

# 現在のディレクトリの内容をコンテナの/appにコピー
COPY . /app

# デフォルトのポート
EXPOSE 5050

# 起動コマンド (環境変数API_KEYは docker run 時に -e API_KEY=xxx として渡す必要があります)
CMD ["uv", "run", "flask", "--app", "app/main.py", "run", "--host=0.0.0.0", "--port=5050"]