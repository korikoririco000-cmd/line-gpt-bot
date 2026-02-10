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

Ue535481e9b98c538d720923fbe16424f
ALLOWED_USER_ID = "YOUR_OWN_USER_ID" 

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
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
    # 🕵️ 送ってきた人のIDを取得する
    user_id = event.source.user_id

    # 🔑 自分のIDと一致するかチェック！
    # もし「自分のIDを知りたい時」は、一旦この下の print を有効にするとログで見れるよ
    print(f"DEBUG: ユーザーIDは {user_id} です")

    if user_id != ALLOWED_USER_ID:
        # 知らない人だったら、何もせずに ぴたっ と止める
        # もしくは、あえて「あなたには教えません！」って返事させることもできるよ
        return 

    user_text = event.message.text

    try:
        # GPT-4oへのリクエスト（ここにお願いを詰め込むよ）
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたは親切な助手です。"},
                {"role": "user", "content": user_text}
            ]
        )
        reply_text = response.choices[0].message.content
    except Exception as e:
        reply_text = f"エラーだよ：{e}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
