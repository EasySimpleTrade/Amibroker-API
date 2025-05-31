import requests
import pandas as pd
import io
import time

import sys


#expirydate = '29-MAY-2025'
expirydate = sys.argv[1]
link = 'https://flattrade.s3.ap-south-1.amazonaws.com/scripmaster/Nfo_Equity_Derivatives.csv'
inputlist = r'C:\API\OptionsList.csv'
outputlist = r'C:\API\OptionsMaster.csv'



def flattrade_to_df(link):    
    try:
        response = requests.get(link)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        print('Downloaded data successfully')
        return df
    except Exception as e:
        print(f"Error downloading or processing the file: {e}")
        return
    


def options_token_list(inputlist=None, outputlist=None, expirydate=None, link=None):
    # Step 1: Read the input list of symbols, strikemin, and strikemax (no header)
    input_df = pd.read_csv(inputlist, header=None, names=['Symbol', 'strikemin', 'strikemax'])
    
    # Step 2: Load the DataFrame from the provided link
    df = flattrade_to_df(link)

    # Create an empty list to store matched data
    matched_options = []

    # Step 3: Iterate over each row in the input list
    for index, row in input_df.iterrows():
        symbol = row['Symbol']
        strikemin = row['strikemin']
        strikemax = row['strikemax']

        # Filter the DataFrame for the symbol and expiry date
        df_filtered = df[(df['Symbol'] == symbol) & (df['Expiry'] == expirydate)]

        if not df_filtered.empty:
            # Further filter for Optiontype as 'CE' or 'PE'
            options_df = df_filtered[(df_filtered['Optiontype'] == 'CE') | (df_filtered['Optiontype'] == 'PE')]

            # If strikemin and strikemax are provided, filter based on the strike price range
            if pd.notna(strikemin) and pd.notna(strikemax):
                options_df = options_df[(options_df['Strike'] >= strikemin) & (options_df['Strike'] <= strikemax)]

            # Check if there are matching options after filtering
            if not options_df.empty:
                for _, option_row in options_df.iterrows():
                    exchange = option_row['Exchange']
                    strike = option_row['Strike']
                    
                    # Convert strike price: If it's an integer, remove decimal; if not, keep one decimal place
                    if strike.is_integer():
                        strike = str(int(strike))  # Convert integer strike to string without decimals
                    else:
                        strike = f"{strike:.1f}"  # Keep one decimal place for float values

                    optiontype = option_row['Optiontype']
                    token = option_row['Token']
                    symbol_concat = f"{symbol}{strike}{optiontype}"  # Concatenate Symbol, Strike, and Optiontype
                    matched_options.append([exchange, symbol_concat, token])

    # Step 4: Convert the matched options to a DataFrame
    result_df = pd.DataFrame(matched_options, columns=['Exchange', 'Symbol', 'Token'])

    # Step 5: Write the data to the output CSV (overwrite existing file)
    result_df.to_csv(outputlist, mode='w', header=True, index=False)
    print(f"Options data saved to {outputlist}.")
    

options_token_list(inputlist, outputlist, expirydate, link)
time.sleep(3)
