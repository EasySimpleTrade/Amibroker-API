'''
VALLAKKOTTAI MURUGAN THUNAI
Easy Simple Trading Solutions
Telegram @easysimpletradeupdates
Website https://easysimpletrade.blogspot.com
Youtube https://www.youtube.com/@easysimpletrade
GitHub https://github.com/EasySimpleTrade
'''

#Required Libraries

import requests
from pyotp import TOTP
import csv
from datetime import datetime

# ---------------- Inputs ----------------

login_file = r'R:\KotakLogin1.txt'
inputs_file = r'C:\API\Files\KotakInputs 1.csv'

login_url = "https://mis.kotaksecurities.com/login/1.0/tradeApiLogin"
validate_url = "https://mis.kotaksecurities.com/login/1.0/tradeApiValidate"

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

client_code = inputs_dict['UserID']
mpin = inputs_dict['MPIN']
totpkey = inputs_dict['TOTPKey']
access_token =  inputs_dict['Token']
mobile_number =  inputs_dict['Mobile']

# ---------------- STEP 1 : TOTP Login ----------------


totp = TOTP(totpkey).now()

login_headers = {
    "Authorization": access_token,
    "neo-fin-key": "neotradeapi",
    "Content-Type": "application/json"
}

login_payload = {
    "mobileNumber": mobile_number,
    "ucc": client_code,
    "totp": totp
}

login_resp = requests.post(login_url, headers=login_headers, json=login_payload)

print("STEP 1 Status:", login_resp.status_code)
login_data = login_resp.json()
print("STEP 1 Response:", login_data)

# Extract token & sid
token = login_data["data"]["token"]
sid = login_data["data"]["sid"]

print("\nExtracted Token:", token)
print("Extracted SID:", sid)

# ---------------- STEP 2 : MPIN Validation ----------------

validate_headers = {
    "Authorization": access_token,      # SAME as step 1
    "neo-fin-key": "neotradeapi",
    "sid": sid,                          # from step 1
    "Auth": token,                       # from step 1
    "Content-Type": "application/json"
}

validate_payload = {
    "mpin": mpin
}

validate_resp = requests.post(
    validate_url,
    headers=validate_headers,
    json=validate_payload
)

print("\nSTEP 2 Status:", validate_resp.status_code)

try:
    print("STEP 2 Response:", validate_resp.json())
except ValueError:
    print("STEP 2 Raw Response:", validate_resp.text)


# ---------------- STEP 2 RESPONSE DATA ----------------
step2_data = validate_resp.json()["data"]

# Extract required fields
final_token = step2_data["token"]
final_sid = step2_data["sid"]
base_url = step2_data["baseUrl"]
ucc = step2_data["ucc"]

# Today's date (DD)
today_date = datetime.now().strftime('%d')


# Prepare dictionary (order preserved)
login_dict = {
    "token": final_token,
    "sid": final_sid,
    "baseurl": base_url,
    "user": ucc,
    "date": today_date
}

# ---------------- WRITE DICTIONARY TO CSV ----------------
def dict_to_csv(dictionary, out_file):
    with open(out_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for key, value in dictionary.items():
            writer.writerow([key, value])

dict_to_csv(login_dict, login_file)

print("✅ Login details written to:", login_file)
