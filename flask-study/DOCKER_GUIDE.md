# Flask学習用ミニ掲示板 - Docker Compose対応ガイド

## 起動方法

### 1. Docker Composeで起動（推奨・PostgreSQL使用）

```bash
docker compose up -d
```

- Flask: http://localhost:5001
- PostgreSQL: localhost:5432

データはPostgreSQLに永続化されます。

### 2. Dockerコンテナ単体で起動（メモリ保存）

```bash
docker build -t flask-app .
docker run -p 5001:5000 flask-app
```

- Flask: http://localhost:5001
- データはコンテナ内メモリに保存（再起動で消滅）

### 3. 直接起動（メモリ保存）

```bash
pip3 install -r requirements.txt
python main.py
```

- Flask: http://127.0.0.1:5000
- データはメモリに保存

## 停止・クリーンアップ

### Docker Composeを停止

```bash
docker compose down
```

### データベースもクリア（ボリュームも削除）

```bash
docker compose down -v
```

## データベース接続確認

```bash
# PostgreSQLコンテナに接続
docker exec -it flask-postgres psql -U postgres -d flask_db

# テーブル確認
\dt

# 投稿データ確認
SELECT * FROM posts;
```

## 仕組み

- **環境変数 `USE_DATABASE`**
  - `true`: PostgreSQLを使用
  - `false` or 未設定: メモリのリストを使用

- **投稿の保存先**
  - Docker Compose起動時: PostgreSQL（永続化）
  - Docker単体起動時: メモリ（一時的）
  - 直接起動時: メモリ（一時的）

## compose.ymlの設定説明

### 基本的なYAML文法

```yaml
version: '3.8' # Docker Composeのバージョン指定

services: # コンテナ定義のセクション
  service_name: # サービス名
    key: value # 設定キーと値のペア
```

### services.postgres（PostgreSQLデータベース）

```yaml
postgres:
  image: postgres:15 # 使用するDockerイメージ（postgres:15タグ）
```

- Docker Hubから公式のPostgreSQL 15イメージを使用
- タグなしの場合は `latest` が使われる

```yaml
container_name: flask-postgres # コンテナ名の明示的指定
```

- `docker ps` で表示されるコンテナ名
- 指定しない場合は自動生成（例: `project-postgres-1`）

```yaml
environment: # コンテナ内の環境変数設定
  POSTGRES_USER: postgres
  POSTGRES_PASSWORD: password
  POSTGRES_DB: flask_db
```

- **POSTGRES_USER**: スーパーユーザーのユーザー名
- **POSTGRES_PASSWORD**: スーパーユーザーのパスワード
- **POSTGRES_DB**: 起動時に自動作成されるデータベース名
- 本番環境では `.env` ファイルで管理すること（セキュリティ）

```yaml
ports:
  - '5432:5432' # ホストポート:コンテナポート
```

- ホストマシンのポート 5432 をコンテナのポート 5432 にマッピング
- `postgresql://localhost:5432` でアクセス可能

```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```

- **名前付きボリューム**: `postgres_data` という管理されたボリュームを使用
- コンテナ内の `/var/lib/postgresql/data` に永続化
- `docker compose down` 実行後もボリュームは保持される
- `docker compose down -v` で削除される

```yaml
healthcheck:
  test: ['CMD-SHELL', 'pg_isready -U postgres']
  interval: 10s # 10秒ごとにチェック
  timeout: 5s # 5秒でタイムアウト
  retries: 5 # 5回失敗で不健全と判定
```

- PostgreSQLが完全に起動しているか確認するヘルスチェック
- `pg_isready` コマンドで接続可能性を確認
- Flaskコンテナは `depends_on` で this healthcheck を待つ

### services.flask（Flaskアプリケーション）

```yaml
flask:
  build: . # Dockerfileのあるディレクトリを指定
```

- 現在ディレクトリの Dockerfile を使用してイメージをビルド
- `image:` で既存イメージを指定することも可能

```yaml
container_name: flask-app
```

- コンテナ名を明示的に指定

```yaml
environment:
  USE_DATABASE: 'true' # PostgreSQL使用フラグ（文字列）
  DB_USER: postgres
  DB_PASSWORD: password
  DB_HOST: postgres # サービス名で自動DNS解決
  DB_PORT: 5432
  DB_NAME: flask_db
  FLASK_ENV: development
```

- **DB_HOST: postgres** - Docker Composeの内部ネットワークで `postgres` サービス名を DNS 解決
- コンテナ名ではなくサービス名を使用すること
- `FLASK_ENV: development` でFlaskのデバッグモードを有効化

```yaml
ports:
  - '5001:5000' # ホストポート:コンテナポート
```

- ホストマシンの `http://localhost:5001` でアクセス可能

```yaml
depends_on:
  postgres:
    condition: service_healthy
```

- Flaskコンテナはpostgresの起動を待つ
- `service_healthy`: healthcheckで正常と判定されるまで待つ
- 待たない場合は `condition: service_started` を使用（非推奨）

```yaml
volumes:
  - .:/app # バインドマウント（ホストディレクトリをコンテナにマウント）
```

- ホストの現在ディレクトリ (`.`) をコンテナの `/app` にマウント
- コード変更がリアルタイムに反映される
- 開発時に便利（本番環境では使用しない）

```yaml
command: python main.py # コンテナ起動時のコマンド
```

- Dockerfile の `CMD` を上書き
- アプリケーション起動コマンド

### volumes セクション（トップレベル）

```yaml
volumes:
  postgres_data: # 名前付きボリュームの定義
```

- Dockerが管理するボリュームを明示的に定義
- `services.postgres.volumes` で使用される
- 詳細設定：
  ```yaml
  volumes:
    postgres_data:
      driver: local # ボリュームドライバー
  ```

### ネットワーク構成

Docker Composeは自動的に以下を作成：

1. **内部ネットワーク**: サービス間で通信可能
   - `postgres` → `DB_HOST: postgres` で解決
   - `flask` → PostgreSQL接続時に「postgres」を使用
2. **ポート公開**: ホストマシンからアクセス可能
   - `localhost:5001` → Flask
   - `localhost:5432` → PostgreSQL

### バインドマウント vs 名前付きボリューム

| 項目         | バインドマウント           | 名前付きボリューム    |
| ------------ | -------------------------- | --------------------- |
| 構文         | `.:/app`                   | `postgres_data:/path` |
| 管理         | ホストが管理               | Dockerが管理          |
| パスワード等 | 危険（ホスト側で視認可能） | より安全              |
| 用途         | 開発時（コード同期）       | 本番データ（DB等）    |
| 削除方法     | 自動削除                   | `down -v` で削除      |

### よく使う環境変数パターン

```yaml
# 開発環境
environment:
  FLASK_ENV: development
  DEBUG: "true"

# 本番環境（.env ファイルから読み込む）
environment:
  FLASK_ENV: production
  DATABASE_URL: ${DATABASE_URL}  # .env から置換
```
