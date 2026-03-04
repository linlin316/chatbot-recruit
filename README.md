# 採用向けAIチャットボット (Flask + Claude API)

企業の採用サイト向けに作成したシンプルなAIチャットボットです。  
求職者からの質問に対して、FAQを優先して回答し、必要な場合のみClaude APIを利用します。

## 主な機能

- FAQ優先回答（APIコスト削減）
- Claude APIによるAI回答
- 簡易安全フィルター（不適切な質問の制御）
- チャットUI（Webページ上のチャットボックス）
- ボタンによる質問ガイド

## 使用技術

- Python
- Flask
- Claude API (Anthropic)
- JavaScript
- HTML / CSS

## Project Structure

```text
app/
├ services/
│ ├ chat_service.py
│ ├ faq.py
│ ├ greeting.py
│ ├ llm_claude.py
│ └ safety.py
│
├ static/
│ ├ chatbot.js
│ └ style.css
│
├ templates/
│ └ index.html
│
├ config.py
└ routes.py

run.py
requirements.txt

```
## セットアップ

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定
```bash
.env.example を参考に .env ファイルを作成します。
ANTHROPIC_API_KEY=your_api_key_here

※ .env は Git にアップロードされません。
```

### 3. アプリ起動
```bash
python run.py
```

### 4.ブラウザで以下を開きます。
```bash
http://127.0.0.1:5000
```
