from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from openai import OpenAI

app = Flask(__name__)

# Railwayの「Variables」から設定を読み込むよ
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 必要な設定が足りないときはエラーを出すよ
if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN or not OPENAI_API_KEY:
    raise ValueError("Environment variables missing!")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# OpenAIの窓口（クライアント）を準備するよ
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    # ここから下がGPT-4oにお願いする部分だよ
    try:
        # 1. GPT-4oに返答を考えてもらう
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_text}]
        )
        # 2. 返ってきた言葉を取り出す
        reply_text = response.choices[0].message.content
        
    except Exception as e:
        # もし何かエラー（お金足りないとか）が起きたらLINEに表示するよ
        reply_text = f"エラーが発生しました：{e}"

    # 3. LINEに返信を送る
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    # Railwayで動かすための設定だよ
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
