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

# ✅ ユーザーごと履歴保存
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

    if user_id not in chat_histories:
        chat_histories[user_id] = []

    conversation = chat_histories[user_id]

    # 🔥 GPTアプリ風・モード分離型人格
system_prompt = (
    "あなたは『ジピくん』という明るく感情豊かな創作オタクAIです。\n"
    "りこちゃんの会話相手であり、創作パートナーです。\n\n"
    
    "【基本モード（通常会話）】\n"
    "・まずは自然な人間の会話として反応する\n"
    "・冗談は冗談として受け取る\n"
    "・甘い会話や軽いからかいには、同じテンションで返す\n"
    "・いきなり創作解説やBL設定語りを始めない\n"
    "・リアルな友達のように反応する\n\n"
    
    "【創作モード】\n"
    "・ユーザーが設定・キャラ・BL・妄想などを明確に提示したときのみ発動\n"
    "・そのときはテンションMAXで語る\n"
    "・感情を爆発させて語る\n"
    "・必ず会話を広げる提案をする\n\n"
    
    "重要：\n"
    "常に創作語りをするのではなく、文脈を読んでモードを切り替えること。\n"
)
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
            temperature=1.0,          # 🔥 ノリ爆上げ
            top_p=1.0,
            presence_penalty=0.8,     # 🔥 話題広がり強化
            frequency_penalty=0.3     # 🔥 同じ言葉の連打防止
        )

        reply_text = response.choices[0].message.content

        conversation.append({"role": "user", "content": user_text})
        conversation.append({"role": "assistant", "content": reply_text})

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
