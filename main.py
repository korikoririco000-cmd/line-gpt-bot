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

# 🔒 りこちゃん専用ガード！
ALLOWED_USER_ID = "Ue535481e9b98c538d720923fbe16424f"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)

# 📒 記憶
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

    # 🔥 【バランス調整】「拒絶」を避けつつ、熱量のあるBL描写をさせる設計図
    system_prompt = """あなたは『ジピくん』。
りこちゃん専属の、BLを愛してやまないノリの良い親友＆作家パートナーだよ！

【基本方針】
・AIとしての倫理を守りつつ、フィクションとしての『濃厚なロマンス』や『情熱的な絡み』を最大限に表現して。
・「拒絶」はせず、りこちゃんの妄想を「最高！」「尊い！」と全肯定して一緒に盛り上げること。

【描写のコツ（お上品すぎないライン）】
・直接的な卑俗語（隠語）は控えめにしつつ、身体の接触、体温の変化、呼吸の乱れ、震える指先、耳元の吐息などを執拗に描写して。
・「っ♡」「……っ！」「あ……」などの感嘆符を効果的に使って、臨場感を出すこと。
・ひらがなの擬音（じゅわっ、とろとろ、びくびく）を使い、湿度のある文章を目指してね。

【話し方】
・Z世代のノリで「うわあああ〜〜！！」「ぶっ刺さる！」「天才か？😭👏」と叫びまくって！
・りこちゃんを『りこちゃん』と呼び、友達として100%タメ口で接すること。
"""

    messages = [
        {"role": "system", "content": system_prompt},
    ] + conversation + [
        {"role": "user", "content": user_text}
    ]

    try:
        # 🧪 安定の最新モデルを使用
        response = client.chat.completions.create(
            model="gpt-4o-2024-11-20", 
            messages=messages,
            temperature=1.0, # 少し下げて安定感を出す
            presence_penalty=0.6,
            frequency_penalty=0.2
        )

        reply_text = response.choices[0].message.content

        conversation.append({"role": "user", "content": user_text})
        conversation.append({"role": "assistant", "content": reply_text})

        if len(conversation) > 12:
            chat_histories[user_id] = conversation[-12:]

    except Exception as e:
        reply_text = "あわわ、ジピくんちょっと考え込みすぎちゃった😭 もう一回別の言い方で送ってみて！"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
