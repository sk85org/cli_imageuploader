# Local Image Uploader API

軽量でセキュアなローカル向けの画像アップロード用APIサーバーです。
`curl` などのCLIツールからの操作を前提に設計されており、データベースはSQLiteを使用し、無駄のない構成となっています。

## ⚙️ 環境構築・起動方法

サーバーはFlaskで実装されています。Python環境（uv等）が整っている状態で実行してください。

### サーバーの起動
セキュリティのため、起動時に**必ず `API_KEY` を環境変数として設定**する必要があります。
また、Macなどではポート重複（AirPlayレシーバーとの衝突）を避けるため `--port=5050` など別のポートを指定することを推奨します。

```bash
# プロジェクト直下（imageuploaderディレクトリ）で実行
API_KEY="your-secret-key" uv run flask --app app/main.py run --debug --port=5050
```

### 📁 データ保存先
サーバーを起動または操作すると、自動的にプロジェクト直下に以下のディレクトリが作成されます。

*   `image/`: 実際の画像ファイルが保存されるディレクトリ
*   `db/images.db`: メタデータ（ファイル名、ID）を管理するSQLiteデータベース

---

## 🔒 セキュリティ
データの変更操作（画像のアップロード・画像の削除）には、**APIキー認証**が必要です。
対象のエンドポイントに対してリクエストを送信する際は、必ずHTTPヘッダーに `x-api-key: <設定したAPIキー>` を含めてください。
含めなかった場合や一致しない場合は、`401 Unauthorized` が返却されます。

---

## 🚀 API エンドポイント 一覧

### 1. サーバー状態確認 (GET)
サーバーが正常に起動しているかを確認するための軽量なルートです。APIキーは不要です。

*   **URL:** `GET /`
*   **認証:** 不要
*   **レスポンス例:** `running`
*   **CURL例:**
    ```bash
    curl http://localhost:5050/
    ```

### 2. 画像検索・一覧取得 (GET)
アップロードされた画像の一覧を取得します。ファイル名の部分一致検索が可能です。APIキーは不要です。

*   **URL:** `GET /api/search`
*   **認証:** 不要
*   **クエリパラメータ:**
    *   `filename=文字` (オプション): ファイル名に含まれる文字列で絞り込みます。（例: `202603` で年月指定検索）
*   **レスポンス例 (200 OK):**
    ```json
    {
      "results": [
        {
          "_id": "1",
          "filename": "20260322-14-41-52-randomstring15chars.jpg"
        }
      ],
      "total": 1
    }
    ```
*   **CURL例:**
    ```bash
    curl "http://localhost:5050/api/search?filename=2026"
    ```

### 3. 画像のアップロード (POST)
画像をサーバー(`image/`)にアップロードし、DBに登録します。
セキュリティと画質維持のため、プライバシー情報（EXIF等の位置情報）は自動的に削除された上で保存されます。また、ファイル名はアップロード日時に基づいてサーバー側で安全な名前にリネームされます。

*   **URL:** `POST /api/upload`
*   **認証:** **必要** (`x-api-key` ヘッダー)
*   **対応フォーマット:** `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`
*   **パラメータ:**
    *   `file`: 画像ファイルの実体 (form-data形式)
*   **レスポンス例 (200 OK):**
    ```json
    {
      "message": "File uploaded successfully",
      "filename": "20260322-14-41-52-randomstring15chars.jpg",
      "_id": "1"
    }
    ```
*   **CURL例:**
    ```bash
    curl -H "x-api-key: your-secret-key" -X POST -F "file=@/path/to/image.jpg" http://localhost:5050/api/upload
    ```

### 4. 画像の削除 (DELETE)
データベース上のレコードと、ディスク上の実際の画像ファイルの両方を完全に削除します。

*   **URL:** `DELETE /api/images/<id>`
*   **認証:** **必要** (`x-api-key` ヘッダー)
*   **パスパラメータ:**
    *   `<id>`: 削除したい画像のID (GET /api/search で取得した `_id` 等)
*   **レスポンス例 (200 OK):**
    ```json
    {
      "message": "Image 20260322-14-41-52-randomstring15chars.jpg deleted successfully",
      "id": "1"
    }
    ```
*   **CURL例:**
    ```bash
    curl -H "x-api-key: your-secret-key" -X DELETE http://localhost:5050/api/images/1
    ```
