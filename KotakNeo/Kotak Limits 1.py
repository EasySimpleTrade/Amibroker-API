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
import time

#Inputs
login_file = r'R:\KotakLogin1.txt'
limits_file = r'R:\KotakLimits1.txt'

'''
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

login_dict = read_csv_dict(login_file)
session_token = login_dict['token']
sid = login_dict['sid']
baseurl = login_dict['baseurl']

'''
session_token = sys.argv[1]
sid = sys.argv[2]
baseurl = sys.argv[3]


print(f"Access Token: {session_token}")
print(f"SID: {sid}")
print(f"Base URL: {baseurl}")


neo_fin_key = 'neotradeapi'
segment = 'ALL'
exchange = 'ALL'
product = 'ALL'

api_headers = {
    'accept': 'application/json',
    'Sid': sid,
    'Auth': session_token,
    'neo-fin-key': neo_fin_key,
    'Content-Type': 'application/x-www-form-urlencoded'
}


limits_data = {
    'jData': f'{{"seg":"{segment}","exch":"{exchange}","prod":"{product}"}}'
}


limits_response = requests.post(f'{baseurl}/quick/user/limits', headers=api_headers, data=limits_data)

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

time.sleep(2)
