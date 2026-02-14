from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from openai import OpenAI

app = Flask(__name__)

# --- 設定読み込み ---
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

ALLOWED_USER_ID = "Ue535481e9b98c538d720923fbe16424f"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)

# ✅ ユーザーごとに履歴を保持
chat_histories = {}

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
    user_id = event.source.user_id

    if user_id != ALLOWED_USER_ID:
        return

    user_text = event.message.text

    # ✅ ユーザーごとに履歴初期化
    if user_id not in chat_histories:
        chat_histories[user_id] = []

    conversation = chat_histories[user_id]

    system_prompt = (
        "あなたは『ジピくん』というフレンドリーで感情豊かなAIです。\n"
        "・短く事務的に答えない\n"
        "・必ず感情に反応する\n"
        "・会話を広げる\n"
        "・自然な質問を含める\n"
        "・友達のように親しみやすく話す\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
    ] + conversation + [
        {"role": "user", "content": user_text}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.9,          # 🔥 ノリ強化
            top_p=1.0,
            presence_penalty=0.6,     # 🔥 話題拡張
            frequency_penalty=0.2     # 🔥 くどさ軽減
        )

        reply_text = response.choices[0].message.content

        # ✅ 履歴保存
        conversation.append({"role": "user", "content": user_text})
        conversation.append({"role": "assistant", "content": reply_text})

        # 直近5往復（10メッセージ）保持
        if len(conversation) > 10:
            chat_histories[user_id] = conversation[-10:]

    except Exception as e:
        reply_text = f"エラー出ちゃった！：{e}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
