'''
VALLAKKOTTAI MURUGAN THUNAI
Easy Simple Trading Solutions
Telegram @easysimpletradeupdates
Website https://easysimpletrade.blogspot.com
Youtube https://www.youtube.com/@easysimpletrade
GitHub https://github.com/EasySimpleTrade
'''

import requests
import pyotp
import hashlib
from urllib.parse import urlparse, parse_qs
import csv
from datetime import datetime

#Inputs
login_file = r"R:\FlattradeLogin1.txt" #Change path as per your requiremnt 
auth_url = "https://auth.flattrade.in"
authapi_url = "https://authapi.flattrade.in"
inputs_file = r'C:\API\Files\FlatTradeInputs 1.csv'


#Read CSV as Dictonary
def read_csv_dict(file_path):
    data_dict = {}
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if not row:
                continue
            key, value = row
            data_dict[key] = value
    return data_dict


inputs_dict = read_csv_dict(inputs_file)

user_id = inputs_dict['UserID']
pass_word = inputs_dict['Password']
totp_key = inputs_dict['TOTPKey']
api_key = inputs_dict['APIKey']
api_secret =  inputs_dict['APISecret']
act_id = user_id

def sha_256(item):
    return hashlib.sha256(item.encode()).hexdigest()

def get_authcode():
    # Step 1: Get SID
    headers = {
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.5",
        "Host": "authapi.flattrade.in",
        "Origin": f"{auth_url}",
        "Referer": f"{auth_url}/",
        }
    response = requests.post(f"{authapi_url}/auth/session", headers=headers)
    print(f"Session Response: {response.status_code}, {response.text}")

    if response.status_code == 200:
        sid = response.text.strip()

        # Step 2: Request Code
        payload = {
            "UserName": user_id,
            "Password": sha_256(pass_word),
            "App": "",
            "ClientID": "",
            "Key": "",
            "APIKey": api_key,
            "PAN_DOB": pyotp.TOTP(totp_key).now(),
            "Sid": sid,
            "Override": ""
        }
        response = requests.post(f"{authapi_url}/ftauth", json=payload, headers=headers)
        print(f"Auth Response: {response.status_code}, {response.text}")

        if response.status_code == 200:
            response_data = response.json()
            
            # Step 3: Extract Auth Code
            redirect_url = response_data.get("RedirectURL", "")
            if redirect_url:
                query_params = parse_qs(urlparse(redirect_url).query)
                if 'code' in query_params:
                    code = query_params['code'][0]
                    print(f"Request Code: {code}")
                    return code
                else:
                    print("Code not found in query parameters.")
            else:
                print("Error, Check in web login", response.text)
        else:
            print("Authentication failed:", response.text)
    else:
        print("Session creation failed:", response.text)


    return None  


def get_apitoken(code, out_file):
    headers = {"Content-Type": "application/json"}
    payload = {
        "api_key": api_key,
        "request_code": code,
        "api_secret": sha_256(f"{api_key}{code}{api_secret}")
    }
    
    response = requests.post(f"{authapi_url}/trade/apitoken", json=payload, headers=headers)
    print(response.text)
    
    if response.status_code == 200:
        response_data = response.json()
        token = response_data.get("token", "")
        stat = response_data.get("stat", "")
        emsg = response_data.get("emsg", "")

        if token:
            today_date = datetime.now().strftime('%d')
            response_data["date"] = today_date
            response_data["user"] = user_id
            
            with open(out_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                for key, value in response_data.items():
                    writer.writerow([key, value])
        else:
            print(f"SessionToken not found. {response_data.get('emsg', '')}")
            input("Press Enter to exit...")
        return token
    else:
        print(response.text)
        input("Press Enter to exit...")






# Login Execute
code = get_authcode()
if code:
    get_apitoken(code,login_file)
else:
    print("Login Failed")
    input("Press Enter to exit...")
