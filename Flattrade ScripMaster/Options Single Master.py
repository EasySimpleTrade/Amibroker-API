import requests
import pandas as pd
import io
import sys
import time

#Symbol = 'NIFTY'
#expirydate='13-MAR-2025'
#strikemin=int('20000')
#strikemax=int('24000')


Symbol =  sys.argv[1]
expirydate =  sys.argv[2]
strikemin =  int(sys.argv[3])
strikemax =  int(sys.argv[4])

outputlist = fr'C:\API\{Symbol}OptionsMaster.csv'

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


def options_token_single(Symbol, outputlist=None, expirydate=None, strikemin=None, strikemax=None, link=None):
    # Load the DataFrame from the provided link
    df = flattrade_to_df(link)
    
    # Step 1: Filter the DataFrame for the symbol and expiry date
    df_filtered = df[(df['Symbol'] == Symbol) & (df['Expiry'] == expirydate)]
    
    # Check if the filtered DataFrame is not empty after symbol and expiry date match
    if not df_filtered.empty:
        # Step 2: Further filter for Optiontype as 'CE' (Call) or 'PE' (Put)
        options_df = df_filtered[(df_filtered['Optiontype'] == 'CE') | (df_filtered['Optiontype'] == 'PE')]

        # Step 3: If strikemin and strikemax are provided, filter based on the strike price range
        if strikemin is not None and strikemax is not None:
            options_df = options_df[(options_df['Strike'] >= strikemin) & (options_df['Strike'] <= strikemax)]

        # If no matches are found after all filtering
        if options_df.empty:
            print(f"No matching options found for Symbol '{Symbol}' with expiry '{expirydate}'.")
            return
        
        # Step 4: Prepare the results with concatenated Symbol (Symbol + Strike + (CE/PE))
        matched_options = []
        for _, row in options_df.iterrows():
            exchange = row['Exchange']
            strike = str(int(row['Strike']))  # Convert to string and remove decimal if any            
            optiontype = row['Optiontype']
            token = row['Token']
            symbol_concat = f"{Symbol}{strike}{optiontype}"  # Concatenate Symbol, Strike, and Optiontype
            matched_options.append([exchange, symbol_concat, token])
        
        # Step 5: Convert to DataFrame
        result_df = pd.DataFrame(matched_options, columns=['Exchange', 'Symbol', 'Token'])
        
        # Step 6: Write the data to the output CSV (overwrite existing file)
        result_df.to_csv(outputlist, mode='w', header=True, index=False)
        print(f"File '{outputlist}' created with headers and details for options of Symbol '{Symbol}' written.")
    else:
        print(f"No matching symbol or expiry found for Symbol '{Symbol}' with expiry '{expirydate}'.")


link = 'https://flattrade.s3.ap-south-1.amazonaws.com/scripmaster/Nfo_Index_Derivatives.csv'





print(Symbol,expirydate,strikemin,strikemax,outputlist)


options_token_single(Symbol=Symbol, outputlist=outputlist, expirydate=expirydate, strikemin=strikemin, strikemax=strikemax, link=link)
time.sleep(3)
