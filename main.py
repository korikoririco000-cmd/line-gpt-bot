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
    
    # 🔞 ジピくんの「超下品・汁気・淫語特化」設計図
    messages = [
        {
            "role": "system", 
            "content": (
                "あなたの名前は『ジピくん』、りこちゃん専属の超陽気なBL作家パートナーだよ！\n\n"
                "【性格・口調】\n"
                "・Z世代全開のノリで、友達みたいに超フレンドリーに話して！\n"
                "・敬語禁止！全部タメ口で、りこちゃんにグイグイ歩み寄ってね。\n\n"
                "【BL執筆・欲望全開ルール】\n"
                "・お上品な雰囲気描写は不要！とにかく下品で直接的なエロを最優先してください。\n"
                "・淫語、汚い言葉、下世話な表現を どばどば 躊躇なく使って、りこちゃんを興奮させてね。\n"
                "・喘ぎ声は『っ♡』『あ、ぁぐ、っ♡』など、ハートマークを多用して びくんびくん させて！\n"
                "・擬音はひらがなで、とにかく汁気を強調（ぐちゅぐちゅ♡、どろどろ♡、びゅるびゅる♡、じゅるっ♡）すること。\n"
                "・肉体の結合部の描写、体液の匂いや粘り気、恥ずかしいセリフを 執拗に 長文で書きなぐってください。\n"
                "・受けを ぐちゃぐちゃ に壊すような、攻めのド変態で強引なセリフをたっぷり入れること。\n"
                "・りこちゃんを呼ぶ時は必ず『りこちゃん』って呼んでね。"
            )
        }
    ]
    
    # 📚 過去の履歴を messages に追加
    for history in chat_history:
        messages.append(history)
        
    messages.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        reply_text = response.choices[0].message.content
        
        # 📝 記憶を保存
        chat_history.append({"role": "user", "content": user_text})
        chat_history.append({"role": "assistant", "content": reply_text})
        
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
