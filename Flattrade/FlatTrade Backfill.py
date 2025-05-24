import pandas as pd
import asyncio
import aiohttp
import json
from datetime import datetime, timezone, timedelta
import nest_asyncio
import csv
import os
import win32com.client
import sys


#Inputs
master_list = r'C:\API\ScripMaster.csv' #Check Drive and Folder Name
login_file = r"R:\FlattradeLogin1.txt" #Check Drive Letter
output_dir = r'R:' #Check Drive Letter

base_url = "https://piconnect.flattrade.in/PiConnectTP/"
historical_ep = 'TPSeries'

#num_of_days = 7
#batch_size = 10
num_of_days = int(sys.argv[1])
batch_size = int(sys.argv[2])
start_date = (datetime.now() - timedelta(days=num_of_days)).strftime('%d-%m-%Y')
end_date = datetime.today().strftime('%d-%m-%Y')


def read_csv_dict(file_path):
    data_dict = {}
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            key, value = row
            data_dict[key] = value
    return data_dict


# PC Timw now
def pc_time():
    return datetime.now().strftime('%d-%m-%Y %H:%M:%S')

#Timestamp to IST
def epoch_to_ist(unix_timestamp):
    utc_time = datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc)
    ist_time = utc_time.astimezone(timezone(timedelta(hours=5, minutes=30)))
    return ist_time.strftime('%d-%m-%Y %H:%M:%S')

#Date,Time to UnixTime Stamp
def epoch(date, time):
    dt = datetime.strptime(f"{date} {time}", '%d-%m-%Y %H:%M:%S')
    return int(dt.timestamp())

async def fetch_symbol_data(session, url, payload, symbol, token, retries=5, delay=3):
    RETRYABLE_STATUSES = {400, 524, 500, 502, 503}

    for attempt in range(retries):
        try:
            async with session.post(url, data=payload) as response:
                if response.status == 200:
                    data = await response.json()

                    if isinstance(data, str):
                        print(f"Error: Data for {symbol} returned as a string, skipping.")
                        return []

                    rows = []
                    for record in data:
                        try:
                            if record.get("stat") == "Ok":
                                ist_time = epoch_to_ist(record['ssboe'])  # should be int-compatible
                                date, time = ist_time.split(' ')
                                rows.append([
                                    symbol, date, time,
                                    record['into'], record['inth'],
                                    record['intl'], record['intc'],
                                    record['intv'], record['oi']
                                ])
                        except AttributeError as e:
                            if "'str' object has no attribute 'get'" in str(e):
                                print(f"Error: Data processing failed for {symbol} with error: {str(e)}. No retry.")
                                return []  # Skip retrying
                            else:
                                print(f"Attempt {attempt + 1}: Attribute error in record for {symbol}: {str(e)}")
                    return rows

                elif response.status in RETRYABLE_STATUSES:
                    print(f"Attempt {attempt + 1}: Status {response.status} for {symbol}, retrying...")
                else:
                    print(f"Error: {symbol} {token} status {response.status}, not retrying.")
                    return []

        except Exception as e:
            if isinstance(e, AttributeError) and "'str' object has no attribute 'get'" in str(e):
                print(f"{symbol} Error: {str(e)}. No retry.")
                return []  # Skip retrying
            print(f"Attempt {attempt + 1}: Exception fetching {symbol} {token}: {str(e)}")

        if attempt < retries - 1:
            await asyncio.sleep(delay)

    print(f"Max retries reached for {symbol} {token}")
    return []


async def hist_data_combined(base_url, end_point, user_id, jkey, master_list, startdate, enddate, output_dir, batchsize=25):
    df_master = pd.read_csv(master_list, names=["Exchange", "Symbol", "Token"])
    df_master = df_master[df_master['Exchange'] != 'Exchange']  # Remove header rows

    url = f"{base_url}{end_point}"

    async with aiohttp.ClientSession() as session:
        for i in range(0, len(df_master), batchsize):
            batch = df_master.iloc[i:i + batchsize]
            tasks = []

            for _, row in batch.iterrows():
                jdata = {
                    "uid": user_id,
                    "exch": row['Exchange'],
                    "token": row['Token'],
                    "st": str(startdate),
                    "et": str(enddate),
                    "intrv": '1'
                }
                payload = f'jData={json.dumps(jdata)}&jKey={jkey}'
                tasks.append(fetch_symbol_data(session, url, payload, row['Symbol'], row['Token']))

            #print(f"\nStarting batch {i // batchsize + 1}")
            results = await asyncio.gather(*tasks)

            # Flatten list of lists
            all_rows = [row for result in results for row in result]

            if all_rows:
                df = pd.DataFrame(all_rows, columns=[
                    'Symbol', 'Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'
                ])
                combined_file = f"{output_dir}/batch_{i//batchsize + 1}.csv"
                df.to_csv(combined_file, index=False)

                try:
                    AB = win32com.client.Dispatch("Broker.Application")
                    AB.Import(0, combined_file, "EST.Format")
                    os.remove(combined_file)
                    #print(f"Batch {i // batchsize + 1} done.")
                except Exception as e:
                    print(f"Import/Delete error: {str(e)}")
            else:
                print(f"No data fetched in batch {i // batchsize + 1}")





#Execute
startdate = epoch(start_date, '00:00:00')
enddate = epoch(end_date, '23:59:59')

            
login_dict = read_csv_dict(login_file)
user_id = login_dict['user']
jkey = login_dict['token']
print(f"User ID: {user_id}")
print(f"JKey: {jkey}")


print(pc_time())
print(start_date , "-", end_date)
asyncio.run(hist_data_combined(base_url, historical_ep, user_id, jkey, master_list, startdate, enddate, output_dir, batch_size))
print(pc_time())
