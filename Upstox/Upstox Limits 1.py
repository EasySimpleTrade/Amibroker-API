import requests
import csv
import sys
import time

login_file = r'R:\UpstoxLogin1.txt'
limits_file = r"R:\UpstoxLimits1.txt"
limits_url = 'https://api.upstox.com/v3/user/get-funds-and-margin'


'''
# Read CSV as Dictionary
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
# ---------------------------------------------------------
# Read Login
# ---------------------------------------------------------
login_dict = read_csv_dict(login_file)
access_token = login_dict['token']
'''
print(f"Received arguments: {sys.argv[1:]}")

time.sleep(1)

if len(sys.argv) < 2:
    print(f"Expected {sys.argv[0]} <token>")
    print(f"Received arguments: {sys.argv[1:]}")
    time.sleep(5)
    sys.exit(1)
    
access_token = sys.argv[1]

# Recursively flatten nested dictionary
def write_dict_to_csv(writer, data):
    for key, value in data.items():

        if isinstance(value, dict):

            for sub_key, sub_value in value.items():

                if isinstance(sub_value, dict):
                    # Go deeper
                    write_nested_dict(writer, sub_key, sub_value)

                else:
                    writer.writerow([f"{key} {sub_key}", sub_value])

        else:
            writer.writerow([key, value])


# Handle deeper nested dictionaries
def write_nested_dict(writer, parent_key, data):

    for key, value in data.items():

        if isinstance(value, dict):
            write_nested_dict(writer, key, value)

        else:
            writer.writerow([f"{parent_key} {key}", value])



# ---------------------------------------------------------
# Upstox Limits API
# ---------------------------------------------------------



headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {access_token}'
}


try:

    limits_response = requests.get(
        limits_url,
        headers=headers
    )

    limits_data = limits_response.json()

    print(limits_data)


    # -----------------------------------------------------
    # Write CSV
    # -----------------------------------------------------

    with open(
        limits_file,
        mode='w',
        newline=''
    ) as file:

        writer = csv.writer(file)

        # Header
        writer.writerow(['status', limits_data.get('status', '')])

        # Data
        data = limits_data.get('data', {})

        write_dict_to_csv(writer, data)


    time.sleep(3)


except Exception as e:

    print("ERROR TYPE:", type(e))
    print("ERROR:", str(e))
