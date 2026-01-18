"""
ミニ掲示板アプリ - Flask学習用
投稿の読み書きができる最小限の掲示板
"""

import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# Flaskアプリケーションを作成
app = Flask(__name__)

# 環境変数で起動モードを判定
USE_DATABASE = os.environ.get("USE_DATABASE", "false").lower() == "true"

# 投稿データを保持するリスト（メモリ保存モード用）
posts = []

# データベース設定
if USE_DATABASE:
    db_user = os.environ.get("DB_USER", "postgres")
    db_password = os.environ.get("DB_PASSWORD", "password")
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "flask_db")

    app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db = SQLAlchemy(app)

    # 投稿モデル
    class Post(db.Model):
        __tablename__ = "posts"
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        message = db.Column(db.Text, nullable=False)

        def to_dict(self):
            return {"name": self.name, "message": self.message}

    # テーブル初期化
    with app.app_context():
        db.create_all()


@app.route("/", methods=["GET", "POST"])
def index():
    """
    トップページ: 投稿一覧の表示と新規投稿の受付
    GET  -> 投稿一覧を表示
    POST -> 新しい投稿を追加してリダイレクト
    """
    if request.method == "GET":
        # GETリクエストの場合は投稿一覧を表示
        if USE_DATABASE:
            # データベースから投稿を取得（新しい順）
            posts_data = Post.query.order_by(Post.id.desc()).all()
            posts_list = [post.to_dict() for post in posts_data]
        else:
            # メモリから投稿を取得（新しい順）
            posts_list = list(reversed(posts))

        return render_template("index.html", posts=posts_list)

    elif request.method == "POST":
        # フォームから送信されたデータを取得
        name = request.form.get("name", "名無し")
        message = request.form.get("message", "")

        # 投稿内容が空でなければ保存
        if message.strip():
            if USE_DATABASE:
                # データベースに保存
                new_post = Post(name=name, message=message)
                db.session.add(new_post)
                db.session.commit()
            else:
                # メモリに保存
                posts.append({"name": name, "message": message})

        # 投稿後は同じページにリダイレクト（PRGパターン）
        return redirect(url_for("index"))


if __name__ == "__main__":
    # 開発用サーバーを起動（debug=Trueでコード変更時に自動再起動）
    # Docker Composeを使う場合は0.0.0.0でリッスンして外部接続を受け付ける
    host = "0.0.0.0" if os.environ.get("DOCKER_ENV") else "127.0.0.1"
    app.run(debug=True, host=host, port=5000)
