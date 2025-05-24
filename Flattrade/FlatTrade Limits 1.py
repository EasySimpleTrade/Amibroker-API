import csv
import json
import requests
import sys


login_file = r"R:\FlattradeLogin1.txt" #Chck drive letter
limits_file = r"R:\FlattradeLimits1.txt" #Check drive letter
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

limits_response = requests.post(limits_url, data=limits_payload)
limits_data = limits_response.json()
print(limits_data) 
with open(limits_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    for key, value in limits_data.items():
        writer.writerow([key, value])


