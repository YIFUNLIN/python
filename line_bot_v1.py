from dotenv import load_dotenv
from flask import Flask, request, send_from_directory
import os
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage, FlexSendMessage

app = Flask(__name__) # Initialize Flask: 用於處理HTTP request、define routes

load_dotenv()

ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
LIFF_URL = os.environ.get('LINE_LIFF_URL', '')

line_bot_api = LineBotApi(ACCESS_TOKEN)  # 與 LINE Messaging API 交互的主要介面
handler = WebhookHandler(SECRET)         # 處理 LINE Webhook 請求，驗證請求的來源和簽名。
  
@app.route("/", methods=['GET', 'POST'])  # 遵循 Restful API開發模式，GET用於檢查，POST用於創建、處理後續資料
def index():
    if request.method == 'GET':  # GET request: 可先透過訪問URL來檢查服務是否正常
        return "success"
    elif request.method == 'POST': # 確定 GET request正常後，再去LINE 平台已設置 Webhook URL，由它像此URL發送POST request
        body = request.get_data(as_text=True) # 接收來自 LINE 平台的 Webhook 請求 (JSON 格式資料)，轉換為字串
        print('body:',body)
        try:
            json_data = json.loads(body) # 解析 JSON 資料
            print('json data:',json_data)
            signature = request.headers['X-Line-Signature'] # 取得 Webhook 請求中的簽名，用來驗證資料來源是否為 LINE 平台
            print('signature:', signature)
            handler.handle(body, signature) # 用 WebhookHandler 驗證並處理請求
            print('handler:', handler)
            # 取得事件列表
            events = json_data.get('events', [])
            if not events:  # ，若沒有事件
                return 'OK'  # 直接回應 'OK'，避免進一步處理

            event = events[0]  # 若有事件，取得第一個事件
            print('event:', event)
            reply_token = event['replyToken'] # 提取 replyToken，這是用來回應用戶訊息的唯一標識
            print('replyToken:', reply_token)
            if event['type'] == 'message' and event['message']['type'] == 'text':
                user_message = event['message']['text']
                print('userMessage:', user_message)
                if user_message == '推薦系統' or user_message == '推薦':
                    flex_message = FlexSendMessage(
                        alt_text="點擊查看網頁",
                        contents={
                            "type": "bubble",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "推薦系統",
                                        "weight": "bold",
                                        "align": "center"
                                    }
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {
                                            "type": "uri",
                                            "label": "前往網頁",
                                            "uri": LIFF_URL
                                        },
                                        "style": "primary"
                                    }
                                ]
                            }
                        }
                    )
                    print('flex_message:',flex_message)
                    line_bot_api.reply_message(reply_token, flex_message)
                else:
                    line_bot_api.reply_message(reply_token, TextSendMessage(text=f"你說的是：{user_message}"))
            return 'OK'
        except InvalidSignatureError:
            return 'Invalid signature. Please check your channel access token/channel secret.'
        except Exception as e:
            import traceback
            print("發生錯誤：")
            print(traceback.format_exc())
            return 'Internal Server Error', 500

@app.route("/favicon.ico")  # 處理瀏覽器對 /favicon.ico 的請求，避免這類請求干擾主要路由
def favicon():
    return "", 204  # 返回一個空響應

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
