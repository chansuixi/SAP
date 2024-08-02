import urllib3
import json
import time
import requests
from tqdm import tqdm
import os
# 2253
latest_blocknum = 10128210
want_to_get_num = 957


# current_script_path = os.path.abspath(__file__)
dir_path = 'FuzzingwithState/transactions/'

http = urllib3.PoolManager()

headers = {
        'User-Agent': 'xxxx'}

proxy = urllib3.ProxyManager('http://api.etherscan.io', headers={'connection': 'keep-alive'})
i = 0
par = tqdm(total=want_to_get_num)
while i < want_to_get_num:
    print("Processing the block:" + str(latest_blocknum - i))
    try:
        URL = "http://api.etherscan.io/api?module=proxy&action=eth_getBlockByNumber&tag="+ str(hex(latest_blocknum - i)) +"&boolean=true&apikey=UFBU3KX3TKBVQQTG4TA1RE2S8M6SC37WG8"
        res = requests.get(URL)
        json_res = json.loads(res.text)
        # print(json_res["result"]["transactions"])
        transactions = json_res["result"]["transactions"]
        file = open(dir_path + str(latest_blocknum - i) + ".txt", mode="w+", encoding="UTF-8")
        file.write(json.dumps({"transactions": transactions}))
        file.close()
        i = i + 1

    except Exception as e:
        print(e)
        print("error")
        time.sleep(5)  # whatever the error is, wait 100 sec more or less
    finally:
        par.update(1)
par.close()