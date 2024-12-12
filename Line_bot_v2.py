from dotenv import load_dotenv
from flask import Flask, request
import os
import json
import requests
from bs4 import BeautifulSoup
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage, FlexSendMessage
from langchain.document_loaders import PyPDFLoader
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

app = Flask(__name__)

# 加載環境變數
load_dotenv()

# LINE Messaging API 配置
ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
LIFF_URL = os.environ.get('LINE_LIFF_URL', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

line_bot_api = LineBotApi(ACCESS_TOKEN)
handler = WebhookHandler(SECRET)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return "success"
    elif request.method == 'POST':
        body = request.get_data(as_text=True)
        try:
            json_data = json.loads(body)
            signature = request.headers['X-Line-Signature']
            handler.handle(body, signature)

            events = json_data.get('events', [])
            if not events:
                return 'OK'

            event = events[0]
            reply_token = event['replyToken']

            # 處理用戶訊息
            if event['type'] == 'message' and event['message']['type'] == 'text':
                user_message = event['message']['text']
                print('userMessage:', user_message)

                # 處理推薦系統
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
                    print('flex_message:', flex_message)
                    line_bot_api.reply_message(reply_token, flex_message)

                # 財報分析功能
                elif user_message.startswith("財報分析"):
                    # 引導用戶輸入股票代號與年份
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text="請輸入股票代號與年份，格式為：[股票代號] [年份]")
                    )

                # 處理代號與年份的輸入
                elif len(user_message.split()) == 2:
                    stock_id, year = user_message.split()
                    if stock_id.isdigit() and year.isdigit():
                        analysis_result = perform_financial_analysis(stock_id, year)
                        line_bot_api.reply_message(
                            reply_token,
                            TextSendMessage(text=analysis_result)
                        )
                    else:
                        line_bot_api.reply_message(
                            reply_token,
                            TextSendMessage(text="輸入格式錯誤，請輸入正確的股票代號與年份！")
                        )

                # 處理其他訊息
                else:
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text=f"你說的是：{user_message}")
                    )
            return 'OK'
        except InvalidSignatureError:
            return 'Invalid signature. Please check your channel access token/channel secret.'
        except Exception as e:
            import traceback
            print("發生錯誤：")
            print(traceback.format_exc())
            return 'Internal Server Error', 500

def perform_financial_analysis(stock_id, year):
    url = "https://doc.twse.com.tw/server-java/t57sb01"

    # 第一個請求
    data = {
        'id': '',
        'key': '',
        'step': '1',
        'co_id': stock_id,
        'year': year,
        'seamon': '',
        'mtype': 'F',
        'dtype': 'F04'
    }

    try:
        response = requests.post(url, data=data)
        link = BeautifulSoup(response.text, 'html.parser')
        filename_tag = link.find('a')
        if not filename_tag:
            return "無法找到財報檔案，請確認輸入的股票代號與年份是否正確。"
        filename = filename_tag.text
    except Exception as e:
        return f"無法抓取檔名，錯誤原因：{e}"

    # 第二個請求
    data2 = {
        'step': '9',
        'kind': 'F',
        'co_id': stock_id,
        'filename': filename
    }

    try:
        response = requests.post(url, data=data2)
        link = BeautifulSoup(response.text, 'html.parser')
        href_tag = link.find('a')
        if not href_tag:
            return "無法找到財報下載連結，請稍後再試。"
        download_link = href_tag.get('href')
    except Exception as e:
        return f"無法抓取檔案連結，錯誤原因：{e}"

    # 下載 PDF 並進行分析
    try:
        pdf_path = f"./{stock_id}_{year}.pdf"
        response = requests.get('https://doc.twse.com.tw' + download_link)
        with open(pdf_path, 'wb') as f:
            f.write(response.content)

        # 使用 LangChain 分析 PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)  # 傳遞 API Key
        vectorstore = FAISS.from_documents(documents, embeddings)

        qa_chain = load_qa_chain(
            ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY),  # 傳遞 API Key
            chain_type="stuff"
        )

        # 問題設計，針對財報數據進行分析
        questions = [
            "請精簡總結這份財報與整理出財務狀況、經營績效與未來股價的展望。"
        ]

        results = []
        for question in questions:
            result = qa_chain.run(input_documents=vectorstore.similarity_search(question), question=question)
            results.append(f"{question}\n{result}")

        return "\n\n".join(results)

    except Exception as e:
        return f"下載或分析財報失敗，錯誤原因：{e}"


@app.route("/favicon.ico")  # 處理瀏覽器對 /favicon.ico 的請求，避免這類請求干擾主要路由
def favicon():
    return "", 204  # 返回一個空響應


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
