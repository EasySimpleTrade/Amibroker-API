import requests
import pandas as pd
import os
import io

import sys
import time

#file_prefix = 'NSEEquityFutures'
#link_file = 'Nfo_Equity_Derivatives'
#expirydate='26-JUN-2025'

file_prefix = sys.argv[1]
link_file = sys.argv[2]
expirydate=sys.argv[3]

input_info = fr'C:\API\{file_prefix}List.csv'
outputlist = fr'C:\API\{file_prefix}Master.csv'
link = f'https://flattrade.s3.ap-south-1.amazonaws.com/scripmaster/{link_file}.csv'

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
import pandas as pd
import os

def futures_token(input_info=None, outputlist=None, expirydate=None, Suffix=None, link=None):

    # Load the data
    df = flattrade_to_df(link)

    def get_futures_row(symbol):
        match = df[(df['Symbol'] == symbol) & (df['Optiontype'] == 'XX') & (df['Expiry'] == expirydate)]
        if not match.empty:
            exchange = match['Exchange'].values[0]
            token = match['Token'].values[0]
            full_symbol = symbol + Suffix if Suffix else symbol
            return [exchange, full_symbol, token]
        else:
            print(f"No matching futures data found for Symbol '{symbol}' with expiry '{expirydate}'.")
            return None

    matched_futures = []

    # Case 1: File path (CSV with symbol list)
    if isinstance(input_info, str) and os.path.exists(input_info):
        input_df = pd.read_csv(input_info, header=None)
        symbol_list = input_df.iloc[:, 0].astype(str).str.strip().tolist()
        for symbol in symbol_list:
            row = get_futures_row(symbol)
            if row:
                matched_futures.append(row)

    # Case 2: Single symbol string
    elif isinstance(input_info, str):
        row = get_futures_row(input_info.strip())
        if row:
            matched_futures.append(row)

    else:
        print("Invalid input_info. Provide a symbol string or CSV file path.")
        return

    # Save the result
    if matched_futures and outputlist:
        result_df = pd.DataFrame(matched_futures, columns=['Exchange', 'Symbol', 'Token'])
        result_df.to_csv(outputlist, index=False)
        print(f"Futures data saved to {outputlist}")
    elif not outputlist:
        print("Output list path not provided.")
    else:
        print("No matching futures tokens found.")




print(file_prefix,link_file,expirydate)


futures_token(input_info=input_info, outputlist=outputlist, expirydate=expirydate,Suffix="-I",link=link)


time.sleep(3)
