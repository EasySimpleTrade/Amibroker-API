'''
VALLAKKOTTAI MURUGAN THUNAI
Easy Simple Trading Solutions
Telegram @easysimpletradeupdates
Website https://easysimpletrade.blogspot.com
Youtube https://www.youtube.com/@easysimpletrade
GitHub https://github.com/EasySimpleTrade
'''

import hashlib
import json
import requests
from pyotp import TOTP
from datetime import datetime
import csv

# Inputs
user_id = 'FA12345' #User Id
password = 'Pass@123' #Password
totpkey = '446556TGXHY47TOQV5E67EFA63WV6FI2' #TOTP Key
vendor_code = 'FA12345_U' #Vendor Code
api_secret = '775c015925197a4982241bd61159d207' #API Secret
imei = 'abc1234' #IMEI

#Write Dictionary to CSV
def dict_to_csv(dictionary, out_file):
    with open(out_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        for key, value in dictionary.items():
            writer.writerow([key, value])

act_id = user_id
login_file = r"R:\ShoonyaLogin1.txt" # Change Path if Required
base_url = "https://api.shoonya.com/NorenWClientTP/"
login_ep = "QuickAuth"

def login(userid, password, totpkey, vendor_code, api_secret, imei, login_file):
    url = f"{base_url}{login_ep}"

    pwd_hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
    u_app_key = f'{userid}|{api_secret}'
    app_key_hashed = hashlib.sha256(u_app_key.encode('utf-8')).hexdigest()

    otp = TOTP(totpkey).now().zfill(6)
    
    values = {
        "apkversion": "1.0.0",
        "uid": userid,
        "pwd": pwd_hashed,
        "factor2": otp,
        "vc": vendor_code,
        "appkey": app_key_hashed,
        "imei": imei,
        "source": "API"
    }

    payload = 'jData=' + json.dumps(values)
    #print(f"Request Payload: {payload}")

    try:

        response = requests.post(url, data=payload)

        if response.status_code == 200:
            response_data = response.json()
            susertoken = response_data.get("susertoken", "")
            stat = response_data.get("stat", "")
            emsg = response_data.get("emsg", "")
            dmsg = response_data.get("emsg", "")
            if dmsg:
                print(f"Message: {dmsg}")

            if susertoken:
                today_date = datetime.now().strftime('%d')
                login_data = {'susertoken':susertoken, 'stat': stat, 'emsg': emsg, 'dmsg': dmsg, 'date': today_date, 'user': user_id}
                dict_to_csv(login_data, login_file)
                print(f"Logged In successfully, response saved to {login_file}")
            
            else:
                print(f"Token not found. {response_data.get('emsg', '')}")
                input("Press Enter to exit...")
            return susertoken
        else:
            print(response.text)
            input("Press Enter to exit...")
        

    except Exception as e:
        print(f"Error during login: {e}")
        input("Press Enter to exit...")
        return None
    
susertoken = login(user_id, password, totpkey, vendor_code, api_secret, imei, login_file) 
