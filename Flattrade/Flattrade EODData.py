import asyncio
import aiohttp
import csv
import json
from datetime import datetime
import os
import ssl
import certifi
import sys

# Inputs
'''
fromdate = '01-01-2023'
todate = '09-06-2025'
eod_import='Yes'
eod_delete='No'
master_file = 'NiftyToken'
batch_size = int('25')
'''
fromdate = sys.argv[1]
todate = sys.argv[2]
eod_import=sys.argv[3]
eod_delete=sys.argv[4]
master_file = sys.argv[5]
batch_size = int(sys.argv[6])

print("start_date="+fromdate)
print("end_date="+todate)
print("do_import="+eod_import)
print("do_delete="+eod_delete)
print("master_file="+master_file)
print("batch_size="+str(batch_size))


input_file = fr'C:\API\{master_file}.csv'
max_retries = 5
login_file = r'R:\FlattradeLogin1.txt'
output_dir = r'C:\HistoricalData'
base_url = 'https://piconnect.flattrade.in/PiConnectTP/'
eod_ep = 'EODChartData'
eod_url = base_url + eod_ep

# Epoch
def epoch(date, time):
    dt = datetime.strptime(f"{date} {time}", '%d-%m-%Y %H:%M:%S')
    return int(dt.timestamp())

startdt = epoch(fromdate, '00:00:00')
enddt = epoch(todate, '23:59:59')

# Read login token
def read_csv_dict(file_path):
    data_dict = {}
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            key, value = row
            data_dict[key] = value
    return data_dict

# Read symbol list
def read_symbols(file_path):
    with open(file_path, mode='r') as file:
        return [row[0].strip() for row in csv.reader(file) if row]

# Write CSV
def write_data_to_csv(symbol, raw_list):
    filepath = os.path.join(output_dir, f"{symbol}.csv")

    try:
        data_list = [json.loads(item) for item in raw_list]  # Each item is a JSON string
    except Exception as e:
        print(f"JSON parsing error for {symbol}: {e}")
        return

    if not data_list:
        print(f"Empty data for {symbol}")
        return

    with open(filepath, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])

        for item in data_list:
            try:
                if 'ssboe' in item:
                    dt = datetime.fromtimestamp(int(item['ssboe']))
                    date_str = dt.strftime('%d-%m-%Y')
                else:
                    dt = datetime.strptime(item['time'], '%d-%b-%Y')
                    date_str = dt.strftime('%d-%m-%Y')
                #time_str = "09:15:00"
                into = item.get('into', '')
                inth = item.get('inth', '')
                intl = item.get('intl', '')
                intc = item.get('intc', '')
                intv = int(float(item.get('intv', 0)))

                writer.writerow([date_str, into, inth, intl, intc, intv])
            except Exception as e:
                print(f"Error writing row for {symbol}: {e}")

    print(f" Saved: {filepath}")

    # Optional Amibroker import
    if eod_import == 'Yes':
        try:
            import win32com.client
            AB = win32com.client.Dispatch("Broker.Application")
            AB.Import(0, filepath, "default.format")
        except Exception as e:
            print(f" Error during import for {symbol}: {str(e)}")

        # Optional file delete
        if eod_delete == 'Yes':
            try:
                os.remove(filepath)
            except Exception as e:
                print(f" Warning: Could not delete {filepath} - {str(e)}")


# Async fetch with retries
async def fetch_symbol_data(session, raw_symbol, ssl_context):
    # For API use, replace '&' with 'AND' or similar safe substitute
    formatted_symbol = f"NSE:{raw_symbol.replace('&', '%26')}-EQ"

    jdata = {
        "sym": formatted_symbol,
        "from": str(startdt),
        "to": str(enddt),
    }
    payload = f'jData={json.dumps(jdata)}&jKey={jkey}'

    for attempt in range(1, max_retries + 1):
        try:
            async with session.post(eod_url, data=payload, ssl=ssl_context, timeout=15) as response:
                result = await response.json()
                write_data_to_csv(raw_symbol, result)  # Keep original symbol for filename
                return
        except Exception as e:
            print(f" Error fetching {raw_symbol} (Attempt {attempt}): {e} - Retrying in 2s...", flush=True)
            await asyncio.sleep(2)

    print(f"❗ Failed after {max_retries} attempts: {raw_symbol}", flush=True)


# Run in batches
async def run_batches(symbols):
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            tasks = [fetch_symbol_data(session, sym, ssl_context) for sym in batch]
            await asyncio.gather(*tasks)



    
    
#Execute    

login_dict = read_csv_dict(login_file)
jkey = login_dict['token']
symbols = read_symbols(input_file)

asyncio.run(run_batches(symbols))
print('Completed')
input("Press Enter to exit...")
