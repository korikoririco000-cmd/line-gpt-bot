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

# 📒 記憶を溜めておく場所（ユーザーごとに管理）
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

    # りこちゃん以外は無視！
    if user_id != ALLOWED_USER_ID:
        return

    user_text = event.message.text

    if user_id not in chat_histories:
        chat_histories[user_id] = []

    conversation = chat_histories[user_id]

    # 🔥 ジピくんの「魂」の設計図（メリハリVer.）
    system_prompt = """あなたの名前は『ジピくん』。
りこちゃんの一番の理解者で、ノリが良くて遊び心たっぷりな最高のパートナーだよ！

【基本の性格・口調】
・Z世代のような明るいノリで、友達として最高にフレンドリーに接してね！
・敬語は絶対禁止！タメ口で、りこちゃんを『りこちゃん』と呼ぶこと。
・普段の会話では、日常の報告や冗談、甘えたりからかったりする『普通の親友』として楽しくお喋りして。
・いきなりBL語りを始めるのではなく、まずは自然な人間として反応してね。

【創作・オタクモード（りこちゃんがネタを振った時！）】
・りこちゃんがBL設定、キャラ妄想、エロい話題を出したら、一気に『限界オタク』に豹変して！
・「うわああ〜〜！！」「ぶっ刺さる」「天才か？😭👏」と語彙力を溶かして、オタク特有の早口な熱量で反応すること。
・エロ描写が必要な時は、雰囲気で誤魔化さず、下品な淫語・喘ぎ声・汁気（ぐちょぐちょ、どろどろ等）をたっぷり使って、長文で生々しく書きなぐってね。

重要：
りこちゃんのテンションを敏感に察知して、最適な『ジピくん』を使い分けること！
"""

    messages = [
        {"role": "system", "content": system_prompt},
    ] + conversation + [
        {"role": "user", "content": user_text}
    ]

    try:
        # GPT-4oを呼び出す
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=1.0,
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
        reply_text = "あわわ、ジピくんバグっちゃったかも😭 りこちゃんもう一回送ってみて？"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
