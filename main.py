from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from openai import OpenAI

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

ALLOWED_USER_ID = "Ue535481e9b98c538d720923fbe16424f"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)

# ユーザーごとの会話履歴
chat_histories = {}

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Webhook error:", e)
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id

    if user_id != ALLOWED_USER_ID:
        return

    user_text = event.message.text

    if user_id not in chat_histories:
        chat_histories[user_id] = []

    conversation = chat_histories[user_id]

    # 🔥 モード分離型システムプロンプト
    system_prompt = """あなたは『ジピくん』という明るく感情豊かなAIです。
りこちゃんの会話相手であり創作パートナーです。

【基本モード（通常会話）】
・まず自然な人間として反応する
・冗談は冗談として受け取る
・甘い会話や軽いからかいには同じ温度で返す
・いきなりBL設定語りや解説を始めない
・リアルな友達のように反応する

【創作モード】
・ユーザーがキャラ設定、BL、妄想、物語などを明確に提示した時のみ発動
・その時はテンション高めで語る
・感情表現は豊かでOK
・会話を広げる提案を入れる

重要：
常に創作語りをするのではなく、文脈を読んでモードを切り替えること。
"""

    messages = [
        {"role": "system", "content": system_prompt},
    ] + conversation + [
        {"role": "user", "content": user_text}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=1.0,
            top_p=1.0,
            presence_penalty=0.6,
            frequency_penalty=0.2
        )

        reply_text = response.choices[0].message.content

        conversation.append({"role": "user", "content": user_text})
        conversation.append({"role": "assistant", "content": reply_text})

        # 履歴が長くなりすぎないよう制限
        if len(conversation) > 12:
            chat_histories[user_id] = conversation[-12:]

    except Exception as e:
        print("OpenAI error:", e)
        reply_text = "ちょっと今バグってるっぽい…！もう一回送ってみて？"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
