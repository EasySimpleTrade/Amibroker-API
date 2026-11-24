import csv
import json
import requests
import sys
import time


login_file = r"R:\FlattradeLogin1.txt" #Chck drive letter
limits_file = r"R:\FlattradeLimits1.txt" #Check drive letter
base_url = 'https://piconnect.flattrade.in/PiConnectAPI/'
limits_ep = 'Limits'

'''
# Read login token
def read_csv_dict(file_path):
    data_dict = {}
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            key, value = row
            data_dict[key] = value
    return data_dict

login_dict = read_csv_dict(login_file)
user_id = login_dict['user']
jkey = login_dict['token']

'''

if len(sys.argv) < 3:
    print(f"Expected {sys.argv[0]} <user_id> <jkey>")
    print(f"Received arguments: {sys.argv[1:]}")
    time.sleep(10)
    sys.exit(1)

user_id = sys.argv[1]
jkey = sys.argv[2]

#print(f"Expected {sys.argv[0]} <user_id> <jkey>")
#print(f"Received arguments: {sys.argv[1:]}")
#time.sleep(1)

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

time.sleep(2)
