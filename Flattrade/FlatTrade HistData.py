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
import csv
import os
import win32com.client
import sys


#Inputs
login_file = r'R:\FlattradeLogin1.txt'
output_dir = r'C:\API\HistoricalData'
base_url = 'https://piconnect.flattrade.in/PiConnectAPI/'
historical_ep = 'TPSeries'
format_file = 'Candle'

# Max seconds to wait for ONE request. If the server does not answer in this time,
# the request is cancelled and retried, instead of hanging forever.
# Increase this if you download a very large date range with 1-minute data.
REQUEST_TIMEOUT = 120


'''
start_date = '02-05-2025' #datetime.today().strftime('%d-%m-%Y')
end_date = '02-05-2025' #datetime.today().strftime('%d-%m-%Y')
do_import = 'No'
do_delete = 'Yes'
master_file = 'Temp'
time_frame = '1'
batch_size = 25
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

# Set to True when the broker says the session/token has expired.
# Remaining symbols are skipped so you can login again and re-run.
session_expired = False


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

#Timestamp to IST
def epoch_to_ist(unix_timestamp):
    utc_time = datetime.fromtimestamp(int(unix_timestamp), tz=timezone.utc)
    return utc_time.astimezone(
        timezone(timedelta(hours=5, minutes=30))
    )

#Date,Time to UnixTime Stamp
def epoch(date, time):
    dt = datetime.strptime(f"{date} {time}", '%d-%m-%Y %H:%M:%S')
    return int(dt.timestamp())



# ======================================================================
# BROKER SPECIFIC PART (for other brokers, change this function:
# URL / payload format / response field names / error handling)
# ======================================================================
async def hist_data_single(session, base_url, end_point, user_id, jkey, symbol, exchange, token,
                           startdate, enddate, output_dir, time_frame, format_file,
                           retries=5, delay=2,
                           do_import='Yes', do_delete='Yes'):
    global session_expired

    # Session already expired in an earlier symbol, no need to call the server again
    if session_expired:
        return

    url = f"{base_url}{end_point}"
    RETRYABLE_STATUSES = {400, 524, 500, 502, 503}

    jdata = {
        "uid": user_id,
        "exch": exchange,
        "token": token,
        "st": str(startdate),
        "et": str(enddate),
        "intrv": time_frame
    }
    payload = f'jData={json.dumps(jdata)}&jKey={jkey}'

    for attempt in range(retries):
        try:
            async with session.post(url, data=payload) as response:
                if response.status == 200:
                    data = await response.json()

                    if isinstance(data, str):
                        print(f"Error: Data for {symbol} returned as a string, no retry needed.")
                        return

                    # Error / no-data reply comes as a dict, e.g. {"stat":"Not_Ok","emsg":"..."}
                    if isinstance(data, dict):
                        emsg = data.get('emsg', str(data))
                        print(f"Error: {symbol} {token}: {emsg}")
                        if 'session' in str(emsg).lower():
                            session_expired = True
                        return

                    rows = []
                    for record in data:
                        try:
                            if record.get("stat") == "Ok":
                                ist_time = epoch_to_ist(record['ssboe'])

                                date_str = ist_time.strftime('%d-%m-%Y')
                                time_str = ist_time.strftime('%H:%M:%S')
                                rows.append([
                                    symbol, date_str, time_str,
                                    record['into'],  # Open
                                    record['inth'],  # High
                                    record['intl'],  # Low
                                    record['intc'],  # Close
                                    max(0, float(record['intv'])),  # Volume
                                    record['oi']     # OI
                                ])
                        except AttributeError as e:
                            if "'str' object has no attribute 'get'" in str(e):
                                print(f"Error: Data processing failed for {symbol}: {str(e)}. No retry.")
                                return
                            else:
                                print(f"Attempt {attempt + 1}: Attribute error for {symbol}: {str(e)}")

                    # Nothing to save or import
                    if not rows:
                        print(f"No data for {symbol}, skipped.")
                        return

                    df = pd.DataFrame(rows, columns=['Symbol', 'Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
                    output_file = f"{output_dir}/{symbol}.csv"
                    df.to_csv(output_file, index=False)

                    # ---------- Import to AmiBroker (not broker specific) ----------
                    if do_import == 'Yes':
                        imported = False
                        try:
                            AB = win32com.client.Dispatch("Broker.Application")
                            AB.Import(0, output_file, format_file+".format")
                            imported = True
                        except Exception as e:
                            print(f"Error during import for {symbol}: {str(e)}")

                        # Delete the CSV only if the import worked, otherwise keep it
                        if do_delete == 'Yes':
                            if imported:
                                try:
                                    os.remove(output_file)
                                except Exception as e:
                                    print(f"Warning: Could not delete {output_file} - {str(e)}")
                            else:
                                print(f"Import failed, CSV kept: {output_file}")
                    return

                elif response.status in RETRYABLE_STATUSES:
                    print(f"Attempt {attempt + 1}: Retryable status {response.status} for {symbol}, retrying...")
                else:
                    print(f"Error: Failed to fetch data for {symbol} {token}, status code {response.status}, not retrying.")
                    return

        except aiohttp.ClientError as e:
            print(f"Attempt {attempt + 1}: Client error for {symbol} {token}: {str(e)}")
        except asyncio.TimeoutError:
            print(f"Attempt {attempt + 1}: Timeout (>{REQUEST_TIMEOUT}s) for {symbol} {token}")
        except Exception as e:
            print(f"Attempt {attempt + 1}: Exception for {symbol} {token}: {str(e)}")

        # Only sleep if it's not the last attempt
        if attempt < retries - 1:
            await asyncio.sleep(delay)
        else:
            print(f"Max retries reached for {symbol}. Giving up.")




async def hist_data_list(base_url, end_point, user_id, jkey, master_list,
                         startdate, enddate, output_dir, time_frame, format_file,
                         do_import='Yes', do_delete='Yes'):
    timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        df_master = pd.read_csv(master_list, names=["Exchange", "Symbol", "Token"], usecols=["Exchange", "Symbol", "Token"])
        df_master = df_master[df_master['Exchange'] != 'Exchange']  
        #print(df_master)

        for i in range(0, len(df_master), batch_size):
            print(f"\nProcessing batch {i // batch_size + 1}: symbols {i + 1} to {i + len(df_master.iloc[i:i + batch_size])}")

            tasks = []
            batch = df_master.iloc[i:i + batch_size]

            for _, row in batch.iterrows():
                task = hist_data_single(
                    session, base_url, end_point, user_id, jkey,
                    row['Symbol'], row['Exchange'], row['Token'],
                    startdate, enddate, output_dir, time_frame, format_file,
                    do_import=do_import, do_delete=do_delete
                )
                tasks.append(task)

            try:
                await asyncio.gather(*tasks)
            except Exception as e:
                print(f"Error during batch {i // batch_size + 1}: {str(e)}")

            if session_expired:
                print("\n*** SESSION EXPIRED. Login again and re-run. Remaining symbols skipped. ***")
                break





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
asyncio.run(hist_data_list(base_url, historical_ep, user_id, jkey, master_list, startdate, enddate, output_dir,
                           time_frame, format_file, do_import=do_import, do_delete=do_delete))
print(pc_time())
input("Press Enter to exit...")
