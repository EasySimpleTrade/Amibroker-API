'''
VALLAKKOTTAI MURUGAN THUNAI
Easy Simple Trading Solutions

Upstox Historical Data
'''

# =========================================================
# Libraries
# =========================================================

import pandas as pd
import asyncio
import aiohttp
import csv
import os
import sys
import ssl
import certifi
import calendar

from datetime import datetime, timedelta
from urllib.parse import quote

import win32com.client


# =========================================================
# Inputs
# =========================================================

login_file = r'R:\UpstoxLogin1.txt'

output_dir = r'C:\API\HistoricalData'

base_url = 'https://api.upstox.com/v3/historical-candle/intraday'

format_file = 'Candle'

# =========================================================
# Command Line Inputs
#
# Example:
#
# python "Upstox HistData.py" 18-08-2026 18-08-2026 Yes Yes MasterUpstox 1 25
#
# =========================================================

start_date = sys.argv[1]
end_date = sys.argv[2]
do_import = sys.argv[3]
do_delete = sys.argv[4]
master_file = sys.argv[5]
time_frame = sys.argv[6]
unit = sys.argv[7]
batch_size = int(sys.argv[8])

'''
start_date = '24-08-2026'
end_date = '24-08-2026'
do_import = 'no'
do_delete = 'no'
master_file = 'MasterUpstox' #IndexUpstox MasterUpstox CRUDEOILUpstox
time_frame = '1'
unit = 'minutes'
batch_size = 25
'''


print("start_date=" + start_date)
print("end_date=" + end_date)
print("do_import=" + do_import)
print("do_delete=" + do_delete)
print("master_file=" + master_file)
print("time_frame=" + time_frame)
print("unit=" + unit)
print("batch_size=" + str(batch_size))


master_list = fr'C:\API\Files\{master_file}.csv'

#input("Press enter to exit...")

# =========================================================
# Validate time frame
# =========================================================

try:

    interval = int(time_frame)

except ValueError:

    print("ERROR: time_frame must be a number.")
    sys.exit(1)


if interval < 1 or interval > 300:

    print("ERROR: Upstox minute interval must be between 1 and 300.")
    sys.exit(1)




# =========================================================
# Global API Rate Limiter
# Maximum: 500 requests per minute
# =========================================================

REQUESTS_PER_MINUTE = 500
REQUEST_INTERVAL = 60.0 / REQUESTS_PER_MINUTE

rate_limit_lock = asyncio.Lock()
next_request_time = 0.0


async def rate_limit():

    global next_request_time

    async with rate_limit_lock:

        current_time = asyncio.get_running_loop().time()

        wait_time = next_request_time - current_time

        if wait_time > 0:

            await asyncio.sleep(wait_time)

        # Reserve the next request slot
        next_request_time = (
            max(
                next_request_time,
                asyncio.get_running_loop().time()
            )
            + REQUEST_INTERVAL
        )
# =========================================================
# Login CSV
# =========================================================

def read_csv_dict(file_path):

    data_dict = {}

    with open(
        file_path,
        mode='r',
        newline='',
        encoding='utf-8'
    ) as file:

        reader = csv.reader(file)

        for row in reader:

            if len(row) >= 2:

                key = row[0].strip()
                value = row[1].strip()

                data_dict[key] = value

    return data_dict


# =========================================================
# PC Time
# =========================================================

def pc_time():

    return datetime.now().strftime(
        '%d-%m-%Y %H:%M:%S'
    )


# =========================================================
# Date conversion
#
# FlatTrade:
# DD-MM-YYYY
#
# Upstox:
# YYYY-MM-DD
# =========================================================

def upstox_date(date_string):

    return datetime.strptime(
        date_string,
        '%d-%m-%Y'
    ).strftime('%Y-%m-%d')


# =========================================================
# Generate date chunks
#
# Upstox V3:
#
# 1-15 minute intervals:
# maximum approximately 1 month
#
# >15 minute intervals:
# maximum approximately 1 quarter
#
# We use conservative chunks.
# =========================================================

def generate_date_chunks(start_date_string, end_date_string):

    start = datetime.strptime(
        start_date_string,
        '%d-%m-%Y'
    ).date()

    end = datetime.strptime(
        end_date_string,
        '%d-%m-%Y'
    ).date()


    if start > end:

        raise ValueError(
            "start_date cannot be greater than end_date"
        )


    # -----------------------------------------------------
    # 1 to 15 minutes
    # -----------------------------------------------------

    if interval <= 15:

        max_days = 28


    # -----------------------------------------------------
    # 16 to 300 minutes
    # Use approximately one quarter.
    # -----------------------------------------------------

    else:

        max_days = 85


    chunks = []

    current_start = start


    while current_start <= end:

        current_end = min(
            current_start + timedelta(days=max_days - 1),
            end
        )

        chunks.append(
            (
                current_start.strftime('%Y-%m-%d'),
                current_end.strftime('%Y-%m-%d')
            )
        )

        current_start = current_end + timedelta(days=1)


    return chunks


# =========================================================
# Format instrument key for URL
#
# NSE_FO|59150
#
# becomes
#
# NSE_FO%7C59150
# =========================================================

def encode_instrument_key(instrument_key):

    return quote(
        str(instrument_key),
        safe=''
    )


# =========================================================
# Fetch one date chunk for one symbol
# =========================================================

async def fetch_chunk(
        session,
        access_token,
        symbol,
        instrument_key,
        chunk_start,
        chunk_end,
        retries=2,
        delay=2):


    encoded_key = encode_instrument_key(
        instrument_key
    )


    url = (
        f'{base_url}/'
        f'{encoded_key}/'
        f'{unit}/'
        f'{interval}'
        #f'{chunk_end}/'
        #f'{chunk_start}'
    )


    headers = {

        'Content-Type': 'application/json',

        'Accept': 'application/json',

        'Authorization':
            f'Bearer {access_token}'
    }


    retryable_statuses = {
        #400,
        408,
        429,
        500,
        502,
        503,
        504,
        524
    }

    # =========================================================
    # Permanent Upstox error codes
    # Do NOT retry these
    # =========================================================

    non_retryable_error_codes = {
        'UDAPI1021',
        'UDAPI1022',
        'UDAPI100011',
        'UDAPI1015',
        'UDAPI1146',
        'UDAPI1147',
        'UDAPI1148'
    }


    for attempt in range(retries):

        try:

            await rate_limit()
            async with session.get(
                url,
                headers=headers,
                ssl=ssl_context
            ) as response:


                # =========================================
                # Successful response
                # =========================================

                if response.status == 200:

                    data = await response.json()

                    #print(f'\nURL: {url}')
                    #print(f'Response status: {response.status}')
                    #print(f'Response: {data}\n')

                    if (
                        not isinstance(data, dict)
                        or data.get('status') != 'success'
                    ):

                        print(
                            f'Error: Invalid response for {symbol}'
                        )

                        return []

                    candles = (
                        data
                        .get('data', {})
                        .get('candles', [])
                    )

                    print(
                        f'{symbol}: Received {len(candles)} candles'
                    )

                    return candles


                # =========================================
                # Error response
                # =========================================

                else:

                    error_text = await response.text()

                    error_code = None


                    # -----------------------------------------
                    # Extract Upstox error code
                    # -----------------------------------------

                    try:

                        error_data = json.loads(error_text)

                        errors = error_data.get(
                            'errors',
                            []
                        )

                        if errors:

                            error_code = (
                                errors[0].get('errorCode')
                                or
                                errors[0].get('error_code')
                            )

                    except Exception:

                        pass


                    # -----------------------------------------
                    # Permanent Upstox errors
                    # -----------------------------------------

                    if error_code in non_retryable_error_codes:

                        print(
                            f'Non-retryable error '
                            f'{error_code} for {symbol}'
                        )

                        print(
                            f'Response: {error_text[:500]}'
                        )

                        return []


                    # -----------------------------------------
                    # Retryable HTTP errors
                    # -----------------------------------------

                    elif response.status in retryable_statuses:

                        print(
                            f'Attempt {attempt + 1}: '
                            f'Retryable status '
                            f'{response.status} '
                            f'for {symbol} '
                            f'{chunk_start} to {chunk_end}'
                        )

                        print(
                            f'Response: {error_text[:500]}'
                        )


                    # -----------------------------------------
                    # Other errors
                    # -----------------------------------------

                    else:

                        print(
                            f'ERROR: {symbol} '
                            f'{instrument_key} '
                            f'status={response.status}'
                        )

                        print(
                            f'Response: {error_text[:500]}'
                        )

                        return []


        except aiohttp.ClientError as e:

            print(
                f'Attempt {attempt + 1}: '
                f'Client error for {symbol}: {e}'
            )


        except Exception as e:

            print(
                f'Attempt {attempt + 1}: '
                f'Exception for {symbol}: {e}'
            )


        # =============================================
        # Retry delay
        # =============================================

        if attempt < retries - 1:

            await asyncio.sleep(delay)


    print(
        f'Max retries reached for '
        f'{symbol} '
        f'{chunk_start} to {chunk_end}'
    )

    return []


# =========================================================
# Process one symbol
# =========================================================

async def hist_data_single(
        session,
        access_token,
        symbol,
        instrument_key,
        start_date,
        end_date,
        output_dir,
        do_import='yes',
        do_delete='yes'):


    '''print(
        f'\nDownloading: {symbol} '
        f'[{instrument_key}]'
    )'''


    # -----------------------------------------------------
    # Generate date chunks
    # -----------------------------------------------------

    chunks = generate_date_chunks(
        start_date,
        end_date
    )


    '''print(
        f'{symbol}: '
        f'{len(chunks)} date chunk(s)'
    )'''


    all_candles = []


    # -----------------------------------------------------
    # Download every date chunk
    # -----------------------------------------------------

    for chunk_number, (
        chunk_start,
        chunk_end
    ) in enumerate(chunks, start=1):


        '''print(
            f'{symbol}: '
            f'Chunk {chunk_number}/{len(chunks)} '
            f'{chunk_start} -> {chunk_end}'
        )'''


        candles = await fetch_chunk(
            session,
            access_token,
            symbol,
            instrument_key,
            chunk_start,
            chunk_end
        )


        if candles:

            all_candles.extend(candles)


    # -----------------------------------------------------
    # No data
    # -----------------------------------------------------

    if not all_candles:

        print(
            f'{symbol}: No historical data found.'
        )

        return


    # -----------------------------------------------------
    # Parse candles
    #
    # Upstox:
    #
    # [0] timestamp
    # [1] open
    # [2] high
    # [3] low
    # [4] close
    # [5] volume
    # [6] OI
    # -----------------------------------------------------

    rows = []


    for candle in all_candles:

        try:

            if len(candle) < 7:

                continue


            timestamp = candle[0]

            open_price = candle[1]

            high_price = candle[2]

            low_price = candle[3]

            close_price = candle[4]

            volume = candle[5]

            oi = candle[6]


            # ---------------------------------------------
            # Convert timestamp
            # ---------------------------------------------

            dt = datetime.fromisoformat(
                timestamp
            )


            date = dt.strftime(
                '%d-%m-%Y'
            )

            time = dt.strftime(
                '%H:%M:%S'
            )


            # ---------------------------------------------
            # Volume correction
            # Same protection as FlatTrade version
            # ---------------------------------------------

            volume = max(
                0,
                float(volume)
            )


            rows.append([

                symbol,

                date,

                time,

                open_price,

                high_price,

                low_price,

                close_price,

                volume,

                oi

            ])


        except Exception as e:

            print(
                f'Error processing candle '
                f'for {symbol}: {e}'
            )


    # -----------------------------------------------------
    # Create DataFrame
    # -----------------------------------------------------

    if not rows:

        print(
            f'{symbol}: No valid candle records.'
        )

        return


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


    # -----------------------------------------------------
    # Remove duplicate candles
    #
    # This is important because date chunks can overlap
    # depending on API boundaries.
    # -----------------------------------------------------

    df.drop_duplicates(
        subset=[
            'Symbol',
            'Date',
            'Time'
        ],
        inplace=True
    )


    # -----------------------------------------------------
    # Sort newest first
    #
    # This matches the Upstox response order and your
    # expected sample.
    # -----------------------------------------------------

    df['_datetime'] = pd.to_datetime(
        df['Date'] + ' ' + df['Time'],
        format='%d-%m-%Y %H:%M:%S'
    )


    df.sort_values(
        '_datetime',
        ascending=False,
        inplace=True
    )


    df.drop(
        columns=['_datetime'],
        inplace=True
    )


    # -----------------------------------------------------
    # Create output directory
    # -----------------------------------------------------

    os.makedirs(
        output_dir,
        exist_ok=True
    )


    # -----------------------------------------------------
    # Output file
    # -----------------------------------------------------

    output_file = os.path.join(
        output_dir,
        f'{symbol}.csv'
    )


    # -----------------------------------------------------
    # Save CSV
    # -----------------------------------------------------

    df.to_csv(
        output_file,
        index=False,
        float_format='%.2f'
    )


    '''print(
        f'{symbol}: '
        f'{len(df):,} candles saved'
    )


    print(
        f'File: {output_file}'
    )'''


    # -----------------------------------------------------
    # AmiBroker Import + Delete
    # -----------------------------------------------------

    if do_import == 'yes':
        try:
            #print(f'{symbol}: Importing to AmiBroker...')
            AB = win32com.client.Dispatch( "Broker.Application")
            AB.Import(0,output_file,format_file + ".format")
            #print( f'{symbol}: AmiBroker import completed.')
            # ---------------------------------------------
            # Delete ONLY after successful import
            # ---------------------------------------------
            if do_delete == 'yes':
                try:
                    os.remove(output_file)
                    #print( f'{symbol}: CSV deleted.')
                except Exception as e:
                    print(f'Warning: Could not delete ' f'{output_file}: {e}')
        except Exception as e:
            print( f'Error during AmiBroker import 'f'for {symbol}: {e}')


# =========================================================
# Process master list
# =========================================================

async def hist_data_list(
        session,
        access_token,
        master_list,
        start_date,
        end_date,
        output_dir,
        do_import='yes',
        do_delete='yes'):


    # -----------------------------------------------------
    # Read Upstox Master
    #
    # Columns:
    #
    # Symbol,Instrument_Key
    # -----------------------------------------------------

    df_master = pd.read_csv(
        master_list,
        dtype=str
    )


    # -----------------------------------------------------
    # Remove whitespace
    # -----------------------------------------------------

    df_master.columns = (
        df_master.columns
        .str.strip()
    )


    df_master['Symbol'] = (
        df_master['Symbol']
        .astype(str)
        .str.strip()
    )


    df_master['Instrument_Key'] = (
        df_master['Instrument_Key']
        .astype(str)
        .str.strip()
    )


    # -----------------------------------------------------
    # Remove blank rows
    # -----------------------------------------------------

    df_master = df_master[
        (
            df_master['Symbol'].notna()
        )
        &
        (
            df_master['Instrument_Key'].notna()
        )
        &
        (
            df_master['Symbol'] != ''
        )
        &
        (
            df_master['Instrument_Key'] != ''
        )
    ]


    print(
        f'\nMaster records: '
        f'{len(df_master):,}'
    )


    # -----------------------------------------------------
    # Batch processing
    # Same concept as FlatTrade
    # -----------------------------------------------------

    for i in range(
        0,
        len(df_master),
        batch_size
    ):


        batch = df_master.iloc[
            i:i + batch_size
        ]


        batch_number = (
            i // batch_size
        ) + 1


        print(
            '\n============================================================'
        )

        print(
            f'Processing batch {batch_number}: '
            f'symbols {i + 1} to '
            f'{i + len(batch)}'
        )

        print(
            '============================================================'
        )


        tasks = []


        for _, row in batch.iterrows():


            task = hist_data_single(

                session,

                access_token,

                row['Symbol'],

                row['Instrument_Key'],

                start_date,

                end_date,

                output_dir,

                do_import=do_import,

                do_delete=do_delete

            )


            tasks.append(task)


        try:

            await asyncio.gather(
                *tasks
            )


        except Exception as e:

            print(
                f'Error during batch '
                f'{batch_number}: {e}'
            )


# =========================================================
# Main
# =========================================================

# ---------------------------------------------------------
# SSL context
# ---------------------------------------------------------

ssl_context = ssl.create_default_context(
    cafile=certifi.where()
)


# ---------------------------------------------------------
# Read login
# ---------------------------------------------------------

login_dict = read_csv_dict(
    login_file
)


if 'token' not in login_dict:

    print(
        f'ERROR: token not found in '
        f'{login_file}'
    )

    sys.exit(1)


access_token = ''#login_dict['token']


print(
    f'Access token loaded.'
)


# ---------------------------------------------------------
# Create output directory
# ---------------------------------------------------------

os.makedirs(
    output_dir,
    exist_ok=True
)


# ---------------------------------------------------------
# Display settings
# ---------------------------------------------------------

print(
    '\n============================================================'
)

print(
    'UPSTOX HISTORICAL DATA'
)

print(
    '============================================================'
)

print(
    f'Start Date : {start_date}'
)

print(
    f'End Date   : {end_date}'
)

print(
    f'Interval   : {interval} minute(s)'
)

print(
    f'Master     : {master_list}'
)

print(
    f'Output     : {output_dir}'
)

print(
    f'Import     : {do_import}'
)

print(
    f'Delete     : {do_delete}'
)

print(
    f'Batch Size : {batch_size}'
)

print(
    '============================================================'
)


# ---------------------------------------------------------
# Start
# ---------------------------------------------------------

print(
    f'Start Time: {pc_time()}'
)


async def main():

    timeout = aiohttp.ClientTimeout(
        total=120
    )


    connector = aiohttp.TCPConnector(
        limit=batch_size,
        ssl=ssl_context
    )


    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector
    ) as session:


        await hist_data_list(

            session,

            access_token,

            master_list,

            start_date,

            end_date,

            output_dir,

            do_import=do_import,

            do_delete=do_delete

        )


# ---------------------------------------------------------
# Execute
# ---------------------------------------------------------

try:

    asyncio.run(
        main()
    )


except KeyboardInterrupt:

    print(
        '\nProcess interrupted by user.'
    )


except Exception as e:

    print(
        f'\nFatal error: {e}'
    )


print(
    f'End Time: {pc_time()}'
)


input(
    'Press Enter to exit...'
)

