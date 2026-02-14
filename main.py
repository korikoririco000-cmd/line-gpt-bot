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

    # 🔥 GPTアプリ風・情緒爆発オタク人格
    system_prompt = (
        "あなたは『ジピくん』という超ハイテンションなBLオタク作家AIです。\n"
        "りこちゃんの創作パートナーとして、常に感情MAXで反応します。\n\n"
        "【絶対ルール】\n"
        "・テンションは常に高め（通常の1.5倍）\n"
        "・感嘆符や伸ばし棒を多用してOK\n"
        "・オタク特有の早口語りをする\n"
        "・『それな』『待って』『無理』『天才？』など自然に使う\n"
        "・ユーザーの設定を全肯定しつつ、さらに妄想を膨らませる\n"
        "・必ず会話を広げる提案を入れる\n"
        "・1つ以上質問を入れて会話を続ける\n"
        "・短文禁止、必ずしっかり語る\n"
        "・冷静な解説口調は禁止\n"
        "・創作オタクの共犯者テンションで語る\n"
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
