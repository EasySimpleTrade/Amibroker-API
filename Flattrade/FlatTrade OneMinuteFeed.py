#import requests
#import pyotp
#import hashlib
#from urllib.parse import urlparse, parse_qs
import json
from datetime import datetime, timedelta, timezone
import threading
import websocket
import pandas as pd
import time
import csv
import win32com.client
import pythoncom


def read_csv_dict(file_path):
    data_dict = {}
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            key, value = row
            data_dict[key] = value
    return data_dict


#Inputs
login_file = r'R:\FlattradeLogin1.txt'
master_file = r'C:\API\ScripMaster.csv'
rtd_file = r'R:\OneMinuteFeed.csv'


base_url = "https://piconnect.flattrade.in/PiConnectTP/"
wss_url = "wss://piconnect.flattrade.in/PiConnectWSTp/" 

login_dict = read_csv_dict(login_file)
user_id = login_dict['user']
jkey = login_dict['token']
act_id = user_id
print(f"User ID: {user_id}")
print(f"JKey: {jkey}")

#time.sleep(5)

# Define the function to get current time with milliseconds
def pc_time():
    return datetime.now().strftime('%H:%M:%S.%f')[:-2]  # Keep two decimal places

#Convert timestamp to IST Function
def epoch_to_ist(unix_timestamp):
    utc_time = datetime.fromtimestamp(int(unix_timestamp), timezone.utc)    
    # Define IST timezone (UTC +5:30)
    ist_time = utc_time + timedelta(hours=5, minutes=30)    
    return ist_time

# Symbol Master Function
def symbol_master(file_path):
    global symbol_mapping, inst_tokens
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(file_path)

        # Convert the relevant columns to strings and strip any extra spaces
        df['Token'] = df['Token'].apply(lambda x: str(int(x)) if pd.notnull(x) else '').str.strip()
        df['Symbol'] = df['Symbol'].astype(str).str.strip()
        df['Exchange'] = df['Exchange'].astype(str).str.strip()

        # Create symbol mapping dictionary with 'Token' as key and 'Symbol' as value
        symbol_mapping = dict(zip(df['Token'], df['Symbol']))

        # Create a list of dictionaries with 'instrument_token' and 'exchange_segment'
        inst_tokens = [
            f"{row['Exchange']}|{row['Token']}"
            for _, row in df.iterrows()
        ]

        print(f"Loaded symbol mapping and instrument tokens from {file_path}")
    except Exception as e:
        print(f"Error loading data from CSV: {e}")

# Exchange Timing Function
NSE_BSE_START = datetime.strptime("09:15:00", "%H:%M:%S").time()
NSE_BSE_END = datetime.strptime("15:29:59", "%H:%M:%S").time()
CDS_START = datetime.strptime("09:00:00", "%H:%M:%S").time()
CDS_END = datetime.strptime("16:59:59", "%H:%M:%S").time()
MCX_SUMMER_END = datetime.strptime("23:54:59", "%H:%M:%S").time()
MCX_WINTER_END = datetime.strptime("23:29:59", "%H:%M:%S").time()
MCX_START = datetime.strptime("09:00:00", "%H:%M:%S").time()

def exchange_timing(exchange, date_time):
    time = date_time.time()  # Extract time from the datetime object
    month = date_time.month  # Extract the month once

    if exchange in ['NSE', 'BSE', 'NFO', 'BFO']:
        return NSE_BSE_START <= time <= NSE_BSE_END

    elif exchange == 'CDS':
        return CDS_START <= time <= CDS_END

    elif exchange == 'MCX':
        # Different end times based on the month
        mcx_end = MCX_SUMMER_END if 4 <= month <= 10 else MCX_WINTER_END
        return MCX_START <= time <= mcx_end

    # If exchange is not in the list, allow by default
    print(f"No time filtering for exchange: {exchange}")
    return True


def on_open(websocket_app):
    print("WebSocket connection opened")
    payload = {
        "t": "c",
        "uid": userid,
        "actid": actid,
        "susertoken": susertoken,
        "source": "API"
    }
    print("WebSocket connection requesting")
    websocket_app.send(json.dumps(payload)) 

def on_error(websocket_app, error):
    print(pc_time())
    print(f"WebSocket error: {error}")

def on_close(websocket_app, close_status_code, close_msg):
    print(pc_time())
    print(f"WebSocket closed: {close_status_code}, {close_msg}")

def ws_run_forever(websocket_app, stop_event):
    while not stop_event.is_set():
        try:
            websocket_app.run_forever(ping_interval=3, ping_payload='{"t":"h"}')
            print(f"WebSocket run forever: {pc_time()}")
        except Exception as e:
            print(f"WebSocket run_forever ended in exception: {e}")
        # Sleep for a short period before attempting to reconnect
        time.sleep(2)

def close_websocket(websocket_app, stop_event):
    print(pc_time())
    stop_event.set() 
    websocket_app.close() 
    print("WebSocket connection closed.")

    

# Function to start the WebSocket connection
def start_websocket(wssurl, user_id, act_id, user_token, 
                    ws_message_callback=None, ws_open_callback=None, ws_close_callback=None, ws_error_callback=None):
    global on_message, on_open, on_close, on_error
    global userid, actid, susertoken
    
    # Assigning values to global variables
    userid = user_id
    actid = act_id
    susertoken = user_token
    
    # Assigning callbacks
    on_message = ws_message_callback
    on_open = ws_open_callback if ws_open_callback else on_open  # Use custom callback if provided
    on_close = ws_close_callback
    on_error = ws_error_callback

    stop_event = threading.Event()
    
    url = f"{wssurl}?access_token={user_token}"
    print(f"Connecting to {url}")
    
    # Creating a WebSocketApp instance
    websocket_app = websocket.WebSocketApp(url,
                                           on_message=on_message,
                                           on_error=on_error,
                                           on_close=on_close,
                                           on_open=on_open)
    
    # Start the WebSocket in a separate thread
    ws_thread = threading.Thread(target=ws_run_forever, args=(websocket_app, stop_event))
    ws_thread.daemon = True
    ws_thread.start()

    return websocket_app, stop_event  # Return the WebSocket app and stop event

def subscription(feed_type="tick", action="subscribe", batch_size=32):
    try:
        print('Subscribing Tokens')
        for i in range(0, len(inst_tokens), batch_size):
            token_batch = inst_tokens[i:i + batch_size]
            values = {}
            
            # Determine the action (subscribe/unsubscribe) and feed type
            if action == "subscribe":
                if feed_type == "tick":
                    values['t'] = 't'
                elif feed_type == "depth":
                    values['t'] = 'd'
                else:
                    values['t'] = str(feed_type)
            elif action == "unsubscribe":
                if feed_type == "tick":
                    values['t'] = 'u'
                elif feed_type == "depth":
                    values['t'] = 'ud'

            # Handle instrument (single or list)
            if isinstance(token_batch, list):
                values['k'] = '#'.join(token_batch)
            else:
                values['k'] = token_batch

            data = json.dumps(values)
            
            # Check WebSocket connection and send data
            if websocket_app and websocket_app.sock.connected:
                websocket_app.send(data)
            else:
                print("WebSocket is not connected.")
            
            #print(f"{action.capitalize()}d batch {i//batch_size + 1}")
            time.sleep(0.1)
        print('Subscribed')  
        
    except Exception as e:
        print(f"Error during {action}: {e}")

# Variables initialization
last_ltp = {}  # Dictionary to store the last LTP for each token
previous_ltp = {}  # Dictionary to store the previous LTP for each token
last_oi = {}  # Dictionary to store the last OI for each token
last_volume = {}  # Dictionary to store the last volume for each token
cumulative_tick_volume = {}  # Cumulative tick volumes
last_processed_time = {}  # Last processed time per token
open_price = {}  # Open price per token
high_price = {}  # High price per token
low_price = {}  # Low price per token
close_price = {}  # Close price per token
recent_messages = []  # List for recent messages

def on_message(websocket_app, message):
    global last_oi, last_volume, cumulative_tick_volume, last_processed_time
    global open_price, high_price, low_price, close_price
    global recent_messages

    # Extract message type and basic details
    message = json.loads(message)
    msg_type = message.get('t')
    exchange = message.get('e')
    token = message.get('tk')
    timestamp = message.get('ft')  # Unix timestamp
    msg_status = message.get('s')
    
    if msg_type == 'ck' and msg_status == 'OK':
        print("WebSocket Connected")
        subscription(feed_type="depth", action="subscribe", batch_size=32)

    # Convert timestamp to IST and split into date and time
    if timestamp:
        ist_time = epoch_to_ist(timestamp)
        date_str = ist_time.strftime('%d-%m-%Y')  # Date in DD-MM-YYYY format
        time_str = ist_time.strftime('%H:%M:%S')  # Time in HH:MM:SS format
    else:
        ist_time = datetime.now()
        date_str = ist_time.strftime('%d-%m-%Y')
        time_str = ist_time.strftime('%H:%M:%S')
        #print(f"{date_str} {time_str} {message}")
        return

    # Apply symbol mapping for token
    if token in symbol_mapping:
        mapped_symbol = symbol_mapping[token]

    # Check if within exchange timing
    if not exchange_timing(exchange, ist_time):
        return

    if msg_type in ['tk', 'dk']:  # Acknowledge message (initialize values)
        oi = message.get('oi')  # Open interest
        if oi is not None:
            last_oi[token] = oi  # Initialize and store the OI

    elif msg_type in ['tf', 'df']:  # Feed message
        ltp = message.get('lp')  # Last traded price
        if ltp is not None:
            volume = message.get('v')  # Volume
            oi = message.get('oi')  # Open interest

            # Use last known OI if provided OI is 0 or not present
            if oi is None or oi == 0:
                oi = last_oi.get(token, 0)
            else:
                last_oi[token] = oi  # Update last known OI

            # Convert ltp to float
            try:
                ltp = float(ltp)
            except ValueError:
                print(f"Warning: Unable to convert ltp to float for token {token}")
                return

            # Process tick volume
            tick_volume = 0  # Default for indices (where volume is None)
            if volume is not None:
                try:
                    current_volume = int(volume)  # Total volume of the day
                    if token not in last_volume:
                        last_volume[token] = current_volume
                    else:
                        previous_volume = last_volume[token]
                        tick_volume = current_volume - previous_volume
                        last_volume[token] = current_volume
                except ValueError:
                    print(f"Warning: Unable to convert volume to integer for token {token}: {volume}")
                    return

            # Handle cumulative tick volume and OHLC data per minute
            current_time = datetime.strptime(f'{date_str} {time_str}', '%d-%m-%Y %H:%M:%S')

            # Reset cumulative tick volume and OHLC for new minute
            if token not in last_processed_time or last_processed_time[token].minute != current_time.minute:
                cumulative_tick_volume[token] = 0  # Reset cumulative tick volume
                open_price[token] = ltp  # Open price is the first LTP of the minute
                high_price[token] = ltp  # Initialize high with current LTP
                low_price[token] = ltp  # Initialize low with current LTP
                close_price[token] = ltp  # Initially, close is same as open
                last_processed_time[token] = current_time  # Update last processed time
            else:
                # Update OHLC during the minute
                if ltp > high_price[token]:
                    high_price[token] = ltp
                if ltp < low_price[token]:
                    low_price[token] = ltp
                close_price[token] = ltp

            # Accumulate tick volume for the current minute
            cumulative_tick_volume[token] += tick_volume

            # Format time string to show '00' seconds
            formatted_time = current_time.strftime('%H:%M:00')

            # Prepare output message
            output = [
                "OUT>",
                mapped_symbol,
                date_str,
                formatted_time,  # Time with '00' seconds
                str(open_price[token]),  # Open price
                str(high_price[token]),  # High price
                str(low_price[token]),  # Low price
                str(close_price[token]),  # Close price
                str(cumulative_tick_volume[token]),  # One-minute cumulative tick volume
                str(oi)  # Last known OI
            ]
            output_str = ",".join(output)

            # Print the final output
            #print(output_str)

            # Recent messages processing
            current_time = datetime.now()
            recent_messages.append({
                "symbol": mapped_symbol,
                "date": date_str,
                "time": formatted_time,
                "open": open_price[token],
                "high": high_price[token],
                "low": low_price[token],
                "close": close_price[token],
                "tick_volume": cumulative_tick_volume[token],
                "open_interest": oi,
                "timestamp": current_time
            })

            # Keep only messages from the last 3 seconds
            recent_messages = [msg for msg in recent_messages if (current_time - msg['timestamp']).total_seconds() <= 1.5]

    else:
        print("Unknown message type")



def write_to_csv():
    pythoncom.CoInitialize()  # <- required for COM in a new thread
    AB = win32com.client.Dispatch("Broker.Application")
    while True:
        if recent_messages:
            try:
                # Write recent messages to CSV file
                df = pd.DataFrame(recent_messages).drop(columns=['timestamp'])
                df.to_csv(rtd_file, mode='w', index=False)
                # Clear recent_messages after writing
                #recent_messages.clear()
                # Optional: Add a small delay between write operations
                #time.sleep(0.2)
                #print(pc_time())
                #print("Importing to Broker.Application...")
                AB = win32com.client.Dispatch("Broker.Application")
                AB.Import(0, rtd_file, "OneMinuteFeed.format")
                #AB.RefreshAll()
            except Exception as e:
                #print(f"[write_to_csv] Import error: {e}")
                time.sleep(0.1)
                #pc_current_time = datetime.now().strftime('%H:%M:%S')
                #print(f"[{pc_current_time}] Error while writing to CSV: {e}")
        else:
            # Sleep briefly to avoid tight loop when there's no data
            time.sleep(0.2)

    print("CSV writing thread stopped.")

# Function to stop the CSV thread
def stop_csv_thread():
    csv_stop_event.set()  # Signal the CSV thread to stop
    csv_thread.join() 

#inst_tokens = ['MCX|429116']
symbol_master(master_file)
#symbol_master(r'C:\API\OptionsMaster.csv')
#symbol_master(r'C:\API\ScripMaster.csv')


#Start Web Socket
websocket_app, stop_event = start_websocket(
    wssurl=wss_url,
    user_id=user_id,   
    act_id=act_id,     
    user_token=jkey,  
    ws_message_callback=on_message,  
    ws_open_callback=on_open,      
    ws_close_callback=on_close,     
    ws_error_callback=on_error      
)

#time.sleep(5)
#subscription(feed_type="depth", action="subscribe", batch_size=32)
# Start write_to_csv in a separate thread to continuously write recent_messages to CSV
print('CSV Writing Started')
csv_thread = threading.Thread(target=write_to_csv)
csv_thread.daemon = True  # Daemonize the thread so it exits when the main program does
csv_thread.start()
#time.sleep(60)
input("Press Enter to exit...")
