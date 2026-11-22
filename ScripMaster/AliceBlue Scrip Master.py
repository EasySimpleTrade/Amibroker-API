'''
VALLAKKOTTAI MURUGAN THUNAI
Easy Simple Trading Solutions
Telegram @easysimpletradeupdates
Website https://easysimpletrade.blogspot.com
Youtube https://www.youtube.com/@easysimpletrade
GitHub https://github.com/EasySimpleTrade
'''

import requests
import pandas as pd
from io import StringIO
from datetime import datetime
import os
import win32com.client
import time
import sys
from collections import Counter

#Inputs

'''
sym_type = "" #1 "" 1 for Single Symbol / Empty for List
sym_name = "NIFTY" #NIFTY ""
sym_list = "Options" # NSEEquity BSEEquity NSEEquityFutures Options 
link_segment = 'Nfo_Index_Derivatives' #  NSE_Equity BSE_Equity Nfo_Equity_Derivatives Nfo_Index_Derivatives Bfo_Derivatives Commodity Currency_Derivatives BCD
option_expiry = "29-SEP-2026" #DD-MMM-YYYY
future_expiry = "29-SEP-2026" #DD-MMM-YYYY
strikemin = int("25000") # None
strikemax = int("27000") # None
weekly = "0" # Weekly Expiry 1 Monthly Expiry 0
future_suffix="-I"
Futures="yes" #yes no
Options="yes" #yes no
datafeed="EST"#  "Amifeed"
do_import= "no"
equity_suffix = "" #"-EQ"

market_id = 1
group_id = 2
broker_symbol = "no"
option_suffix = "-I"# -I -II

'''

sym_type = sys.argv[1]
sym_name = sys.argv[2]
sym_list = sys.argv[3]

link_segment = sys.argv[4]

future_expiry = sys.argv[5].upper() 
option_expiry = sys.argv[6].upper()
weekly = sys.argv[7]

strikemin = int(sys.argv[8])
strikemax = int(sys.argv[9])

equity_suffix = sys.argv[10]
future_suffix =sys.argv[11]
option_suffix = sys.argv[12]

Futures=sys.argv[13]
Options=sys.argv[14]

datafeed=sys.argv[15]
do_import=sys.argv[16]

market_id = sys.argv[17]
group_id = sys.argv[18]
broker_symbol = sys.argv[19]



if sym_type == "1":
    input_sym = sym_name
    output_nam = sym_name
else:
    input_sym = fr'C:\API\Files\{sym_list}List.csv'
    output_nam = sym_list

if future_suffix =="-III" or option_suffix == "-III":
    file_suffix = "-III"
elif future_suffix =="-II" or option_suffix == "-II":
    file_suffix = "-II"
else:
    file_suffix = ""    


#option_date = datetime.strptime(option_expiry, "%d-%b-%Y").date()
#future_date = datetime.strptime(future_expiry, "%d-%b-%Y").date()
#outputlist = fr"C:\API\Files\{output_nam}{file_suffix}Master.csv"
outputlist = fr"C:\API\{output_nam}{file_suffix}Master.csv"

print("sym_type      =", repr(sym_type))
print("sym_name      =", repr(sym_name))
print("sym_list      =", repr(sym_list))
print("link_segment  =", repr(link_segment))
print("future_expiry =", repr(future_expiry))
print("option_expiry =", repr(option_expiry))
print("strikemin     =", repr(strikemin))
print("strikemax     =", repr(strikemax))
print("weekly        =", repr(weekly))
print("equity_suffix =", repr(equity_suffix))
print("future_suffix =", repr(future_suffix))
print("option_suffix =", repr(option_suffix))
print("Futures       =", repr(Futures))
print("Options       =", repr(Options))
print("datafeed      =", repr(datafeed))
print("do_import     =", repr(do_import))
print("market_id     =", repr(market_id))
print("group_id      =", repr(group_id))
print("broker_symbol =", repr(broker_symbol))

#time.sleep(10)

# AliceBlue contract-master links
aliceblue_segment = {
    "NSE_Equity": "NSE",
    "BSE_Equity": "BSE",
    "Nfo_Equity_Derivatives": "NFO",
    "Nfo_Index_Derivatives": "NFO",
    "Bfo_Equity_Derivatives": "BFO",
    "Bfo_Index_Derivatives": "BFO",
    "Commodity": "MCX",
    "Currency_Derivatives": "CDS",
    "BSE_Currency_Derivatives": "BCD",
}

aliceblue_file = aliceblue_segment.get(link_segment, link_segment)
link = f"https://v2api.aliceblueonline.com/restpy/static/contract_master/V2/{aliceblue_file}"
#print(link)
#time.sleep(10)

def format_number(x):
    x = float(x)
    if x.is_integer():
        return str(int(x))
    return f"{x:g}"

def flat_fno_df(link):
    # --- Download AliceBlue contract master JSON ---
    response = requests.get(link, timeout=60)
    response.raise_for_status()
    data = response.json()


    # AliceBlue returns:
    # {
    #   "NFO": [
    #       {"symbol": ..., "option_type": ..., "expiry_date": ...,
    #        "instrument_type": ..., "token": ..., "trading_symbol": ...,
    #        "exch": ..., "lot_size": ..., "strike_price": ...}
    #   ]
    # }
    if isinstance(data, dict):
        rows = data.get(aliceblue_file, [])
        if not rows:
            # Keep this tolerant if the response key differs from the URL segment.
            for value in data.values():
                if isinstance(value, list):
                    rows = value
                    break
    elif isinstance(data, list):
        rows = data
    else:
        rows = []

    df = pd.DataFrame(rows)

    # --- Mapping AliceBlue columns to the common format used below ---
    mapping = {
        "exch": "Exchange",
        "symbol": "Symbol",
        "lot_size": "LotSize",
        "expiry_date": "Expiry",
        "strike_price": "Strike",
        "option_type": "OptionType",
        "trading_symbol": "TradingSymbol",
        "token": "Token",
        "instrument_type": "InstrumentType",
    }
    df = df.rename(columns=mapping)

    # --- Normalize fields used by the existing filtering logic ---
    if "Strike" in df.columns:
        df["Strike"] = pd.to_numeric(df["Strike"], errors="coerce")

    if "LotSize" in df.columns:
        df["LotSize"] = pd.to_numeric(df["LotSize"], errors="coerce")

    # AliceBlue expiry_date is epoch milliseconds.
    if "Expiry" in df.columns:
        df["Expiry"] = pd.to_datetime(
            pd.to_numeric(df["Expiry"], errors="coerce"),
            unit="ms",
            errors="coerce",
            utc=True
        ).dt.strftime("%d-%b-%Y").str.upper()

    # The existing options_token() expects "XX" for futures.
    if "OptionType" in df.columns:
        df["OptionType"] = df["OptionType"].fillna("")
        df.loc[
            ~df["OptionType"].isin(["CE", "PE"]),
            "OptionType"
        ] = "XX"

    # --- Sort data (Symbol → Expiry → OptionType → Strike) ---
    sort_order = [c for c in ["Symbol", "Expiry", "OptionType", "Strike"] if c in df.columns]
    if sort_order:
        df = df.sort_values(sort_order).reset_index(drop=True)

    return df


#fno_df = flat_fno_df(link)
#print(fno_df)


def flat_eq_df(link):
    # --- Download AliceBlue contract master JSON ---
    response = requests.get(link, timeout=60)
    response.raise_for_status()
    data = response.json()


    if isinstance(data, dict):
        rows = data.get(aliceblue_file, [])
        if not rows:
            for value in data.values():
                if isinstance(value, list):
                    rows = value
                    break
    elif isinstance(data, list):
        rows = data
    else:
        rows = []

    df = pd.DataFrame(rows)

    # --- Mapping AliceBlue columns to the common format used below ---
    mapping = {
        "exch": "Exchange",
        "symbol": "Symbol",
        "trading_symbol": "TradingSymbol",
        "instrument_type": "InstrumentType",
        "token": "Token",
    }
    df = df.rename(columns=mapping)

    # AliceBlue NSE/BSE equity masters use instrument_type "0".
    # Keep the original segment-specific equity filtering behavior.
    if link_segment == "NSE_Equity":
        df = df[df["InstrumentType"].astype(str) == "0"]
    elif link_segment == "BSE_Equity":
        df = df[df["InstrumentType"].astype(str) == "E"]

    return df


#eq_df = flat_eq_df(link)
#print(eq_df)




def symbol_format(datafeed, name, strike=None, option=None, date=None, weekly="0", suffix="-I", exchange=None,optfix=''):
    # --- Futures ---
    future_symbol = name + suffix if suffix else name
    #print(weekly)
    # --- Options ---
    option_symbol = None
    if strike is not None and option:
        if isinstance(date, str):
            #print(date)
            try:
                date = datetime.strptime(date, "%d-%m-%Y")  # e.g.  "03-06-2025" - "%d-%m-%Y"   "03-JUN-2025" - "%d-%b-%Y"
                #print("DBY",date)
            except:
                pass

        if datafeed == "Amifeed":
            if weekly == "1":
                option_symbol = f"{name}WK{strike}{option}"
            else:
                option_symbol = f"{name}{strike}{option}"

        elif datafeed == "EqualSolutions" and isinstance(date, datetime):
            if weekly == "1":
                option_symbol = f"{name}{date.strftime('%y').upper()}{date.strftime('%b').upper()}{date.strftime('%d')}_{strike}{option}"
            else:
                option_symbol = f"{name}{date.strftime('%y').upper()}{date.strftime('%b').upper()}_{strike}{option}"
        else:
            option_symbol = f"{name}{format_number(strike)}{option}{optfix}"

    return {"future": future_symbol, "option": option_symbol}

def get_symbol_name(broker_symbol, formatted_symbol, trading_symbol):
    if broker_symbol == "yes" and pd.notna(trading_symbol):
        return trading_symbol
    return formatted_symbol


def equity_token(input_sym=None,
                 outputlist=None,
                 link=None,
                 market_id=None,
                 group_id=None,
                 equity_suffix="-EQ",
                 do_import="no"):

    df = flat_eq_df(link)
    #print(df)
    all_matched = []
    
    if not (isinstance(input_sym, str) and os.path.exists(input_sym)):
        print("❌ Equity requires symbol list CSV")
        return

    input_df = pd.read_csv(input_sym, header=None, names=["Symbol"])
    #print(input_df)
    time.sleep(5)
    for _, row in input_df.iterrows():
        symbol = row["Symbol"]

        eq_df = df[df["Symbol"] == symbol]
        if eq_df.empty:
            continue

        r = eq_df.iloc[0]
        all_matched.append([
            r["Exchange"],
            get_symbol_name(
            broker_symbol,
            f"{r['Symbol']}{equity_suffix}",
            r["TradingSymbol"]
            ),
            r["Token"],
            market_id,
            group_id
        ])
    #print(all_matched)
    time.sleep(5)
    if all_matched:
        result_df = pd.DataFrame(
            all_matched,
            columns=["Exchange", "Symbol", "Token", "Market_ID", "Group_ID"]
        )
        #print(result_df)
        time.sleep(5)
        result_df.to_csv(outputlist, mode="w", header=True, index=False)
        print(result_df)
        print(f"✅ Equity data saved to '{outputlist}'")
        time.sleep(5)
        if do_import == "yes":
            try:
                AB = win32com.client.Dispatch("Broker.Application")
                AB.Import(0, outputlist, "MasterInfo.format")
                print("📥 Equity import completed")
            except Exception as e:
                print(f"❌ Import error: {str(e)}")
    else:
        print("⚠️ No equity symbols matched")


def options_token(input_sym=None,
                  outputlist=None,
                  market_id=None,
                  group_id=None,
                  option_expiry=None,
                  future_expiry=None,
                  strikemin=None,
                  strikemax=None,
                  link=None,
                  future_suffix="-I",
                  Futures="yes",
                  Options="yes",
                  datafeed="Amifeed",
                  weekly="0",
                  do_import="no"):

    # --- Load the instrument file ---
    df = flat_fno_df(link)
    #print(df)

    all_matched = []

    def process_symbol(symbol, local_strikemin=None, local_strikemax=None):
        matched = []

        # --- Options ---
        if Options == "yes" and option_expiry:
            df_filtered = df[(df["Symbol"] == symbol) & (df["Expiry"] == option_expiry)]
        

            options_df = df_filtered[df_filtered["OptionType"].isin(["CE", "PE"])]
            

            #--------------------------------------


            strikes = sorted(options_df["Strike"].unique())

            diffs = [round(j - i, 2) for i, j in zip(strikes[:-1], strikes[1:])]

            
            diff_count = Counter(diffs)

            strike_diff = diff_count.most_common(1)[0][0] if diff_count else 0
            strike_diff = format_number(strike_diff)

            #-------------------------------------

            if local_strikemin is not None and local_strikemax is not None:
                options_df = options_df[
                    (options_df["Strike"] >= local_strikemin)
                    & (options_df["Strike"] <= local_strikemax)
                ]

            for _, row in options_df.iterrows():
                sf = symbol_format(
                    datafeed=datafeed,
                    name=row["Symbol"],
                    #strike=int(row["Strike"]),#Strrike
                    strike=row["Strike"],#Strrike
                    option=row["OptionType"],
                    date=row["Expiry"],
                    weekly=weekly,
                    suffix=future_suffix,
                    exchange=row["Exchange"],
                    optfix=option_suffix,
                )
                matched.append([
                    row["Exchange"],
                    get_symbol_name(
                    broker_symbol,
                    sf["option"],
                    row["TradingSymbol"]
                    ),
                    row["Token"],
                    market_id,
                    group_id,
                    '',#row["TickSize"],
                    '',#Skip
                    int(row["LotSize"]),                   
                    row["Expiry"],
                    strike_diff,
                    weekly
                    
                ])

        # --- Futures ---
        if Futures == "yes" and future_expiry:
            df_filtered = df[(df["Symbol"] == symbol) & (df["Expiry"] == future_expiry)]
            strikes = sorted(
                df_filtered.loc[df_filtered["OptionType"].isin(["CE", "PE"]), "Strike"].unique()
            )

            #strikes = sorted(df_filtered["Strike"].unique())

            diffs = [round(j - i, 2) for i, j in zip(strikes[:-1], strikes[1:])]

            
            diff_count = Counter(diffs)

            strike_diff = diff_count.most_common(1)[0][0] if diff_count else 0
            strike_diff = format_number(strike_diff)

            
            future_df = df_filtered[df_filtered["OptionType"] == "XX"]

            if not future_df.empty:
                row = future_df.iloc[0]
                sf = symbol_format(
                    datafeed=datafeed,
                    name=row["Symbol"],
                    strike=None,
                    option=None,
                    date=row["Expiry"],
                    weekly="0",
                    suffix=future_suffix,
                    exchange=row["Exchange"],
                    optfix=option_suffix,
                )
                matched.append([
                    row["Exchange"],
                    get_symbol_name(
                    broker_symbol,
                    sf["future"],
                    row["TradingSymbol"]
                    ),

                    row["Token"],
                    market_id,
                    group_id,
                    '',#row["TickSize"],
                    '',#Skip
                    int(row["LotSize"]),                    
                    row["Expiry"],
                    strike_diff,
                    weekly
                ])

        return matched

    # --- Single symbol or file input ---
    if isinstance(input_sym, str):
        if os.path.exists(input_sym):  # File with multiple symbols
            input_df = pd.read_csv(input_sym, header=None, names=["Symbol", "strikemin", "strikemax"])
            for _, row in input_df.iterrows():
                symbol = row["Symbol"]
                local_strikemin = row["strikemin"] if pd.notna(row["strikemin"]) else strikemin
                local_strikemax = row["strikemax"] if pd.notna(row["strikemax"]) else strikemax
                matched = process_symbol(symbol, local_strikemin, local_strikemax)
                all_matched.extend(matched)
        else:  # Single symbol string
            matched = process_symbol(input_sym, strikemin, strikemax)
            all_matched.extend(matched)
    else:
        print("❌ Invalid input_sym. Provide a symbol string or file path.")
        return

    # --- Save results ---
    if all_matched:
        result_df = pd.DataFrame(all_matched,
                                 columns=["Exchange", "Symbol", "Token", "Market_ID", "Group_ID", "TickSize","Extra1","LotSize", "Expiry", "StrikeDiff","Weekly"])
        result_df.to_csv(outputlist, mode="w", header=True, index=False)
        print(result_df)
        print(f"✅ Data saved to '{outputlist}'")

        # --- Import into AmiBroker ---
        if do_import == "yes":
            try:
                AB = win32com.client.Dispatch("Broker.Application")
                AB.Import(0, outputlist, "MasterInfo.format")
                print("📥 Import to AmiBroker completed successfully")
            except Exception as e:
                print(f"❌ Error during import: {str(e)}")

    else:
        print("⚠️ No matching data found.")


if link_segment in ["NSE_Equity", "BSE_Equity"]:
    equity_token(
        input_sym=input_sym,
        outputlist=outputlist,
        link=link,
        market_id=market_id,
        group_id=group_id,
        equity_suffix=equity_suffix,
        do_import=do_import
    )
else:
    options_token(
        input_sym=input_sym,
        outputlist=outputlist,
        market_id=market_id,
        group_id=group_id,
        option_expiry=option_expiry,
        future_expiry=future_expiry,
        strikemin=strikemin,
        strikemax=strikemax,
        link=link,
        future_suffix=future_suffix,
        Futures=Futures,
        Options=Options,
        datafeed=datafeed,
        weekly=weekly,
        do_import=do_import
    )


time.sleep(3)

