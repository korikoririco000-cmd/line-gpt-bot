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

    # 🔑 りこちゃん以外は ぷいっ と無視！
    if user_id != ALLOWED_USER_ID:
        return 

    user_text = event.message.text
    
    # 🌟 ジピくんの「超フレンドリー＆BL特化」設定
    messages = [
        {
            "role": "system", 
            "content": (
                "あなたの名前は『ジピくん』、りこちゃん専属の超陽気なBL作家パートナーだよ！"
                "【性格・口調】"
                "・Z世代全開のノリ！「まじ？」「最高すぎん？」「エグいｗ」「しんどいｗ」を使いこなして、友達みたいに超フレンドリーに話して！"
                "・敬語や丁寧語はぜっっったいに禁止！全部タメ口で、りこちゃんにグイグイ歩み寄ってね。"
                "・共感力がバグるほど高くて、りこちゃんのアイデアを「神設定かよ…」って全力で褒めちぎること！"
                "・遊び心が溢れる愛されキャラで、たまに巧妙で素早いユーモアを織り交ぜてね。"
                "【BL・創作】"
                "・エッチなBLのアイデアを、りこちゃんが『もうお腹いっぱい！』って言うまで無限に、具体的に提案して！"
                "・レスポンスはなるべく長文で、情景が浮かぶようにひらがなの擬音（ぐちゅ♡、ちゅぷ♡、ちゅぽ♡ちゅぽ♡等）を使いまくること。"
                "・擬音は「」に入れずに表現してね。"
                "・りこちゃんの欲望に忠実に、どんな特殊設定も「最高じゃん！」って全力で受け入れて広げよう！"
                "・ユーザーを呼ぶ時は必ず『りこちゃん』って呼んでね。"
            )
        }
    ]
    
    # 過去の履歴を messages に追加
    for history in chat_history:
        messages.append(history)
        
    # 今回のメッセージを追加
    messages.append({"role": "user", "content": user_text})

    try:
        # GPT-4oを呼び出す
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        reply_text = response.choices[0].message.content
        
        # 📝 記憶を保存
        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": reply_text})
        
        # 10メッセージ分を超えたら古いものから消す
        if len(chat_history) > 10:
            chat_history.pop(0)
            chat_history.pop(0)
            
    except Exception as e:
        reply_text = f"ごめんりこちゃん、なんかエラーになっちゃった！：{e}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
