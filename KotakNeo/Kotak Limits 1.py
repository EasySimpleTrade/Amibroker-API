'''
VALLAKKOTTAI MURUGAN THUNAI
Easy Simple Trading Solutions
Telegram @easysimpletradeupdates
Website https://easysimpletrade.blogspot.com
Youtube https://www.youtube.com/@easysimpletrade
GitHub https://github.com/EasySimpleTrade
'''

import csv
import requests
import sys

#Inputs
login_file = r'R:\KotakLogin1.txt'
limits_file = r'R:\KotakLimits1.txt'


access_token = sys.argv[1]
session_token = sys.argv[2]
sid = sys.argv[3]
hs_server_id = sys.argv[4]

print(f"Access Token: {access_token}")
print(f"Session Token: {session_token}")
print(f"SID: {sid}")
print(f"HS Server ID: {hs_server_id}")

neo_fin_key = 'neotradeapi'
segment = 'CASH'
exchange = 'NSE'
product = 'ALL'

api_headers = {
    'accept': 'application/json',
    'Sid': sid,
    'Auth': session_token,
    'neo-fin-key': neo_fin_key,
    'Content-Type': 'application/x-www-form-urlencoded',
    'Authorization': f'Bearer {access_token}'
}


limits_data = {
    'jData': f'{{"seg":"{segment}","exch":"{exchange}","prod":"{product}"}}'
}


limits_response = requests.post(f'https://gw-napi.kotaksecurities.com/Orders/2.0/quick/user/limits?sId={hs_server_id}', headers=api_headers, data=limits_data)

# Check if the response is OK (status code 200)
if limits_response.status_code == 200:
    # Convert response to a dictionary
    limits_data = limits_response.json()

    # Write to CSV (without header)
    with open(limits_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        for key, value in limits_data.items():
            writer.writerow([key, value])  # Writing key-value pairs

    print(f"Response Text: {limits_response.text}")

else:

    print(f"Error Message: {limits_response.text}")
    input("Press Enter to exit...")

