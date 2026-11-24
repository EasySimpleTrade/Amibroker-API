'''
VALLAKKOTTAI MURUGAN THUNAI
Easy Simple Trading Solutions
Telegram @easysimpletradeupdates
Website https://easysimpletrade.blogspot.com
Youtube https://www.youtube.com/@easysimpletrade
GitHub https://github.com/EasySimpleTrade
'''

#Libraries
import json
from datetime import datetime, timedelta, timezone
import threading
import websocket
import pandas as pd
import time
import csv
import win32com.client
import pythoncom
import requests

# Input
login_file = r'R:\FlatTradeLogin1.txt'
inputs_file = r'C:\API\Files\FlatTradeInputs 1.csv'
master_file = r'C:\API\Files\ScripMaster.csv'
rtd_file = r'R:\FlatTrade Candle Feed.csv'
format_file = 'Candle'
telegram_message = 'FlatTrade Websocket Disconnected'

wss_url = 'wss://piconnect.flattrade.in/PiConnectWSAPI/'


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


# Telegram alert
def send_telegram(channel_id, bot_key, text):
    def _send():
        try:
            #print(f"Telegram Send | channel_id={channel_id} | text={text}")
            response = requests.post(
                f"https://api.telegram.org/bot{bot_key}/sendMessage",
                data={"chat_id": channel_id,"text": text},timeout=5)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()

# To get current PC time with milliseconds
def pc_time():
    return datetime.now().strftime('%H:%M:%S.%f')[:-2]

#Convert timestamp to IST Function
def epoch_to_ist(unix_timestamp):
    utc_time = datetime.fromtimestamp(int(unix_timestamp), timezone.utc)    
    ist_time = utc_time + timedelta(hours=5, minutes=30)    
    return ist_time

# Symbol Master Function
def symbol_master(file_path):
    global symbol_mapping, inst_tokens
    try:
        df = pd.read_csv(file_path)

        df['Token'] = df['Token'].apply(lambda x: str(int(x)) if pd.notnull(x) else '').str.strip()
        df['Symbol'] = df['Symbol'].astype(str).str.strip()
        df['Exchange'] = df['Exchange'].astype(str).str.strip()

        symbol_mapping = dict(zip(df['Token'], df['Symbol']))

        # Instrument tokens in "EXCHANGE|TOKEN" format (vectorized, no row loop)
        inst_tokens = (df['Exchange'] + '|' + df['Token']).tolist()

        print(f"Loaded symbol mapping and instrument tokens from {file_path}")
    except Exception as e:
        print(f"Error loading data from CSV: {e}")


# WebSocket open callback: send authentication message
def on_open(ws):
    print("WebSocket Opened")
    payload = {
        "t": "a",
        "uid": userid,
        "actid": actid,
        "accesstoken": susertoken,
        "source": "API"
    }
    print(f"Sending payload: {json.dumps(payload)}")
    ws.send(json.dumps(payload))
    print(f"WebSocket authentication message sent at {pc_time()}")

# WebSocket error callback
def on_error(ws, error):
    print(f"WebSocket error: {error}")
    if channel_id != "":
        send_telegram(channel_id,bot_key,f"{error}")

# WebSocket close callback
def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket closed: {close_status_code}, {close_msg}")
    if channel_id != "":
        send_telegram(channel_id,bot_key,telegram_message)

# Close WebSocket function
def close_websocket(websocket_app, stop_event):
    """Close the WebSocket connection and stop the thread."""
    stop_event.set()
    websocket_app.close() 
    print("WebSocket connection closed.")

# Keep the WebSocket connection alive and reconnect on failure
def ws_run_forever(websocket_app, stop_event):
    while not stop_event.is_set():
        try:
            websocket_app.run_forever(ping_interval=3, ping_payload='{"t":"h"}')  # Send a ping every 3 seconds
        except Exception as e:
            print(f"WebSocket run_forever ended in exception: {e}")
        # Sleep for a short period before attempting to reconnect
        time.sleep(1)    


# Function to start the WebSocket connection
def start_websocket(wssurl, user_id, act_id, user_token, ws_message_callback=None, 
                    ws_open_callback=None, ws_close_callback=None, ws_error_callback=None):
    global userid, actid, susertoken
    
    # Assigning values to global variables
    userid = user_id
    actid = act_id
    susertoken = user_token

    stop_event = threading.Event()
    
    url = f"{wssurl}"
    print(f"Connecting to {url}")
    
    # Creating a WebSocketApp instance - use the passed callbacks directly
    websocket_app = websocket.WebSocketApp(url,
                                           on_message=ws_message_callback if ws_message_callback else on_message,
                                           on_error=ws_error_callback if ws_error_callback else on_error,
                                           on_close=ws_close_callback if ws_close_callback else on_close,
                                           on_open=ws_open_callback if ws_open_callback else on_open)
    
    # Start the WebSocket in a separate thread
    ws_thread = threading.Thread(target=ws_run_forever, args=(websocket_app, stop_event))
    ws_thread.daemon = True
    ws_thread.start()

    return websocket_app, stop_event  

def subscription(feed_type="tick", action="subscribe", batch_size=32):
    try:
        print('Subscribing Tokens')
        for i in range(0, len(inst_tokens), batch_size):
            token_batch = inst_tokens[i:i + batch_size]
            values = {}
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

            if isinstance(token_batch, list):
                values['k'] = '#'.join(token_batch)
            else:
                values['k'] = token_batch

            data = json.dumps(values)
            #print(data)
            if websocket_app and websocket_app.sock.connected:
                websocket_app.send(data)
            else:
                print("WebSocket is not connected.")
            
            time.sleep(0.1)
        print('Subscribed')              
    
    except Exception as e:
        print(f"Error during {action}: {e}")


# Variables initialization
last_ltp = {}  # Last LTP (float) per token
last_oi = {}  # Last OI per token
last_valid_ltp = {}  # Last LTP (float) with nonzero volume per token, used as BUYSELL baseline
close_price = {}  # Close price per token
last_volume = {}  # Last day volume per token
last_aux1 = {}  # Last aux1 value per token (TBQTSQ / BIDASK)
last_aux2 = {}  # Last aux2 value per token (TBQTSQ / BIDASK)
last_direction = {}  # Last up/down direction per token
last_processed_time = {}  # Last processed time per token
recent_messages = []  # List for recent messages

open_price = {}  # Open price per token
high_price = {}  # High price per token
low_price = {}  # Low price per token
cumulative_tick_volume = {}  # Cumulative tick volumes
cumulative_buy_volume = {} # Cumulative buy volumes
cumulative_sell_volume = {} # Cumulative sell volumes

# Set of index tokens (string type for consistency)
index_tokens = {'26000', '26009', '26017', '26037', '26074', '26013',
                '26008', '26018', '26020', '26021', '26023', '26029',
                '26030', '26031', '1'}

def on_message(websocket_app, message):
    global recent_messages

    # Extract message type and basic details
    message = json.loads(message)
    msg_type = message.get('t')
    exchange = message.get('e')
    token = message.get('tk')
    timestamp = message.get('ft')
    msg_status = message.get('s')
    
    if msg_type == 'ak' and msg_status == 'OK':
        print("WebSocket Connected")
        subscription(feed_type=subscribe_type, action="subscribe", batch_size=32)

    # Messages without feed time (e.g. connection acknowledgement) are not processed further
    if not timestamp:
        return

    # Convert timestamp to IST and split into date and time
    ist_time = epoch_to_ist(timestamp)
    date_str = ist_time.strftime('%d-%m-%Y')  
    time_str = ist_time.strftime('%H:%M:%S')  

    # Apply symbol mapping for token
    if token in symbol_mapping:
        mapped_symbol = symbol_mapping[token]
        
    #Get OI from acknowledgement message
    if msg_type in ['tk', 'dk']:
        #print(message)
        ts = message.get('ts')
        print(ts)        
        oi = message.get('oi') 
        if oi is not None:
            last_oi[token] = oi # Initialize and store the OI
            
    #Process feed message
    elif msg_type in ['tf', 'df']:        
        #print(message)
        #Get LTP, Day Volume and OI
        ltp = message.get('lp')#LTP  
        volume = message.get('v')  #Day Volume
        oi = message.get('oi') #Open Interest
       
        if oi is None or oi == 0:
            oi = last_oi.get(token, 0)
        else:
            last_oi[token] = oi 
       
        # Process tick volume
        tick_volume = 0  
        if volume is not None:
            try:
                current_volume = int(volume)  
                if token not in last_volume:
                    last_volume[token] = current_volume
                else:
                    previous_volume = last_volume[token]
                    tick_volume = current_volume - previous_volume
                    last_volume[token] = current_volume
            except ValueError:
                print(f"Warning: Unable to convert volume to integer for token {token}: {volume}")
                return

        # --- Handle LTP (convert to float, preserve last known) ---
        if ltp is None:
            ltp = last_ltp.get(token)
        else:
            try:
                ltp = float(ltp)
            except (ValueError, TypeError):
                return
            last_ltp[token] = ltp

        # No LTP available yet
        if ltp is None:
            return

        #print(f"I>, {time_str},{ltp},{last_ltp.get(token)},{tick_volume},{oi}")            

        # --- Tick with volume 0 just initializes price baseline ---
        if token not in index_tokens and tick_volume <= 0:
            if token not in last_valid_ltp:
                # First valid LTP seen - initialize baseline
                last_valid_ltp[token] = ltp
            return
        
        # --- Auxiliary fields ---

        # TBQTSQ
        elif aux_field == 'TBQTSQ':
            aux1 = message.get('tbq')
            aux2 = message.get('tsq')

            if aux1 is None:
                aux1 = last_aux1.get(token, 0)
            else:
                last_aux1[token] = aux1

            if aux2 is None:
                aux2 = last_aux2.get(token, 0)
            else:
                last_aux2[token] = aux2

        #BIDASK      
        elif aux_field == 'BIDASK':
            aux1 = message.get('bp1')
            aux2 = message.get('sp1')

            if aux1 is None:
                aux1 = last_aux1.get(token, 0)
            else:
                last_aux1[token] = aux1

            if aux2 is None:
                aux2 = last_aux2.get(token, 0)
            else:
                last_aux2[token] = aux2          

        # NONE
        else:  
            aux1 = ''
            aux2 = ''

        #print(f"P>,{time_str},{ltp},{last_ltp.get(token)},{tick_volume},{oi},{aux1},{aux2}")

        # Making Candlestick
        feed_time = ist_time.replace(microsecond=0)
        
        if token not in last_processed_time or last_processed_time[token].minute != feed_time.minute:
            cumulative_tick_volume[token] = 0
            cumulative_buy_volume[token] = 0
            cumulative_sell_volume[token] = 0
            
            open_price[token] = ltp  
            high_price[token] = ltp  
            low_price[token] = ltp  
            close_price[token] = ltp  
            last_processed_time[token] = feed_time  
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
        formatted_time = ist_time.strftime('%H:%M:00')
        #print("OUT>", mapped_symbol, date_str, formatted_time, open_price[token], high_price[token], low_price[token], close_price[token], cumulative_tick_volume[token], oi, aux1, aux2)            

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
            "aux1": aux1,
            "aux2": aux2,            
            "timestamp": current_time
        })

        # Keep only messages from the last few seconds
        recent_messages = [msg for msg in recent_messages if (current_time - msg['timestamp']).total_seconds() <= 0.5]

    else:
        print("Unknown message type", {message})


#Write to CSV and Import        
def write_to_csv():
    pythoncom.CoInitialize()  
    AB = win32com.client.Dispatch("Broker.Application")
    while True:
        if recent_messages:
            try:
                df = pd.DataFrame(recent_messages).drop(columns=['timestamp'])
                df.to_csv(rtd_file, mode='w', index=False)
                #time.sleep(0.2)
                #print(pc_time())
                #print("Importing to Broker.Application...")
                AB.Import(0, rtd_file, f"{format_file}.format")
            except Exception as e:
                time.sleep(0.1)
                #pc_current_time = datetime.now().strftime('%H:%M:%S')
                #print(f"[{pc_current_time}] Error while writing to CSV: {e}")
        else:
            time.sleep(0.2)



#Get Values for Variables    
login_dict = read_csv_dict(login_file)
user_id = login_dict['user']
jkey = login_dict['token']
act_id = user_id

# Load subscription and auxiliary-field settings
inputs_dict = read_csv_dict(inputs_file)
subscribe_type = inputs_dict['Subscription']
aux_field = inputs_dict['AuxField']
channel_id = inputs_dict['TelegramChannelID']
bot_key = inputs_dict['TelegramBotKey']

print(f"Subscription: {subscribe_type}, AuxField: {aux_field}")

# Symbol Master
symbol_master(master_file)

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


# Start write_to_csv 
csv_thread = threading.Thread(target=write_to_csv)
csv_thread.daemon = True  
csv_thread.start()
time.sleep(10)
input("Press Enter to exit...")    

