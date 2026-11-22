import csv
import requests
import json
import sys
import time

login_file = r'R:\AliceBlueLogin1.txt'
limits_file = r"R:\AliceBlueLimits1.txt" 
base_url = 'https://a3.aliceblueonline.com/'
limits_ep = 'open-api/od/v1/limits'

'''
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

print(f"Received arguments: {sys.argv[1:]}")
time.sleep(1)

if len(sys.argv) < 3:
    print(f"Expected {sys.argv[0]} <user_id> <jkey>")
    print(f"Received arguments: {sys.argv[1:]}")
    time.sleep(5)
    sys.exit(1)
    
user_id = sys.argv[1]
jkey = sys.argv[2]

limits_url = base_url + limits_ep

headers = {
    "Authorization": f"Bearer {jkey}",
    "Content-Type": "application/json"
}

try:
    limits_response = requests.get(limits_url, headers=headers)
    limits_data = limits_response.json()
    print(limits_data)

    with open(limits_file, mode='w', newline='') as file:
        writer = csv.writer(file)

        # Write status and message
        writer.writerow(['status', limits_data.get('status')])
        writer.writerow(['message', limits_data.get('message')])

        # Write result dictionary
        result = limits_data.get('result', [])

        if result:
            for key, value in result[0].items():
                writer.writerow([key, value])

    time.sleep(3)
except Exception as e:
    print("ERROR TYPE:", type(e))
    print("ERROR:", str(e))
