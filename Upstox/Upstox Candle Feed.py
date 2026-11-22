# Libraries
import json
import threading
import time
import csv
import requests
import websocket
import pandas as pd
from datetime import datetime, timedelta, timezone
from google.protobuf.json_format import MessageToDict
import win32com.client
import pythoncom

# ==================================================================== #
# BEGIN GENERATED PROTOBUF CODE (from MarketDataFeed_pb2.py)
# See "PROTOBUF CODE IS EMBEDDED BELOW" note above for how to refresh this.
# ==================================================================== #
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    7,
    35,
    1,
    '',
    'MarketDataFeed.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x14MarketDataFeed.proto\x12,com.upstox.marketdatafeederv3udapi.rpc.proto\"9\n\x04LTPC\x12\x0b\n\x03ltp\x18\x01 \x01(\x01\x12\x0b\n\x03ltt\x18\x02 \x01(\x03\x12\x0b\n\x03ltq\x18\x03 \x01(\x03\x12\n\n\x02\x63p\x18\x04 \x01(\x01\"W\n\x0bMarketLevel\x12H\n\x0b\x62idAskQuote\x18\x01 \x03(\x0b\x32\x33.com.upstox.marketdatafeederv3udapi.rpc.proto.Quote\"N\n\nMarketOHLC\x12@\n\x04ohlc\x18\x01 \x03(\x0b\x32\x32.com.upstox.marketdatafeederv3udapi.rpc.proto.OHLC\"?\n\x05Quote\x12\x0c\n\x04\x62idQ\x18\x01 \x01(\x03\x12\x0c\n\x04\x62idP\x18\x02 \x01(\x01\x12\x0c\n\x04\x61skQ\x18\x03 \x01(\x03\x12\x0c\n\x04\x61skP\x18\x04 \x01(\x01\"V\n\x0cOptionGreeks\x12\r\n\x05\x64\x65lta\x18\x01 \x01(\x01\x12\r\n\x05theta\x18\x02 \x01(\x01\x12\r\n\x05gamma\x18\x03 \x01(\x01\x12\x0c\n\x04vega\x18\x04 \x01(\x01\x12\x0b\n\x03rho\x18\x05 \x01(\x01\"i\n\x04OHLC\x12\x10\n\x08interval\x18\x01 \x01(\t\x12\x0c\n\x04open\x18\x02 \x01(\x01\x12\x0c\n\x04high\x18\x03 \x01(\x01\x12\x0b\n\x03low\x18\x04 \x01(\x01\x12\r\n\x05\x63lose\x18\x05 \x01(\x01\x12\x0b\n\x03vol\x18\x06 \x01(\x03\x12\n\n\x02ts\x18\x07 \x01(\x03\"\x8e\x03\n\x0eMarketFullFeed\x12@\n\x04ltpc\x18\x01 \x01(\x0b\x32\x32.com.upstox.marketdatafeederv3udapi.rpc.proto.LTPC\x12N\n\x0bmarketLevel\x18\x02 \x01(\x0b\x32\x39.com.upstox.marketdatafeederv3udapi.rpc.proto.MarketLevel\x12P\n\x0coptionGreeks\x18\x03 \x01(\x0b\x32:.com.upstox.marketdatafeederv3udapi.rpc.proto.OptionGreeks\x12L\n\nmarketOHLC\x18\x04 \x01(\x0b\x32\x38.com.upstox.marketdatafeederv3udapi.rpc.proto.MarketOHLC\x12\x0b\n\x03\x61tp\x18\x05 \x01(\x01\x12\x0b\n\x03vtt\x18\x06 \x01(\x03\x12\n\n\x02oi\x18\x07 \x01(\x01\x12\n\n\x02iv\x18\x08 \x01(\x01\x12\x0b\n\x03tbq\x18\t \x01(\x01\x12\x0b\n\x03tsq\x18\n \x01(\x01\"\x9f\x01\n\rIndexFullFeed\x12@\n\x04ltpc\x18\x01 \x01(\x0b\x32\x32.com.upstox.marketdatafeederv3udapi.rpc.proto.LTPC\x12L\n\nmarketOHLC\x18\x02 \x01(\x0b\x32\x38.com.upstox.marketdatafeederv3udapi.rpc.proto.MarketOHLC\"\xbd\x01\n\x08\x46ullFeed\x12P\n\x08marketFF\x18\x01 \x01(\x0b\x32<.com.upstox.marketdatafeederv3udapi.rpc.proto.MarketFullFeedH\x00\x12N\n\x07indexFF\x18\x02 \x01(\x0b\x32;.com.upstox.marketdatafeederv3udapi.rpc.proto.IndexFullFeedH\x00\x42\x0f\n\rFullFeedUnion\"\x98\x02\n\x14\x46irstLevelWithGreeks\x12@\n\x04ltpc\x18\x01 \x01(\x0b\x32\x32.com.upstox.marketdatafeederv3udapi.rpc.proto.LTPC\x12G\n\nfirstDepth\x18\x02 \x01(\x0b\x32\x33.com.upstox.marketdatafeederv3udapi.rpc.proto.Quote\x12P\n\x0coptionGreeks\x18\x03 \x01(\x0b\x32:.com.upstox.marketdatafeederv3udapi.rpc.proto.OptionGreeks\x12\x0b\n\x03vtt\x18\x04 \x01(\x03\x12\n\n\x02oi\x18\x05 \x01(\x01\x12\n\n\x02iv\x18\x06 \x01(\x01\"\xd7\x02\n\x04\x46\x65\x65\x64\x12\x42\n\x04ltpc\x18\x01 \x01(\x0b\x32\x32.com.upstox.marketdatafeederv3udapi.rpc.proto.LTPCH\x00\x12J\n\x08\x66ullFeed\x18\x02 \x01(\x0b\x32\x36.com.upstox.marketdatafeederv3udapi.rpc.proto.FullFeedH\x00\x12\x62\n\x14\x66irstLevelWithGreeks\x18\x03 \x01(\x0b\x32\x42.com.upstox.marketdatafeederv3udapi.rpc.proto.FirstLevelWithGreeksH\x00\x12N\n\x0brequestMode\x18\x04 \x01(\x0e\x32\x39.com.upstox.marketdatafeederv3udapi.rpc.proto.RequestModeB\x0b\n\tFeedUnion\"\xe2\x01\n\nMarketInfo\x12\x62\n\rsegmentStatus\x18\x01 \x03(\x0b\x32K.com.upstox.marketdatafeederv3udapi.rpc.proto.MarketInfo.SegmentStatusEntry\x1ap\n\x12SegmentStatusEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12I\n\x05value\x18\x02 \x01(\x0e\x32:.com.upstox.marketdatafeederv3udapi.rpc.proto.MarketStatus:\x02\x38\x01\"\xe9\x02\n\x0c\x46\x65\x65\x64Response\x12@\n\x04type\x18\x01 \x01(\x0e\x32\x32.com.upstox.marketdatafeederv3udapi.rpc.proto.Type\x12T\n\x05\x66\x65\x65\x64s\x18\x02 \x03(\x0b\x32\x45.com.upstox.marketdatafeederv3udapi.rpc.proto.FeedResponse.FeedsEntry\x12\x11\n\tcurrentTs\x18\x03 \x01(\x03\x12L\n\nmarketInfo\x18\x04 \x01(\x0b\x32\x38.com.upstox.marketdatafeederv3udapi.rpc.proto.MarketInfo\x1a`\n\nFeedsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x41\n\x05value\x18\x02 \x01(\x0b\x32\x32.com.upstox.marketdatafeederv3udapi.rpc.proto.Feed:\x02\x38\x01*8\n\x04Type\x12\x10\n\x0cinitial_feed\x10\x00\x12\r\n\tlive_feed\x10\x01\x12\x0f\n\x0bmarket_info\x10\x02*E\n\x0bRequestMode\x12\x08\n\x04ltpc\x10\x00\x12\x0b\n\x07\x66ull_d5\x10\x01\x12\x11\n\roption_greeks\x10\x02\x12\x0c\n\x08\x66ull_d30\x10\x03*{\n\x0cMarketStatus\x12\x12\n\x0ePRE_OPEN_START\x10\x00\x12\x10\n\x0cPRE_OPEN_END\x10\x01\x12\x0f\n\x0bNORMAL_OPEN\x10\x02\x12\x10\n\x0cNORMAL_CLOSE\x10\x03\x12\x11\n\rCLOSING_START\x10\x04\x12\x0f\n\x0b\x43LOSING_END\x10\x05\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'MarketDataFeed_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_MARKETINFO_SEGMENTSTATUSENTRY']._loaded_options = None
  _globals['_MARKETINFO_SEGMENTSTATUSENTRY']._serialized_options = b'8\001'
  _globals['_FEEDRESPONSE_FEEDSENTRY']._loaded_options = None
  _globals['_FEEDRESPONSE_FEEDSENTRY']._serialized_options = b'8\001'
  _globals['_TYPE']._serialized_start=2535
  _globals['_TYPE']._serialized_end=2591
  _globals['_REQUESTMODE']._serialized_start=2593
  _globals['_REQUESTMODE']._serialized_end=2662
  _globals['_MARKETSTATUS']._serialized_start=2664
  _globals['_MARKETSTATUS']._serialized_end=2787
  _globals['_LTPC']._serialized_start=70
  _globals['_LTPC']._serialized_end=127
  _globals['_MARKETLEVEL']._serialized_start=129
  _globals['_MARKETLEVEL']._serialized_end=216
  _globals['_MARKETOHLC']._serialized_start=218
  _globals['_MARKETOHLC']._serialized_end=296
  _globals['_QUOTE']._serialized_start=298
  _globals['_QUOTE']._serialized_end=361
  _globals['_OPTIONGREEKS']._serialized_start=363
  _globals['_OPTIONGREEKS']._serialized_end=449
  _globals['_OHLC']._serialized_start=451
  _globals['_OHLC']._serialized_end=556
  _globals['_MARKETFULLFEED']._serialized_start=559
  _globals['_MARKETFULLFEED']._serialized_end=957
  _globals['_INDEXFULLFEED']._serialized_start=960
  _globals['_INDEXFULLFEED']._serialized_end=1119
  _globals['_FULLFEED']._serialized_start=1122
  _globals['_FULLFEED']._serialized_end=1311
  _globals['_FIRSTLEVELWITHGREEKS']._serialized_start=1314
  _globals['_FIRSTLEVELWITHGREEKS']._serialized_end=1594
  _globals['_FEED']._serialized_start=1597
  _globals['_FEED']._serialized_end=1940
  _globals['_MARKETINFO']._serialized_start=1943
  _globals['_MARKETINFO']._serialized_end=2169
  _globals['_MARKETINFO_SEGMENTSTATUSENTRY']._serialized_start=2057
  _globals['_MARKETINFO_SEGMENTSTATUSENTRY']._serialized_end=2169
  _globals['_FEEDRESPONSE']._serialized_start=2172
  _globals['_FEEDRESPONSE']._serialized_end=2533
  _globals['_FEEDRESPONSE_FEEDSENTRY']._serialized_start=2437
  _globals['_FEEDRESPONSE_FEEDSENTRY']._serialized_end=2533
# @@protoc_insertion_point(module_scope)
# ==================================================================== #
# END GENERATED PROTOBUF CODE
# ==================================================================== #

# ------------------------------------------------------------------ #
# Input
# ------------------------------------------------------------------ #
login_file = r'R:\UpstoxLogin1.txt'              # 2-column CSV: token,<ACCESS_TOKEN>
inputs_file = r'C:\API\Files\UpstoxInputs 1.csv'
master_file = r'C:\API\Files\MasterUpstox.csv'   # columns: Symbol,Instrument_Key  (Instrument_Key = full instrument_key)
rtd_file = r'R:\Upstox Candle Feed.csv'
format_file = 'Candle'

authorize_url = 'https://api.upstox.com/v3/feed/market-data-feed/authorize'
#subscribe_mode = 'full'                          # ltpc | option_greeks | full | full_d30
#aux_field = 'BUYSELL'                             # 'TBQTSQ' | 'BIDASK' | 'BUYSELL' | anything else = NONE
reconnect_delay = 2                              # seconds to wait before re-authorizing after a drop

recent_window = 0.3   # seconds a candle stays in recent_messages (same value as the previous Upstox code)
idle_sleep = 0.1     # writer thread: wait between checks when there is no new data
import_pause = 0.05    # writer thread: pause after every import (previous Upstox value, set 0 for none)

# Fallback list/mapping, used only if master_file can't be loaded.
# Once symbol_master() runs successfully these two globals get overwritten
# with everything from MasterUpstox.csv.
instrument_keys = ['NSE_INDEX|Nifty 50', 'NSE_INDEX|Nifty Bank']
symbol_mapping = {'NSE_INDEX|Nifty 50': 'NIFTY','NSE_INDEX|Nifty Bank': 'BANKNIFTY'}
IST = timezone(timedelta(hours=5, minutes=30))


# ------------------------------------------------------------------ #
# Helpers
# ------------------------------------------------------------------ #
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


#Convert epoch milliseconds (ltt) to IST Function
def epoch_ms_to_ist(epoch_ms):
    return datetime.fromtimestamp(int(epoch_ms) / 1000, tz=IST)


# Symbol Master Function
def symbol_master(file_path):
    """Load MasterUpstox.csv (columns: Symbol,Instrument_Key) into the global
    symbol_mapping (key -> Symbol) and instrument_keys (list of keys) --
    same role as the Flattrade symbol_master() function, adapted for the
    fact that Upstox's instrument_key is already the full subscribe value
    (no Exchange+Token join needed)."""
    global symbol_mapping, instrument_keys
    try:
        df = pd.read_csv(file_path)
        df['Symbol'] = df['Symbol'].astype(str).str.strip()
        df['Instrument_Key'] = df['Instrument_Key'].astype(str).str.strip()
        symbol_mapping = dict(zip(df['Instrument_Key'], df['Symbol']))
        instrument_keys = df['Instrument_Key'].tolist()
        print(f"Loaded symbol mapping and instrument keys from {file_path}")
    except Exception as e:
        print(f"Error loading data from {file_path}: {e} -- using fallback instrument_keys/symbol_mapping")
    set_index_tokens()


def set_index_tokens():
    """index_tokens = instruments that skip the 'volume must change' rule in the
    COMMON LOGIC. Indices never carry volume. In 'ltpc' mode Upstox sends no
    volume for any instrument, so every instrument skips the rule."""
    global index_tokens
    if subscribe_mode == 'ltpc':
        index_tokens = set(instrument_keys)
    else:
        index_tokens = {key for key in instrument_keys if '_INDEX|' in key}


def get_authorized_uri(access_token):
    """Call the V3 authorize REST endpoint to get a fresh, short-lived wss:// URL."""
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    resp = requests.get(authorize_url, headers=headers, timeout=10)  # timeout: never hang forever on a bad network
    resp.raise_for_status()
    payload = resp.json()
    return payload['data']['authorized_redirect_uri']


def decode_protobuf(buffer):
    """Decode a binary protobuf message into a FeedResponse object."""
    feed_response = FeedResponse()
    feed_response.ParseFromString(buffer)
    return feed_response


# ------------------------------------------------------------------ #
# WebSocket callbacks
# ------------------------------------------------------------------ #
# WebSocket open callback: subscribe the instruments
def on_open(ws):
    print(f"WebSocket Opened at {pc_time()}")
    subscription(ws, instrument_keys, subscribe_mode)


# WebSocket error callback
def on_error(ws, error):
    print(f"WebSocket error: {error}")
    if channel_id != "":
        send_telegram(channel_id,bot_key,f"{error}")

# WebSocket close callback
def on_close(ws, close_status_code, close_msg):
    print(f"WebSocket closed at {pc_time()}: {close_status_code}, {close_msg}")
    if channel_id != "":
        send_telegram(channel_id,bot_key,telegram_message)

# ------------------------------------------------------------------ #
# Reconnect-aware run loop
# ------------------------------------------------------------------ #
current_ws_app = None  # kept so close_websocket() can reach whichever socket is currently live


# Close WebSocket function
def close_websocket(stop_event):
    stop_event.set()
    if current_ws_app is not None:
        current_ws_app.close()
    print("WebSocket connection closed.")


# Keep the WebSocket connection alive and reconnect on failure
def ws_run_forever(access_token, stop_event):
    """Keeps the feed alive. On every (re)connect attempt -- including after
    a drop -- it fetches a brand-new authorized_redirect_uri first, since the
    old one is single-use/short-lived and cannot be reused."""
    global current_ws_app

    while not stop_event.is_set():
        try:
            wss_url = get_authorized_uri(access_token)
            print(f"[{pc_time()}] Authorized redirect URI: {wss_url}")

            ws_app = websocket.WebSocketApp(
                wss_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            current_ws_app = ws_app

            # run_forever() blocks here until the socket drops/closes
            ws_app.run_forever(ping_interval=20)

        except Exception as e:
            print(f"[{pc_time()}] Connection attempt failed: {e}")

        if not stop_event.is_set():
            print(f"[{pc_time()}] Reconnecting in {reconnect_delay}s with a fresh authorized URI...")
            time.sleep(reconnect_delay)


# Function to start the WebSocket connection
def start_websocket(access_token):
    stop_event = threading.Event()

    # Start the WebSocket in a separate thread
    ws_thread = threading.Thread(target=ws_run_forever, args=(access_token, stop_event))
    ws_thread.daemon = True
    ws_thread.start()

    return stop_event


def subscription(ws, keys, mode="full", method="sub"):
    """Send a subscribe/unsubscribe/change-mode request. Must go out as a
    BINARY frame (per Upstox V3 docs), even though the payload itself is JSON."""
    request = {
        "guid": "someguid",
        "method": method,          # sub | unsub | change_mode
        "data": {
            "mode": mode,
            "instrumentKeys": keys
        }
    }
    binary_data = json.dumps(request).encode('utf-8')
    if ws.sock and ws.sock.connected:
        ws.send(binary_data, opcode=websocket.ABNF.OPCODE_BINARY)
        print(f"Sent {method} request for {len(keys)} instrument(s) in '{mode}' mode")
    else:
        print("WebSocket is not connected.")


# Variables initialization  (same names as the Flattrade file)
last_ltp = {}  # Last LTP (float) per token
last_oi = {}  # Last OI per token
last_valid_ltp = {}  # Last LTP (float) with nonzero volume per token, used as BUYSELL baseline
close_price = {}  # Close price per token
last_volume = {}  # Last day volume (VTT) per token
last_aux1 = {}  # Last aux1 value per token (TBQTSQ / BIDASK)
last_aux2 = {}  # Last aux2 value per token (TBQTSQ / BIDASK)
last_direction = {}  # Last up/down direction per token
last_processed_time = {}  # Start of the minute (date + HH:MM:00) of the candle being built, per token
recent_messages = []  # List for recent messages
new_data = threading.Event()  # set by process_feed() when a candle changed, cleared by the writer thread

open_price = {}  # Open price per token
high_price = {}  # High price per token
low_price = {}  # Low price per token
cumulative_tick_volume = {}  # Cumulative tick volumes
cumulative_buy_volume = {} # Cumulative buy volumes
cumulative_sell_volume = {} # Cumulative sell volumes

# Tokens that skip the "volume must change" rule (indices; every instrument in ltpc mode)
# Filled by set_index_tokens() when symbol_master() runs
index_tokens = set()


def extract_feed_fields(feed):
    """Pull ltpc + OI/TBQ/TSQ/best-bid-ask + VTT from a feed.

    Returns:
        (ltpc, oi, tbq, tsq, bidP, askP, vtt)

    vtt is Upstox's cumulative Volume Traded Today.
    """
    full_feed = feed.get('fullFeed')
    if full_feed:
        market_ff = full_feed.get('marketFF')
        if market_ff:
            bidP = askP = None
            quotes = (market_ff.get('marketLevel') or {}).get('bidAskQuote')
            if quotes:
                bidP = quotes[0].get('bidP')
                askP = quotes[0].get('askP')

            return (
                market_ff.get('ltpc'),
                market_ff.get('oi'),
                market_ff.get('tbq'),
                market_ff.get('tsq'),
                bidP,
                askP,
                market_ff.get('vtt')
            )

        index_ff = full_feed.get('indexFF')
        if index_ff:
            return index_ff.get('ltpc'), None, None, None, None, None, None

        return None, None, None, None, None, None, None

    # ltpc mode: flat, no VTT available
    return feed.get('ltpc'), None, None, None, None, None, None


def on_message(ws, message):
    """Upstox V3 pushes binary protobuf frames. One frame can carry many
    instruments, so decode it and hand each instrument to process_feed()."""
    try:
        decoded = decode_protobuf(message)
        data_dict = MessageToDict(decoded)
    except Exception as e:
        print(f"Could not decode message: {e}")
        return

    feeds = data_dict.get('feeds')
    if not feeds:
        # e.g. the initial "market_info" segment-status message -- nothing to process
        return

    for instrument_key, feed in feeds.items():
        try:
            process_feed(instrument_key, feed)
        except Exception as e:
            # one bad instrument must not drop the other instruments in the same frame
            print(f"[{pc_time()}] Error processing {instrument_key}: {e}")


# ==================================================================== #
# process_feed() = the Upstox version of on_message() in the Flattrade file.
# Same two halves:
#   1. BROKER SPECIFIC: PARSING - understands the Upstox message and fills the common fields:
#         token, mapped_symbol, ist_time, date_str, ltp, tick_volume, oi,
#         message (a dict with tbq, tsq, bp1, sp1)
#   2. COMMON LOGIC - the same in every broker file: volume rule, aux fields,
#         candle building, recent_messages.
# ==================================================================== #
def process_feed(token, feed):
    global recent_messages

    # ================================================================ #
    # 1. BROKER SPECIFIC: PARSING (Upstox)
    # ================================================================ #
    ltpc, oi, tbq, tsq, bidP, askP, vtt = extract_feed_fields(feed)
    if not ltpc:
        return

    ltp = ltpc.get('ltp')  #LTP
    ltt = ltpc.get('ltt')  #Last trade time (epoch milliseconds)
    if ltp is None or ltt is None:
        return

    # Convert time to IST and split into date and time
    ist_time = epoch_ms_to_ist(ltt)
    date_str = ist_time.strftime('%d-%m-%Y')
    time_str = ist_time.strftime('%H:%M:%S')

    # Apply symbol mapping for token
    mapped_symbol = symbol_mapping.get(token, token)

    # Aux inputs, named like the Flattrade message fields so the COMMON LOGIC is identical
    message = {'tbq': tbq, 'tsq': tsq, 'bp1': bidP, 'sp1': askP}

    # OI (keep the last value when this update has none)
    if oi is None or oi == 0:
        oi = last_oi.get(token, 0)
    else:
        last_oi[token] = oi

    # Process tick volume: VTT (Volume Traded Today) is the day volume,
    # so tick volume = current VTT - previous VTT. ltq is intentionally not used.
    volume = vtt  #Day Volume
    tick_volume = 0
    if volume is not None:
        try:
            current_volume = int(volume)
        except (ValueError, TypeError):
            print(f"Warning: Unable to convert vtt to integer for token {token}: {volume}")
            return
        if token not in last_volume:
            last_volume[token] = current_volume
        else:
            previous_volume = last_volume[token]
            tick_volume = current_volume - previous_volume
            last_volume[token] = current_volume

    # --- Handle LTP (convert to float) ---
    try:
        ltp = float(ltp)
    except (ValueError, TypeError):
        print(f"Warning: Unable to convert ltp to float for token {token}: {ltp}")
        return
    last_ltp[token] = ltp

    # ================================================================ #
    # 2. COMMON LOGIC (same in every broker file)
    # ================================================================ #

    #print(f"I>, {time_str},{ltp},{last_ltp.get(token)},{tick_volume},{oi}")

    # --- Tick with volume 0 just initializes price baseline ---
    if token not in index_tokens and tick_volume <= 0:
        if token not in last_valid_ltp:
            # First valid LTP seen - initialize baseline
            last_valid_ltp[token] = ltp
        return

    # --- Auxiliary fields ---
    # BUYSELL classification is based on tick-volume change and LTP movement.
    buy_volume = sell_volume = 0

    if aux_field == 'BUYSELL':
        aux1 = buy_volume
        aux2 = sell_volume

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
    # Full minute start (date + hour + minute), so the same minute on another hour/day is never mistaken
    minute_start = ist_time.replace(second=0, microsecond=0)

    if last_processed_time.get(token) != minute_start:
        # New minute: start a fresh candle
        cumulative_tick_volume[token] = 0
        cumulative_buy_volume[token] = 0
        cumulative_sell_volume[token] = 0

        open_price[token] = ltp
        high_price[token] = ltp
        low_price[token] = ltp
        close_price[token] = ltp
        last_processed_time[token] = minute_start
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
    recent_messages = [msg for msg in recent_messages if (current_time - msg['timestamp']).total_seconds() <= recent_window]


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




# ------------------------------------------------------------------ #
# Execute
# ------------------------------------------------------------------ #

#Get Values for Variables
login_dict = read_csv_dict(login_file)
access_token = login_dict['token']

# Load subscription and auxiliary-field settings
inputs_dict = read_csv_dict(inputs_file)
subscribe_mode = inputs_dict['Subscription']                        
aux_field = inputs_dict['AuxField']  

# Symbol Master
symbol_master(master_file)   # loads instrument_keys + symbol_mapping from MasterUpstox.csv
#print(f"Subscribing to {len(instrument_keys)} instrument(s): {instrument_keys}")

#Start Web Socket
stop_event = start_websocket(access_token)

# Start write_to_csv 
csv_thread = threading.Thread(target=write_to_csv)
csv_thread.daemon = True  
csv_thread.start()
time.sleep(10)
input("Press Enter to exit...")   

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    close_websocket(stop_event)
