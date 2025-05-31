import requests
import pandas as pd
import os
import io

import sys
import time

#EXCEQ = 'NSE'
EXCEQ =  sys.argv[1]

inputlist = fr'C:\API\{EXCEQ}EquityList.csv'
outputlist = fr'C:\API\{EXCEQ}EquityMaster.csv'
link = f'https://flattrade.s3.ap-south-1.amazonaws.com/scripmaster/{EXCEQ}_Equity.csv'

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

def equity_token(inputlist=None, outputlist=None, link=None):
    # Step 1: Read the input list of symbols
    input_df = pd.read_csv(inputlist, header=None)
    symbol_list = input_df.iloc[:, 0].str.strip().tolist()  # List of symbols

    # Step 2: Load the DataFrame from the provided link
    df = flattrade_to_df(link)  # Assuming you have this function to load the CSV from the link

    # Create an empty list to store matched data
    matched_symbols = []
    
    # Step 3: Match each symbol exactly with the Symbol column of the exchange file
    for sym in symbol_list:
        # Use exact matching in the Symbol column
        match = df[df['Symbol'] == sym]

        if not match.empty:
            # Extract exchange, symbol, and token for the match
            exchange = match['Exchange'].values[0]
            token = match['Token'].values[0]
            matched_symbols.append([exchange, sym, token])
    
    # Step 4: Save the matched data into a new CSV file
    if matched_symbols:
        result_df = pd.DataFrame(matched_symbols, columns=['Exchange', 'Symbol', 'Token'])
        result_df.to_csv(outputlist, index=False)
        print(f"Data saved to {outputlist}")
    else:
        print(f"No matching symbols found in the data.")



print(EXCEQ)

equity_token(inputlist=inputlist, outputlist=outputlist, link=link)

time.sleep(3)
