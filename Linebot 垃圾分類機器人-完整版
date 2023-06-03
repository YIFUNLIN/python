from flask import Flask, request

# 載入 json 標準函式庫，處理回傳的資料格式
import json

# 載入 LINE Message API 相關函式庫
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, LocationSendMessage
import tensorflow as tf
import cv2
import numpy as np
app = Flask(__name__)  # 建立 app 變數為 Flask 物件，__name__ 表示目前執行的程式
 
@app.route("/", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)                    # 取得收到的訊息內容
    try:
        json_data = json.loads(body)                         # json 格式化訊息內容
        access_token = 'UbErzZYczvq3sJRdLCRTgCRPe0MoAl9SgTinnwO5bekPLTNhdVRhVfQT+0YA7sdeqW7UQQuOX4P/uXWnDjPgj3SxrcEhBcKQ6hTyYbdMc+lP5aOZXdtGn/ilaDBzChjWPD5M/xU5tcMxUAtKG5XOmgdB04t89/1O/w1cDnyilFU='                                    # 你的 Access Token
        secret = '4ce7aa1c00ff292a34b61874ea62a809'                                          # 你的 Channel Secret
        line_bot_api = LineBotApi(access_token)              # 確認 token 是否正確
        handler = WebhookHandler(secret)                     # 確認 secret 是否正確
        signature = request.headers['X-Line-Signature']      # 加入回傳的 headers
        handler.handle(body, signature)                      # 綁定訊息回傳的相關資訊
        tk = json_data['events'][0]['replyToken']            # 取得回傳訊息的 Token
        type = json_data['events'][0]['message']['type']     # 取得 LINE 收到的訊息類型
        # 判斷如果是文字
        if type=='text':
            msg = json_data['events'][0]['message']['text']  # 取得 LINE 收到的文字訊息
            img_url = reply_img(msg)
            location_info = reply_location(msg)
            
            if location_info:
            # 如果有地點資訊，回傳地點
                location_message = LocationSendMessage(
                    title=location_info['title'],
                    address=location_info['address'],
                    latitude=float(location_info['latitude']),
                    longitude=float(location_info['longitude'])
                )
                line_bot_api.reply_message(tk, location_message)
            elif img_url:
                # 如果有圖片網址，回傳圖片
                img_message = ImageSendMessage(
                    original_content_url=img_url,
                    preview_image_url=img_url
                )
                line_bot_api.reply_message(tk, img_message)
            else:
                # 如果都沒有，回傳文字
                text_message = TextSendMessage(text='找不到相關內容')
                line_bot_api.reply_message(tk, text_message)
            
                        
        # 判斷如果是圖片
        elif type == 'image':
            msgID = json_data['events'][0]['message']['id']  # 取得訊息 id
            message_content = line_bot_api.get_message_content(msgID)  # 根據訊息 ID 取得訊息內容
           # 在适当的位置调用 recognize() 函数获取预测结果和图片链接
            reply_message, image_url = recognize(message_content)

            # 创建 ImageSendMessage 对象
            image_message = ImageSendMessage(original_content_url=image_url, preview_image_url=image_url)

            # 回复预测结果和对应的图片
            line_bot_api.reply_message(tk, [reply_message, image_message])

        else:
            reply = '你傳的不是文字或圖片呦～'
        print(reply)
        line_bot_api.reply_message(tk,TextSendMessage(reply))  # 回傳訊息
    except:
        print(body)                                            # 如果發生錯誤，印出收到的內容
    return 'OK'                                                # 驗證 Webhook 使用，不能省略


# 建立回覆圖片的函式
def reply_img(text):
    # 文字對應圖片網址的字典
    img = {
        'Trash':'https://down-tw.img.susercontent.com/file/e790674054cfc3fba672c457e2ba159c',
        'Paper':'https://cf.shopee.tw/file/ba1f82987531c905c007f905a32bd412',
        'Paper_Containers':'https://cf.shopee.tw/file/d8d985e3935bae46edebc252a1a46950',
        'Plastics':'https://image1.thenewslens.com/2017/8/xw5rb10op8d4ys399eyy8hffua6y1p.jpg?auto=compress&q=80&w=1080',
        'Tin_and_aluminum':'https://www.kdmanpower.com.tw/upload/images/%E7%B5%84%E5%90%88%201_%E9%A0%81%E9%9D%A2_15.png',
        'Glass':'https://cf.shopee.tw/file/a3ede2a7bf9ad480634bef0bddd04a20',
        '星期一其他類':'https://1.bp.blogspot.com/-v0IDttUio-w/XixZmBsdxYI/AAAAAAAArr8/WBk0SSZLdw89gX8lhMrQJ8Hj0OYLhMvCQCLcBGAsYHQ/s1600/%25E8%25B3%2587%25E6%25BA%2590%25E5%259B%259E%25E6%2594%25B6%25E5%2588%2586%25E9%25A1%259E%25E4%25B8%2580%25E8%25A6%25BD%25E8%25A1%25A8%25E5%259C%2596%25E6%2596%2587%25E6%2591%25BA%25E9%25A0%2581-%25E4%25B8%25AD%25E6%2596%2587%25E7%2589%258804.jpg',
        '星期二其他類':'https://1.bp.blogspot.com/-v0IDttUio-w/XixZmBsdxYI/AAAAAAAArr8/WBk0SSZLdw89gX8lhMrQJ8Hj0OYLhMvCQCLcBGAsYHQ/s1600/%25E8%25B3%2587%25E6%25BA%2590%25E5%259B%259E%25E6%2594%25B6%25E5%2588%2586%25E9%25A1%259E%25E4%25B8%2580%25E8%25A6%25BD%25E8%25A1%25A8%25E5%259C%2596%25E6%2596%2587%25E6%2591%25BA%25E9%25A0%2581-%25E4%25B8%25AD%25E6%2596%2587%25E7%2589%258804.jpg',
        '星期四其他類':'https://1.bp.blogspot.com/-v0IDttUio-w/XixZmBsdxYI/AAAAAAAArr8/WBk0SSZLdw89gX8lhMrQJ8Hj0OYLhMvCQCLcBGAsYHQ/s1600/%25E8%25B3%2587%25E6%25BA%2590%25E5%259B%259E%25E6%2594%25B6%25E5%2588%2586%25E9%25A1%259E%25E4%25B8%2580%25E8%25A6%25BD%25E8%25A1%25A8%25E5%259C%2596%25E6%2596%2587%25E6%2591%25BA%25E9%25A0%2581-%25E4%25B8%25AD%25E6%2596%2587%25E7%2589%258804.jpg',
        '星期五其他類':'https://1.bp.blogspot.com/-v0IDttUio-w/XixZmBsdxYI/AAAAAAAArr8/WBk0SSZLdw89gX8lhMrQJ8Hj0OYLhMvCQCLcBGAsYHQ/s1600/%25E8%25B3%2587%25E6%25BA%2590%25E5%259B%259E%25E6%2594%25B6%25E5%2588%2586%25E9%25A1%259E%25E4%25B8%2580%25E8%25A6%25BD%25E8%25A1%25A8%25E5%259C%2596%25E6%2596%2587%25E6%2591%25BA%25E9%25A0%2581-%25E4%25B8%25AD%25E6%2596%2587%25E7%2589%258804.jpg',
        '星期六其他類':'https://1.bp.blogspot.com/-v0IDttUio-w/XixZmBsdxYI/AAAAAAAArr8/WBk0SSZLdw89gX8lhMrQJ8Hj0OYLhMvCQCLcBGAsYHQ/s1600/%25E8%25B3%2587%25E6%25BA%2590%25E5%259B%259E%25E6%2594%25B6%25E5%2588%2586%25E9%25A1%259E%25E4%25B8%2580%25E8%25A6%25BD%25E8%25A1%25A8%25E5%259C%2596%25E6%2596%2587%25E6%2591%25BA%25E9%25A0%2581-%25E4%25B8%25AD%25E6%2596%2587%25E7%2589%258804.jpg',
        '星期一':'https://1.bp.blogspot.com/-HtFJjIKwOVs/XixZmBYOVyI/AAAAAAAArsE/3WW5U3SBf985OjybMWva0jJUqplm5nKBQCLcBGAsYHQ/s1600/%25E8%25B3%2587%25E6%25BA%2590%25E5%259B%259E%25E6%2594%25B6%25E5%2588%2586%25E9%25A1%259E%25E4%25B8%2580%25E8%25A6%25BD%25E8%25A1%25A8%25E5%259C%2596%25E6%2596%2587%25E6%2591%25BA%25E9%25A0%2581-%25E4%25B8%25AD%25E6%2596%2587%25E7%2589%258803.jpg',
        '星期五':'https://1.bp.blogspot.com/-HtFJjIKwOVs/XixZmBYOVyI/AAAAAAAArsE/3WW5U3SBf985OjybMWva0jJUqplm5nKBQCLcBGAsYHQ/s1600/%25E8%25B3%2587%25E6%25BA%2590%25E5%259B%259E%25E6%2594%25B6%25E5%2588%2586%25E9%25A1%259E%25E4%25B8%2580%25E8%25A6%25BD%25E8%25A1%25A8%25E5%259C%2596%25E6%2596%2587%25E6%2591%25BA%25E9%25A0%2581-%25E4%25B8%25AD%25E6%2596%2587%25E7%2589%258803.jpg',
        '星期二':'https://1.bp.blogspot.com/-yQ50YTREuAM/XixZmCYRNEI/AAAAAAAArsA/3U8R2xxZdp4Lpk7By9vizu3s5RI83aBVgCLcBGAsYHQ/s1600/%25E8%25B3%2587%25E6%25BA%2590%25E5%259B%259E%25E6%2594%25B6%25E5%2588%2586%25E9%25A1%259E%25E4%25B8%2580%25E8%25A6%25BD%25E8%25A1%25A8%25E5%259C%2596%25E6%2596%2587%25E6%2591%25BA%25E9%25A0%2581-%25E4%25B8%25AD%25E6%2596%2587%25E7%2589%258802.jpg',
        '星期四':'https://1.bp.blogspot.com/-yQ50YTREuAM/XixZmCYRNEI/AAAAAAAArsA/3U8R2xxZdp4Lpk7By9vizu3s5RI83aBVgCLcBGAsYHQ/s1600/%25E8%25B3%2587%25E6%25BA%2590%25E5%259B%259E%25E6%2594%25B6%25E5%2588%2586%25E9%25A1%259E%25E4%25B8%2580%25E8%25A6%25BD%25E8%25A1%25A8%25E5%259C%2596%25E6%2596%2587%25E6%2591%25BA%25E9%25A0%2581-%25E4%25B8%25AD%25E6%2596%2587%25E7%2589%258802.jpg',
        '星期六':'https://1.bp.blogspot.com/-yQ50YTREuAM/XixZmCYRNEI/AAAAAAAArsA/3U8R2xxZdp4Lpk7By9vizu3s5RI83aBVgCLcBGAsYHQ/s1600/%25E8%25B3%2587%25E6%25BA%2590%25E5%259B%259E%25E6%2594%25B6%25E5%2588%2586%25E9%25A1%259E%25E4%25B8%2580%25E8%25A6%25BD%25E8%25A1%25A8%25E5%259C%2596%25E6%2596%2587%25E6%2591%25BA%25E9%25A0%2581-%25E4%25B8%25AD%25E6%2596%2587%25E7%2589%258802.jpg'
    }
    if text in img:
        return img.get(text)
    else:
      # 如果找不到對應的圖片，回傳 False
        return False

# 建立回覆地點的函式
def reply_location(text):
    # 建立地點與文字對應的字典
    location = {
        '萬華區': {
            'title': '萬華區',
            'address': '臺北市萬華區長順街臨131號',
            'latitude': '25.031347',
            'longitude': '121.490747'
        },
        '內湖區': {
            'title': '內湖區',
            'address': '臺北市內湖區舊宗路二段臨158號',
            'latitude': '25.0700469999999',
            'longitude': '121.574785'
        },
        '北投區': {
            'title': '北投區',
            'address': '臺北市北投區大度路三段臨250號',
            'latitude': '25.1234082',
            'longitude': '121.4669281'
        },
        '士林區': {
            'title': '士林區',
            'address': '臺北市士林區中正路臨692號對面',
            'latitude': '25.0864',
            'longitude': '121.5066'
        },
        '中山區': {
            'title': '中山區',
            'address': '臺北市中山區建國北路一段臨5-1號',
            'latitude': '25.046412',
            'longitude': '121.537031'
        },
        '松山區': {
            'title': '松山區',
            'address': '臺北市松山區民權東路五段臨94號',
            'latitude': '25.06316899999',
            'longitude': '121.56739899999'
        },
        '大同區': {
            'title': '大同區',
            'address': '臺北市大同區環河北路一段63號之1',
            'latitude': '25.052557',
            'longitude': '121.507442'
        },
        '中正區': {
            'title': '中正區',
            'address': '臺北市中正區師大路臨241號',
            'latitude': '25.0209417',
            'longitude': '121.5253309'
        },
        '大安區': {
            'title': '大安區',
            'address': '臺北市大安區通化街120巷20之1號旁',
            'latitude': '25.0293959999',
            'longitude': '121.55325'
        },
        '信義區': {
            'title': '信義區',
            'address': '臺北市信義區忠孝東路五段275巷7弄邊',
            'latitude': '25.0413',
            'longitude': '121.5703'
        },
        '文山區': {
            'title': '文山區',
            'address': '臺北市文山區景豐街臨82號',
            'latitude': '25.001258',
            'longitude': '121.545115999999'
        },
        '南港區': {
            'title': '南港區',
            'address': '臺北市南港區松河街699號',
            'latitude': '25.058671',
            'longitude': '121.596766'
        }
    }
    if text in location:
        return location.get(text)
    else:
        # 如果找不到對應的地點，回傳 False
        return False

def recognize(img):
    model = tf.keras.models.load_model('keras_model.h5', compile=False)  #利用load_model載入我們預先訓練好的模型
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32) #建形狀為(1, 224, 224, 3) 的 NumPy 數組。用於存儲待預測圖像的數據。
    
    #圖像預處理步驟
    image = cv2.imdecode(np.frombuffer(img.content, np.uint8), cv2.IMREAD_COLOR)
    #代碼使用 OpenCV 的 imdecode() 函數將傳遞給函數的圖像數據解碼為圖像格式。 img.content 是包含圖像數據的字節流對象。
    #np.frombuffer(img.content, np.uint8) 的作用是將 img.content 中的字節數據解析為一個 NumPy 數組，
    #數據類型為 np.uint8（無符號8位整數）。這樣可以將字節數據轉換為可處理的數組形式。                                   
                                       
    img = cv2.resize(image, (398, 224))  # 改變尺寸
    img = img[0:224, 80:304]  # 裁切为正方形，符合 model 大小
    image_array = np.asarray(img)  # 去除換行符號和结尾空白，產生文字數组
    normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1  # 轉換預測模組
    data[0] = normalized_image_array
    
    prediction = model.predict(data)  # 預測结果
    Paper, Paper_Containers, Plastics, Tin_and_aluminum, Glass, Trash = prediction[0]
    
    if Paper > 0.5:
        result = 'Paper'
    elif Paper_Containers > 0.5:
        result = 'Paper_Containers'
    elif Plastics > 0.5:
        result = 'Plastics'
    elif Tin_and_aluminum > 0.5:
        result = 'Tin_and_aluminum'
    elif Glass > 0.5:
        result = 'Glass'
    elif Trash > 0.5:
        result = 'Trash'
    else:
        result = "I don't know"
    
                                       
    image_url = reply_img(result)                                   
    # 建構回覆消息對象
    reply_text = f"The predicted item is: {result}"
    reply_message = TextSendMessage(text=reply_text)
    
    return reply_message,image_url


if __name__ == "__main__":
    app.run()
