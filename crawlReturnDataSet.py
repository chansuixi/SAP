import csv
import json
import time

import requests
import os
import urllib3
http = urllib3.PoolManager()
API_KEY = "UFBU3KX3TKBVQQTG4TA1RE2S8M6SC37WG8"
SAVE_FOLDER = "/Users/yangkaixuan/Downloads/SmartGift-main/RTDataSet"
headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36'
}
proxy = urllib3.ProxyManager('http://61.135.155.82:443', headers={'connection': 'keep-alive'})

def download_contract_source(address, version, label):
    url1 = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={API_KEY}"
    URL2 = ("https://api.etherscan.io/api?module=contract&action=getabi&address=" + address +
            "&apikey=UFBU3KX3TKBVQQTG4TA1RE2S8M6SC37WG8")



    try:
        num_folder = 0
        response1 = requests.get(url1)
        response2 = requests.get(URL2)
        if response1.status_code == 200:
            contract_data = response1.json()
            if contract_data['status'] == "1" and contract_data['message'] == "OK":
                source_code = contract_data['result'][0]['SourceCode']

                filename = f"{label}_{version}_{address}.sol"
                if label == '2':
                    label_folder = "no_delcare"
                elif label == '0':
                    label_folder = "mal"
                else:
                    label_folder = "vul"
                num_folder = len(source_code.split("\r\n"))// 200
                os.makedirs(os.path.join(SAVE_FOLDER, label_folder + str(num_folder)), exist_ok=True)
                save_path = os.path.join(SAVE_FOLDER, label_folder + str(num_folder), filename)
                with open(save_path, "w+") as file:
                    file.write(source_code)

                print(f"Source code for contract {address} downloaded successfully. Saved as {filename}")
            else:
                print(f"Failed to download source code for contract {address}. Error message: {contract_data['message']}")
        else:
            print(f"Failed to download source code for contract {address}. Response status code: {response1.status_code}")

        if response2.status_code == 200:
            raw_string2 = response2.text
            json_string = json.loads(raw_string2)
            abi = json_string["result"]
            filename = f"{label}_{version}_{address}.abi"
            if label == '2':
                label_folder = "no_delcare"
            elif label == '0':
                label_folder = "mal"
            else:
                label_folder = "vul"
            os.makedirs(os.path.join(SAVE_FOLDER, label_folder + str(num_folder)), exist_ok=True)
            save_path = os.path.join(SAVE_FOLDER, label_folder + str(num_folder), filename)
            with open(save_path, "w+") as file:
                file.write(abi)

            print(f"Source code for contract {address} downloaded successfully. Saved as {filename}")
        else:
            print(f"Failed to download source code for contract {address}. Error message: {contract_data['message']}")
    except Exception:
        time.sleep(2)
        print(f"wrong with {address}")
# Read contract addresses and Solidity versions from CSV file
contract_data = []
csv_file = "/Users/yangkaixuan/Downloads/SmartGift-main/reentracy_with_sorted_version-Manual Label-1.csv"

def count_revulsc_num(label):
    num = 0
    if label == 1:
        num += 1
    return num

with open(csv_file, "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        address = row["address"]
        version = row["CompilerVersion"]
        label = row["label"]
        contract_data.append((address, version, label))

# Create the save folder if it doesn't exist
os.makedirs(SAVE_FOLDER, exist_ok=True)
num = 0
# Download contract source code
for address, version, label in contract_data:
    if label == '1':
        download_contract_source(address, version, label)
        num += 1
# download_contract_source('0x805129c7144688224c122c924e3855d5b4fa01d8' , '111',1)
    # print(vul_num)
    # download_contract_source(address, version, label)
