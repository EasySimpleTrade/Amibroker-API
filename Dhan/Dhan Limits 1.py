'''
VALLAKKOTTAI MURUGAN THUNAI
Easy Simple Trading Solutions
Telegram @easysimpletradeupdates
Website https://easysimpletrade.blogspot.com
Youtube https://www.youtube.com/@easysimpletrade
GitHub https://github.com/EasySimpleTrade
'''

import requests
import csv
import sys

#Inputs
login_file = r'R:\DhanLogin1.txt'
limits_file = r'R:\DhanLimits1.txt'

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
JWT = login_dict['access']

#JWT = 'eyJ0eXAiOiJKV1QiLCJh......'
'''

JWT = sys.argv[1]


print(JWT)

url = "https://api.dhan.co/v2/fundlimit"

headers = {
    "Content-Type": "application/json",
    "access-token": JWT  
}

limits_response = requests.get(url, headers=headers)

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
