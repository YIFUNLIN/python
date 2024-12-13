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
from pymongo import MongoClient


# 加載環境變數
load_dotenv()

ENDPOINT = os.environ.get('mongodb_endpoint', '')
client = MongoClient(ENDPOINT)
db = client['mydatabase']
collection = db['Financial_report']

app = Flask(__name__)



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

                # 推薦系統功能
                if user_message == '推薦系統' or user_message == '推薦':
                    flex_message = FlexSendMessage(
                        alt_text="點擊查看網頁",
                        contents={
                            "type": "bubble",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {"type": "text", "text": "推薦系統", "weight": "bold", "align": "center"}
                                ]
                            },
                            "footer": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "button",
                                        "action": {"type": "uri", "label": "前往網頁", "uri": LIFF_URL},
                                        "style": "primary"
                                    }
                                ]
                            }
                        }
                    )
                    line_bot_api.reply_message(reply_token, flex_message)

                # 財報分析功能
                elif user_message.startswith("財報分析"):
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text="請輸入股票代號與年份，格式為：[股票代號] [年份]")
                    )

                # 處理股票代號與年份
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

                # 近況分析功能
                elif user_message == "近況分析":
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text="請輸入股票代號，eg. 2330")
                    )

                # 處理股票代號輸入
                elif user_message.isdigit():
                    stock_id = user_message
                    analysis_result = perform_recent_analysis(stock_id)
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text=analysis_result)
                    )

                
                # 處理其他訊息
                else:
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text=f"沒錯，你說的是：{user_message}")
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
    pdf_path = f"./{stock_id}_{year}.pdf"  # 預設 PDF 路徑

    try:
        existing_document = collection.find_one({'stock_id': stock_id, 'year': year})
        
        if existing_document:
            print("已存在，直接從DB中提取")
            pdf_content = existing_document["content"]
            
            # 将数据库中的 PDF 内容写入文件
            with open(pdf_path, "wb") as f:
                f.write(pdf_content)
        else:
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

            response = requests.post(url, data=data)
            link = BeautifulSoup(response.text, 'html.parser')
            filename_tag = link.find('a')
            if not filename_tag:
                return "無法找到財報檔案，請確認輸入的股票代號與年份是否正確。"
            filename = filename_tag.text

            # 第二個請求
            data2 = {
                'step': '9',
                'kind': 'F',
                'co_id': stock_id,
                'filename': filename
            }

            response = requests.post(url, data=data2)
            link = BeautifulSoup(response.text, 'html.parser')
            href_tag = link.find('a')
            if not href_tag:
                return "無法找到財報下載連結，請稍後再試。"
            download_link = href_tag.get('href')

            # 下載 PDF 並進行分析
            response = requests.get('https://doc.twse.com.tw' + download_link)
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            pdf_content = response.content
            
            # 將 結果 存入 MongoDB
            document = {
                "stock_id": stock_id,
                "year": year,   
                "content": pdf_content
            }
            collection.insert_one(document)
            print(f"成功儲存{stock_id}_{year}的年報")

        # 使用 LangChain 分析 PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectorstore = FAISS.from_documents(documents, embeddings)

        qa_chain = load_qa_chain(
            ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=OPENAI_API_KEY),
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

def perform_recent_analysis(stock_id):
    # 更新抓取 API 的邏輯
    url = f"https://ess.api.cnyes.com/ess/api/v1/news/keyword?q={stock_id}&limit=3&page=1"
    try:
        response = requests.get(url)
        response.raise_for_status()  # 確保請求成功
        json_data = response.json()

        # 確認資料格式並擷取前三筆新聞
        items = json_data.get('data', {}).get('items', [])
        if not items:
            return f"無法找到與 {stock_id} 相關的新聞資料。"

        news = []
        for item in items[:3]:
            title = item['title']
            news_id = item['newsId']
            link = f"https://news.cnyes.com/news/id/{news_id}"
            news.append(f"標題: {title}\n連結: {link}")

        # 格式化結果
        news_list = "\n\n".join(news)
        return f"以下是與 {stock_id} 相關的最新新聞：\n\n{news_list}"

    except Exception as e:
        return f"無法取得或分析近況，錯誤原因：{e}"
    
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
