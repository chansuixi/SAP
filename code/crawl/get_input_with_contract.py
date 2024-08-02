import os
import json
import urllib3
import time
import requests
from tqdm import tqdm

http = urllib3.PoolManager()
headers = {
        'User-Agent': 'xxxxx'
}
proxy = urllib3.ProxyManager('xxxxx', headers={'connection': 'keep-alive'})

file_path = 'FuzzingwithState/transactions/'
output_path = "FuzzingwithState/trcode_with_input/"
file_list = os.listdir(file_path)
m = 0
for i in file_list:
    if i.startswith('10127273'):

        break
    m = m + 1


k = 0
with tqdm(total=957 - 0) as par:
    while k < 957:
        print("processing the block: " + str(file_list[k]))
        file = open(file_path + file_list[k], mode='r+', encoding='UTF-8')
        res = file.read()
        transaction_list = json.loads(res)['transactions']
        i = 0
        while i < len(transaction_list):
            # print(transaction_list[i])
            contract_address = transaction_list[i]['to']
            if contract_address is None:
                i = i + 1
                continue
            input = transaction_list[i]['input']
            # print(input)
            if input == "0x":
                i = i + 1
                continue
            # print("process the contract" + str(i) + ":" + str(contract_address))
            try:
               
                URL1 = ("https://api.etherscan.io/api?module=proxy&action=eth_getCode&address=" + contract_address +
                        "&tag=latest" +
                        "&apikey=UFBU3KX3TKBVQQTG4TA1RE2S8M6SC37WG8")
                res1 = requests.get(URL1,headers=headers)
                
                URL2 = ("https://api.etherscan.io/api?module=contract&action=getabi&address=" + contract_address +
                        "&apikey=UFBU3KX3TKBVQQTG4TA1RE2S8M6SC37WG8")
                
                res2 = requests.get(URL2,headers=headers)
                # print(response2)
                # time.sleep(1)
                URL3 = ("https://api.etherscan.io/api?module=contract&action=getsourcecode&address=" + contract_address +
                        "&apikey=UFBU3KX3TKBVQQTG4TA1RE2S8M6SC37WG8")
                res3 = requests.get(URL3, headers=headers)
                raw_string1 = res1.text
               
                raw_string2 = res2.text
                
                raw_string3 = res3.text
                json_string1 = json.loads(raw_string1)
                json_string2 = json.loads(raw_string2)
                json_string3 = json.loads(raw_string3)
                byte_code = json_string1["result"]
                if byte_code is None:
                    continue
                abi = json_string2["result"]
                if abi is None:
                    continue
                source_code = json_string3["result"][0]["SourceCode"]
                if source_code is None:
                    continue
                file = open(output_path + str(i) + "-" + file_list[k].split('.')[0] + "-" + contract_address + '.txt', mode='w+', encoding="UTF-8")
                file.write(json.dumps({"byteCode":byte_code, "abi":abi, "input":input, "sourceCode":source_code}))
                file.close()
               
                i = i + 1

            except Exception as e:
                
                time.sleep(2)
        k = k + 1
        par.update(1)