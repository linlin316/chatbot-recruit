#  採用向けAIチャットボット (Flask + Claude API)

企業の採用サイト向けに作成したシンプルなAIチャットボットです。  
求職者からの質問に対して、FAQを優先して回答し、必要な場合のみClaude APIを利用します。

## 主な機能

- FAQ優先回答（APIコスト削減）
- Claude APIによるAI回答
- 簡易安全フィルター（不適切な質問の制御）
- チャットUI（Webページ上のチャットボックス）
- ボタンによる質問ガイド
- 未命中質問の記録・管理スクリプト

## 使用技術

- Python
- Flask
- Claude API (Anthropic)
- SQLite
- JavaScript
- HTML / CSS

## ディレクトリ構成

```text
app/
├── services/
│   ├── chat_service.py   # チャット処理フロー
│   ├── faq.py            # FAQ照合ロジック（キャッシュあり）
│   ├── greeting.py       # あいさつ検知・除去
│   ├── llm_claude.py     # Claude API呼び出し
│   └── safety.py         # 入力の正規化・ブロック判定
│
├── static/
│   ├── chatbot.js        # チャットUI（フロントエンド）
│   └── style.css
│
├── templates/
│   └── index.html
│
├── config.py             # 各種設定値
├── db.py                 # DB接続・テーブル初期化
└── routes.py             # APIエンドポイント

init_db.py                # 初回のみ実行：DB初期化＋FAQデータ投入
manage_faq.py             # 未命中質問の確認・FAQ同義語追加
check_db.py               # DB内容の確認
run.py                    # アプリ起動エントリーポイント
requirements.txt
```

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定

`.env.example` を参考に `.env` ファイルを作成します。

```env
ANTHROPIC_API_KEY=your_api_key_here
```

> `.env` は Git にコミットされません。

### 3. DB初期化とFAQデータ投入（初回のみ）

```bash
python init_db.py
```

### 4. アプリ起動

```bash
python run.py
```

### 5. ブラウザで確認

```
http://127.0.0.1:5000
```

## FAQ管理

FAQに命中しなかった質問は `data/chatbot.db` の `unanswered` テーブルに記録されます。  
以下のスクリプトで確認・管理できます。

```bash
# 未命中質問の一覧確認
python check_db.py

# 未命中質問をFAQの同義語に追加（対話式）
python manage_faq.py
```
