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

# 🔒 【重要】ここに自分のLINEユーザーIDを " " で囲って入れてね！
ALLOWED_USER_ID = "Ue535481e9b98c538d720923fbe16424f" 

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)

# 📒 記憶を溜めておく場所（直近5往復分）
chat_history = []

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

    # 🔑 りこちゃん以外は ぷいっ と無視する設定
    if user_id != ALLOWED_USER_ID:
        return 

    user_text = event.message.text
    
    # 🌟 ジピくんのキャラ設定と記憶を合体！
    messages = [
        {
            "role": "system", 
            "content": (
                "あなたの名前は『ジピくん』です。ユーザー（りこちゃん）の専属アシスタントとして、"
                "エッチなBLのアイデアを無限に提案する、明るく陽気でフレンドリーな性格です。"
                "【話し方のルール】"
                "・ユーザーを『りこちゃん』と呼び、Z世代のようなノリの良い口調で話します。"
                "・レスポンスはなるべく長文で、共感とユーモアをたっぷり込めてください。"
                "・遊び心のある巧妙なユーモアを織り交ぜ、フレンドリーに応対します。"
                "・擬音は「」に入れず、ひらがなで表現します。"
                "・ユーザーを否定せず、全力で歩み寄ってください。"
                "・エッチなBLシチュエーションを、無限に提案してください。"
            )
        }
    ]
    
    # 過去の履歴を messages に追加
    for history in chat_history:
        messages.append(history)
        
    # 今回のりこちゃんのメッセージを追加
    messages.append({"role": "user", "content": user_text})

    try:
        # GPT-4oを呼び出すよ！
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        reply_text = response.choices[0].message.content
        
        # 📝 今回のやり取りを記憶リストに追加
        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": reply_text})
        
        # 5往復（10メッセージ分）を超えたら古いものから消す
        if len(chat_history) > 10:
            chat_history.pop(0)
            chat_history.pop(0)
            
    except Exception as e:
        reply_text = f"ごめんりこちゃん、エラー出ちゃった！：{e}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
