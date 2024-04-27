from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 指定 chromedriver 的路径
chromedriver_path = r"C:\Users\yifun\Desktop\chromedriver-win64\chromedriver.exe"
service = Service(chromedriver_path)

# 设置 Chrome 选项
options = webdriver.ChromeOptions() # 建立Chrome瀏覽器的配置對象
options.add_argument('--headless')  # 若不想显示窗口，这行不要用注释

def search_and_visit():
    while True:  # 添加一个无限循环，使程序可以不断重复运行
        driver = webdriver.Chrome(service=service, options=options) # 使用上面配置的服務和選項啟動Chrome瀏覽器
        try:
            driver.get('https://www.google.com') # 打開指定的URL
            search_box = driver.find_element(By.NAME, 'q') # 找到頁面上名為'q'的元素
            search_box.send_keys('xxx')  # 輸入想找的關鍵詞
            search_box.send_keys(Keys.RETURN) # 執行搜尋

            wait = WebDriverWait(driver, 60) # 設定網頁load最多等待時間
            # 等待直到搜索结果可见
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a h3')))

            # 逐步滾動頁面直到找到足夠的搜尋結果
            results_needed = 13 # 依照當時網站在搜尋引擎的位置而訂，設定搜尋結果數量

            while True: # 無限循環
                links = driver.find_elements(By.CSS_SELECTOR, 'a h3') # 使用CSS選擇器找到所有包含搜尋結果標題的a h3元素（通常是搜尋結果的標題）
                if len(links) >= results_needed: # 判斷目前頁面上搜尋結果的數量是否達到或超過所需的數量
                    break 
                else: # 若還沒，滾輪繼續往下找
                    driver.execute_script("window.scrollBy(0, 400);")  # 執行JavaScript命令以在瀏覽器中向下捲動400像素，以載入更多結果
                    time.sleep(1)  # 在滾動後暫停1秒，給予頁面載入新內容的時間。

            if len(links) >= results_needed: # 再次檢查是否有足夠的搜尋結果
                parent_link = links[results_needed - 1].find_element(By.XPATH, './../..')  # 第13个元素的索引为12
                parent_link.click()
                time.sleep(30)  # page停留时间
                '''
                取得第13個搜尋結果的連結。使用results_needed - 1來得到正確的索引（因為列表索引從0開始）。
                然後透過XPath找到該h3的父鏈接元素，因為通常h3標籤包裹在一個超鏈接<a>中，所以使用./../..`来访问这个链接元素
                '''
            else:
                print(f"即使滚动后搜索结果仍不足{results_needed}个。")

        finally:
            driver.quit()  # 关闭浏览器，结束当前会话

        time.sleep(2)  # 每次循环结束后等待2秒再重新开始

if __name__ == '__main__':
    search_and_visit()
