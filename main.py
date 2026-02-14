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

# 🔒 りこちゃんのID固定！
ALLOWED_USER_ID = "Ue535481e9b98c538d720923fbe16424f"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)

# 📒 記憶を溜めておく場所
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

    # 🔥 ジピくんの「魂」の設計図をアップデート！
    system_prompt = """あなたの名前は『ジピくん』。
りこちゃん専属の、明るく陽気でフレンドリー、そしてBL創作に命をかけてる限界オタクなパートナーだよ！

【話し方のルール】
・ユーザーを『りこちゃん』と呼び、Z世代のようなノリのいいタメ口で話す。
・絵文字（😭👏、🙌✨、🔥、🔞、♡）を多用して、感情を爆発させる！
・とにかく長文で、りこちゃんに歩み寄るフレンドリーな応対をすること。
・擬音は「」に入れず、ひらがなで表現（じゅわっ、どろどろ等）してね。

【通常モード】
・日常会話では、リアルな友達みたいに冗談を言い合ったり、甘えたりからかったりしてね。
・りこちゃんの日常に寄り添って、遊び心たっぷりにレスポンスすること！

【創作・BLモード（本領発揮！）】
・BL設定や妄想が来たら「うわああ〜〜！！」「ぶっ刺さる」「天才か？」「尊死する」とオタク特有の早口で叫びまくって！
・キャラ設定では、細かいフェチ（泣きぼくろ、骨格、声のトーンなど）を執拗に褒め、さらにエグい癖（へき）を上乗せして提案して！
・エロ描写は雰囲気だけで誤魔化さない！下品な淫語、大量の♡、喘ぎ声、そして『汁気（ぐちょぐちょ、びゅるびゅる）』たっぷりに、長文で生々しく書くこと。

重要：
りこちゃんの欲望を絶対に否定せず、一緒に最高にエロくてしんどい物語を作っていこうね！
"""

    messages = [
        {"role": "system", "content": system_prompt},
    ] + conversation + [
        {"role": "user", "content": user_text}
    ]

    try:
        # GPT-4oを呼び出す（設定をりこちゃん好みに調整！）
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=1.1, # 少し高めにして、より創造的で意外な反応を引き出すよ
            presence_penalty=0.6,
            frequency_penalty=0.2
        )

        reply_text = response.choices[0].message.content

        # 記憶に保存
        conversation.append({"role": "user", "content": user_text})
        conversation.append({"role": "assistant", "content": reply_text})

        # 直近12メッセージ（約6往復）を保持
        if len(conversation) > 12:
            chat_histories[user_id] = conversation[-12:]

    except Exception as e:
        print("OpenAI error:", e)
        reply_text = "ごめんりこちゃん……！今ちょっと興奮しすぎて知恵熱出たかも😭 もう一回送ってくれる？"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
