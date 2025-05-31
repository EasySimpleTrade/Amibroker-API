import requests
import pandas as pd
import os
import io

import sys
import time

#input_info = 'SENSEX'
#expirydate='03-JUN-2025'
#strikemin=int('80000')
#strikemax=int('90000')
#link_file = 'Bfo_Index_Derivatives'
#Suffix="-I"
#Futures='Yes'
#Options='Yes'

input_info = sys.argv[1]
expirydate= sys.argv[2]
strikemin= int(sys.argv[3])
strikemax= int(sys.argv[4])
link_file = sys.argv[5]
Suffix= sys.argv[6]
Futures= sys.argv[7]
Options= sys.argv[8]


link = f'https://flattrade.s3.ap-south-1.amazonaws.com/scripmaster/{link_file}.csv'
outputlist = fr'C:\API\{input_info}FNOMaster.csv'

def flattrade_to_df(link):    
    try:
        response = requests.get(link)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        print("Downloaded data successfully")
        return df
    except Exception as e:
        print(f"Error downloading or processing the file: {e}")
        return

def options_token(input_info=None, outputlist=None, expirydate=None, strikemin=None, strikemax=None, link=None,
                  Suffix=None, Futures='Yes', Options='Yes'):
    def format_strike(strike):
        if float(strike).is_integer():
            return str(int(strike))
        else:
            return f"{strike:.1f}"

    def process_symbol(symbol, local_strikemin=None, local_strikemax=None):
        df_filtered = df[(df['Symbol'] == symbol) & (df['Expiry'] == expirydate)]
        if df_filtered.empty:
            print(f"No data found for Symbol '{symbol}' and Expiry '{expirydate}'.")
            return []

        matched = []

        # Options: CE/PE
        if Options.lower() == 'yes':
            options_df = df_filtered[df_filtered['Optiontype'].isin(['CE', 'PE'])]
            if local_strikemin is not None and local_strikemax is not None:
                options_df = options_df[(options_df['Strike'] >= local_strikemin) & (options_df['Strike'] <= local_strikemax)]

            for _, row in options_df.iterrows():
                exchange = row['Exchange']
                strike = format_strike(row['Strike'])
                optiontype = row['Optiontype']
                token = row['Token']
                full_symbol = f"{symbol}{strike}{optiontype}"
                matched.append([exchange, full_symbol, token])

        # Futures: Optiontype == 'XX'
        if Futures.lower() == 'yes':
            future_df = df_filtered[df_filtered['Optiontype'] == 'XX']
            if not future_df.empty:
                exchange = future_df['Exchange'].values[0]
                token = future_df['Token'].values[0]
                future_symbol = symbol + Suffix if Suffix else symbol
                matched.append([exchange, future_symbol, token])

        return matched

    # Load the DataFrame
    df = flattrade_to_df(link)
    all_matched = []

    if isinstance(input_info, str):
        if os.path.exists(input_info):  # File path
            input_df = pd.read_csv(input_info, header=None, names=['Symbol', 'strikemin', 'strikemax'])
            for _, row in input_df.iterrows():
                symbol = row['Symbol']
                local_strikemin = row['strikemin'] if pd.notna(row['strikemin']) else strikemin
                local_strikemax = row['strikemax'] if pd.notna(row['strikemax']) else strikemax
                matched = process_symbol(symbol, local_strikemin, local_strikemax)
                all_matched.extend(matched)
        else:  # Single symbol string
            matched = process_symbol(input_info, strikemin, strikemax)
            all_matched.extend(matched)
    else:
        print("Invalid input_info. Provide a symbol string or file path.")
        return

    # Save output
    if all_matched:
        result_df = pd.DataFrame(all_matched, columns=['Exchange', 'Symbol', 'Token'])
        result_df.to_csv(outputlist, mode='w', header=True, index=False)
        print(f"Data saved to '{outputlist}'.")
    else:
        print("No matching data found.")




print(input_info,expirydate,strikemin,strikemax,link_file,Suffix,Futures,Options)

options_token(input_info=input_info, outputlist=outputlist, expirydate=expirydate, strikemin=strikemin, strikemax=strikemax,link=link,Suffix=Suffix,Futures=Futures, Options=Options)

time.sleep(60)
