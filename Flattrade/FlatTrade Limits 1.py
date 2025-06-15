import csv
import json
import requests
import sys


login_file = r"R:\FlattradeLogin1.txt"
limits_file = r"R:\FlattradeLimits1.txt"
base_url = 'https://piconnect.flattrade.in/PiConnectTP/'
limits_ep = 'Limits'


user_id = sys.argv[1]
jkey = sys.argv[2]

print(f"UserID: {user_id}")
print(f"JKey: {jkey}")
act_id = user_id

jdata = {
    "uid": user_id,
    "actid": act_id
}

limits_url = base_url+limits_ep
limits_payload = f'jData={json.dumps(jdata)}&jKey={jkey}'

try:
    limits_response = requests.post(limits_url, data=limits_payload)
    limits_data = limits_response.json()
    with open(limits_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        for key, value in limits_data.items():
            writer.writerow([key, value])
except ValueError as e:
    print(f"JSON decode error: {e}")
    input("Press Enter to exit...")
except requests.exceptions.SSLError as e:
    print(f"SSL error: {e}")
    input("Press Enter to exit...")
except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
    input("Press Enter to exit...")
