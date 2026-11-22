'''
VALLAKKOTTAI MURUGAN THUNAI
Easy Simple Trading Solutions
Telegram @easysimpletradeupdates
Website https://easysimpletrade.blogspot.com
Youtube https://www.youtube.com/@easysimpletrade
GitHub https://github.com/EasySimpleTrade
'''

#Libraries
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
import ssl
import certifi


#Inputs
login_file = r'R:\AliceBlueLogin1.txt'
output_dir = r'C:\API\HistoricalData'
base_url = 'https://a3.aliceblueonline.com/'
historical_ep = 'open-api/od/ChartAPIService/api/chart/history'
format_file = 'Candle'

# Index tokens. For these, payload exchange is sent as exchange + "::index"
index_tokens = {'26000', '26009', '26017', '26037', '26074', '26013',
                '26008', '26018', '26020', '26021', '26023', '26029',
                '26030', '26031', '1'}


'''
start_date = '01-10-2026' #Start date
end_date = '01-10-2026' #End date
do_import = 'No' #Import to amibroker 'Yes' 'No'
do_delete = 'Yes' #Delete downloaded file 'Yes' 'No' it work if do_import == 'Yes'
master_file = 'ScripMaster' #Master File Name IndexMaster ScripMaster
time_frame = '1' #timeframe '1' one minute 'D' daily
batch_size = 5
'''
start_date = sys.argv[1]
end_date = sys.argv[2]
do_import = sys.argv[3]
do_delete = sys.argv[4]
master_file = sys.argv[5]
time_frame = sys.argv[6]
batch_size = int(sys.argv[7])

print("start_date="+start_date)
print("end_date="+end_date)
print("do_import="+do_import)
print("do_delete="+do_delete)
print("master_file="+master_file)
print("time_frame="+time_frame)
print("batch_size="+str(batch_size))


master_list = fr'C:\API\Files\{master_file}.csv'

if time_frame == 'D':
    format_file = 'EOD'
else:
    format_file = 'Candle'


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


# PC Time now
def pc_time():
    return datetime.now().strftime('%d-%m-%Y %H:%M:%S')

'''#Timestamp to IST
def epoch_to_ist(unix_timestamp):
    utc_time = datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc)
    return utc_time.astimezone(
        timezone(timedelta(hours=5, minutes=30))
    )'''

#Date,Time to UnixTime Stamp
def epoch(date, time):
    dt = datetime.strptime(f"{date} {time}", '%d-%m-%Y %H:%M:%S')
    return int(dt.timestamp())

'''
#Exchange timing
NSE_BSE_START = datetime.strptime("09:15:00", "%H:%M:%S").time()
NSE_BSE_END = datetime.strptime("15:29:59", "%H:%M:%S").time()

def exchange_timing(exchange, date_time):
    time = date_time.time()

    if exchange in ['NSE', 'BSE', 'NFO', 'BFO']:
        return NSE_BSE_START <= time <= NSE_BSE_END

    return True
'''


async def hist_data_single(session, base_url, end_point, user_id, jkey, symbol, exchange, token,
                           startdate, enddate, output_dir, retries=5, delay=2,
                           do_import='Yes', do_delete='Yes'):
    url = f"{base_url}{end_point}"
    RETRYABLE_STATUSES = {400, 524, 500, 502, 503}

    headers = {
        "Authorization": f"Bearer {jkey}",
        "Content-Type": "application/json"
    }

    # Index tokens need "::index" added to the exchange name
    if str(token) in index_tokens:
        exchange_name = exchange + "::index"
    else:
        exchange_name = exchange

    payload = {
        "token": str(token),
        "resolution": str(time_frame),
        "from": str(startdate) + '000',
        "to": str(enddate) + '000',
        "exchange": exchange_name
    }

    ssl_context = ssl.create_default_context(cafile=certifi.where())

    for attempt in range(retries):
        try:
            async with session.post(url, json=payload, headers=headers, ssl=ssl_context) as response:
                if response.status == 200:
                    data = await response.json()

                    if data.get('stat') != 'Ok':
                        print(f"No data : {symbol}")
                        return

                    records = data.get('result', [])

                    if len(records) == 0:
                        print(f"No candles : {symbol}")
                        return

                    rows = []

                    for record in records:

                        dt = datetime.strptime(
                            record['time'],
                            '%Y-%m-%d %H:%M:%S'
                        )

                        date = dt.strftime('%d-%m-%Y')
                        time = dt.strftime('%H:%M:%S')

                        rows.append([
                            symbol,
                            date,
                            time,
                            record['open'],
                            record['high'],
                            record['low'],
                            record['close'],
                            record['volume'],
                            0
                        ])

                    df = pd.DataFrame(
                        rows,
                        columns=[
                            'Symbol',
                            'Date',
                            'Time',
                            'Open',
                            'High',
                            'Low',
                            'Close',
                            'Volume',
                            'OI'
                        ]
                    )

                    # Daily data has no time, so drop the Time column
                    if time_frame == 'D':
                        df = df.drop(columns=['Time'])

                    output_file = f"{output_dir}/{symbol}.csv"

                    df.to_csv(
                        output_file,
                        index=False
                    )

                    #------

                    if do_import == 'Yes':
                        try:
                            AB = win32com.client.Dispatch("Broker.Application")
                            AB.Import(0, output_file, format_file+".format")
                        except Exception as e:
                            print(f"Error during import for {symbol}: {str(e)}")

                        if do_delete == 'Yes':
                            try:
                                os.remove(output_file)
                            except Exception as e:
                                print(f"Warning: Could not delete {output_file} - {str(e)}")
                    return

                elif response.status in RETRYABLE_STATUSES:
                    print(f"Attempt {attempt + 1}: Retryable status {response.status} for {symbol}, retrying...")
                else:
                    print(f"Error: Failed to fetch data for {symbol} {token}, status code {response.status}, not retrying.")
                    return

        except aiohttp.ClientError as e:
            print(f"Attempt {attempt + 1}: Client error for {symbol} {token}: {str(e)}")
        except Exception as e:
            print(f"Attempt {attempt + 1}: Exception for {symbol} {token}: {str(e)}")

        # Only sleep if it's not the last attempt
        if attempt < retries - 1:
            await asyncio.sleep(delay)
        else:
            print(f"Max retries reached for {symbol}. Giving up.")




async def hist_data_list(base_url, end_point, user_id, jkey, master_list,
                         startdate, enddate, output_dir,
                         do_import='Yes', do_delete='Yes'):
    async with aiohttp.ClientSession() as session:
        df_master = pd.read_csv(master_list, names=["Exchange", "Symbol", "Token"], usecols=["Exchange", "Symbol", "Token"])
        df_master = df_master[df_master['Exchange'] != 'Exchange']  # Filter out header row
        #print(df_master)

        for i in range(0, len(df_master), batch_size):
            print(f"\nProcessing batch {i // batch_size + 1}: symbols {i + 1} to {i + len(df_master.iloc[i:i + batch_size])}")

            tasks = []
            batch = df_master.iloc[i:i + batch_size]

            for _, row in batch.iterrows():
                task = hist_data_single(
                    session, base_url, end_point, user_id, jkey,
                    row['Symbol'], row['Exchange'], row['Token'],
                    startdate, enddate, output_dir,
                    do_import=do_import, do_delete=do_delete
                )
                tasks.append(task)

            try:
                await asyncio.gather(*tasks)
            except Exception as e:
                print(f"Error during batch {i // batch_size + 1}: {str(e)}")





#Execute
startdate = epoch(start_date, '00:00:00')
enddate = epoch(end_date, '23:59:59')            
login_dict = read_csv_dict(login_file)
user_id = login_dict['user']
jkey = login_dict['token']


#print(f"User ID: {user_id}")
#print(f"JKey: {jkey}")

print(pc_time())
print(start_date , "-", end_date)
asyncio.run(hist_data_list(base_url, historical_ep, user_id, jkey, master_list, startdate, enddate, output_dir, do_import=do_import, do_delete=do_delete))
print(pc_time())
input("Press Enter to exit...")
