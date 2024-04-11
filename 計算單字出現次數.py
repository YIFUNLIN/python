news = """Consumer prices in the US rose faster than expected last month, in a sign that the fight to slow inflation has stalled.
Prices rose 3.5% over the 12 months to March, up from 3.2% in February, the US Labor Department said.
Higher costs for fuel, housing, dining out and clothing drove the increase.
Analysts warned that the lack of progress in curbing price rises will force the US central bank to keep interest rates higher for longer.
Higher rates help stabilise prices by making it more expensive to borrow for business expansions and other spending. In theory, that in turn slows the economy, and eases the pressures pushing up prices."""


def modify(str): # 將新聞去除標點符號並將大寫轉小寫
    for i in str:
        if i in "%,.?":
            str = str.replace(i,"").lower()
    return str

print(modify(news))

# 計算每個字出現的次數
mydict = {}
def wordcount(str):
    global mydict
    str = str.split()  # 串列形式
    mydict = {wd:str.count(wd) for wd in set(str)} # 轉成dict，才能累積出現次數

wordcount(news)
print('')
print(mydict)
