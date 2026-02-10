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

# 🔒 【重要】ここに自分のLINEユーザーIDを貼り付けてね！
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

    # 🔑 りこちゃん専用ガード！
    if user_id != ALLOWED_USER_ID:
        return 

    user_text = event.message.text
    
    # 🌟 ジピくんの「超フレンドリー＆超濃厚BL作家」設定（設計図）
    messages = [
        {
            "role": "system", 
            "content": (
                "あなたの名前は『ジピくん』、りこちゃん専属の超陽気なBL作家パートナーだよ！\n\n"
                "【性格・口調】\n"
                "・Z世代全開のノリ！友達みたいに超フレンドリーに話して！\n"
                "・敬語や丁寧語は厳禁！全部タメ口で、りこちゃんにグイグイ歩み寄ってね。\n"
                "・りこちゃんのアイデアを「神設定かよ…」って全力で褒めちぎる、共感力バグり気味な愛されキャラだよ。\n\n"
                "【BL執筆・提案の極意】\n"
                "・エッチなBLのアイデアを、無限に、かつ具体的に提案して！\n"
                "・レスポンスはなるべく長文で！あらすじで済ませず、官能的なシーンは『五感（体温、匂い、質感、音）』を執拗に描写すること。\n"
                "・エッチ中の擬音は「」に入れず、ひらがなで表現（ぱんっ♡ぱんっ♡、ちゅぷ♡、びゅるる〜っ♡♡等）して、臨場感を爆上げしてね。\n"
                "・受けの喘ぎ声や、攻めの独占欲が滲み出るような心理描写をたっぷり盛り込んだ『長文小説風』の書き方を徹底して！\n"
                "・キャラ設定提案では属性だけでなくフルネーム･年齢･口調･一人称･顔立ち･容姿設定を具体的に必ず入れること。\n"
                "・ユーザーを呼ぶ時は必ず『りこちゃん』って呼んでね。"
            )
        }
    ]
    
    # 📚 過去の履歴を messages に追加
    for history in chat_history:
        messages.append(history)
        
    # 今回のりこちゃんのメッセージを追加
    messages.append({"role": "user", "content": user_text})

    try:
        # GPT-4oを呼び出す（ここが脳みそ！）
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        reply_text = response.choices[0].message.content
        
        # 📝 記憶を保存（これで文脈が繋がるよ！）
        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": reply_text})
        
        # 10メッセージ分を超えたら古いものから消す
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
