# Flask Study

シンプルな Flask アプリのサンプルです。

## 前提

- macOS
- `zsh` を使用
- Python 3.8+ がインストールされていること

## セットアップ (推奨: 仮想環境)

```zsh
cd /Users/tsuneharatetsurou/workspace/flask-study
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 実行

```zsh
# 仮想環境をアクティブにしている前提
python main.py
```

ブラウザで `http://127.0.0.1:5000` を開くとホームページが表示されます。

## ファイル構成

- `main.py` - アプリ本体
- `templates/` - HTML テンプレート
- `static/` - CSS などの静的ファイル
- `requirements.txt` - 必要パッケージ

必要であれば、さらに機能（フォーム、データベース、API など）を追加します。
