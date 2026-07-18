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

#Inputs

'''
sym_type = "" #1 "" 1 for Single Symbol / Empty for List
sym_name = "NIFTY" #NIFTY ""
sym_list = "Options" # NSEEquityFutures NSEEquity Options
link_segment = 'Nfo_Equity_Derivatives' #  NSE_Equity BSE_Equity Nfo_Equity_Derivatives Nfo_Index_Derivatives Bfo_Derivatives Commodity 
option_expiry = "30-JUN-2026" #DD-MMM-YYYY
future_expiry = "30-JUN-2026" #DD-MMM-YYYY
strikemin = int("25000") # None
strikemax = int("27000") # None
weekly = "0" # Weekly Expiry 1 Monthly Expiry 0
future_suffix="-I"
Futures="yes"
Options="yes"
datafeed="EST"#  "Amifeed"
do_import= "no"
equity_suffix = "" #"-EQ"

market_id = 1
group_id = 2
broker_symbol = "yes"
'''
sym_type = sys.argv[1]
sym_name = sys.argv[2]
sym_list = sys.argv[3]
link_segment = sys.argv[4]
option_expiry = sys.argv[5].upper()
future_expiry = sys.argv[6].upper() 
strikemin = int(sys.argv[7])
strikemax = int(sys.argv[8])
weekly = sys.argv[9]
future_suffix =sys.argv[10]
Futures=sys.argv[11]
Options=sys.argv[12]
datafeed=sys.argv[13]
do_import=sys.argv[14]
equity_suffix = sys.argv[15]
market_id = sys.argv[16]
group_id = sys.argv[17]
broker_symbol = sys.argv[18]

if sym_type == "1":
    input_sym = sym_name
    output_nam = sym_name
else:
    input_sym = fr'C:\API\Files\{sym_list}List.csv'
    output_nam = sym_list


#option_date = datetime.strptime(option_expiry, "%d-%b-%Y").date()
#future_date = datetime.strptime(future_expiry, "%d-%b-%Y").date()
outputlist = fr"C:\API\Files\{output_nam}Master.csv"

print(sym_type, sym_name, sym_list, link_segment, option_expiry, future_expiry,
strikemin, strikemax, weekly, future_suffix, Futures, Options, datafeed, do_import,
      market_id, group_id, broker_symbol)    

link = f'https://flattrade.s3.ap-south-1.amazonaws.com/scripmaster/{link_segment}.csv'




def flat_fno_df(link):
    # --- Download CSV from Dhan API ---
    response = requests.get(link)
    response.raise_for_status()
    df = pd.read_csv(StringIO(response.text))

    # --- Mapping Dhan columns to common format ---
    mapping = {
        "Exchange": "Exchange",
        "Symbol": "Symbol",
        "Lotsize": "LotSize",
        "Expiry": "Expiry",
        "Strike": "Strike",
        "Optiontype": "OptionType",
        "Tradingsymbol": "TradingSymbol",
        #"TICK_SIZE": "TickSize",
        "Token": "Token"
    }
    df = df.rename(columns=mapping)
    '''
    # --- Expiry: convert to datetime ---
    if "Expiry" in df.columns:
        df["Expiry"] = pd.to_datetime(df["Expiry"], format="%d-%b-%Y", errors="coerce")
    '''
    # --- Strike: ensure numeric ---
    if "Strike" in df.columns:
        df["Strike"] = pd.to_numeric(df["Strike"], errors="coerce")

    # --- Sort data (Symbol → Expiry → OptionType → Strike) ---
    sort_order = ["Symbol", "Expiry", "OptionType", "Strike"]
    df = df.sort_values(sort_order).reset_index(drop=True)

    # --- Compute StrikeDiff per Symbol ---
    strike_diffs = {}
    for sym, group in df.groupby("Symbol"):
        strikes = sorted(group.loc[group["OptionType"].isin(["CE", "PE"]), "Strike"].unique())
        if len(strikes) > 1:
            diff = min([j - i for i, j in zip(strikes[:-1], strikes[1:])])
        else:
            diff = 0  # only 1 strike → set 0 instead of None
        strike_diffs[sym] = diff

    # --- Map StrikeDiff back to df ---
    df["StrikeDiff"] = df["Symbol"].map(strike_diffs)
    '''
    # --- Format Expiry back to dd-mm-YYYY ---
    if "Expiry" in df.columns:
        df["Expiry"] = df["Expiry"].dt.strftime("%d-%b-%Y")
    '''
    return df

#fno_df = flat_fno_df(link)
#print(fno_df)


def flat_eq_df(link):
    response = requests.get(link)
    response.raise_for_status()
    df = pd.read_csv(StringIO(response.text))

    mapping = {
        "Exchange": "Exchange",
        "Symbol": "Symbol",
        "Tradingsymbol": "TradingSymbol",
        "Instrument": "InstrumentType",
        "Token": "Token"
    }
    df = df.rename(columns=mapping)

    # Only EQ series
    df = df[df["InstrumentType"] == "EQ"].copy()

    return df

#eq_df = flat_eq_df(link)
#print(eq_df)




def symbol_format(datafeed, name, strike=None, option=None, date=None, weekly="0", suffix="-I", exchange=None):
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
            option_symbol = f"{name}{strike}{option}"

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
    all_matched = []

    if not (isinstance(input_sym, str) and os.path.exists(input_sym)):
        print("❌ Equity requires symbol list CSV")
        return

    input_df = pd.read_csv(input_sym, header=None, names=["Symbol"])

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

    if all_matched:
        result_df = pd.DataFrame(
            all_matched,
            columns=["Exchange", "Symbol", "Token", "Market_ID", "Group_ID"]
        )
        result_df.to_csv(outputlist, mode="w", header=True, index=False)
        print(result_df)
        print(f"✅ Equity data saved to '{outputlist}'")

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

            if local_strikemin is not None and local_strikemax is not None:
                options_df = options_df[
                    (options_df["Strike"] >= local_strikemin)
                    & (options_df["Strike"] <= local_strikemax)
                ]

            for _, row in options_df.iterrows():
                sf = symbol_format(
                    datafeed=datafeed,
                    name=row["Symbol"],
                    strike=int(row["Strike"]),
                    option=row["OptionType"],
                    date=row["Expiry"],
                    weekly=weekly,
                    suffix=future_suffix,
                    exchange=row["Exchange"],
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
                    int(row["LotSize"]),
                    #row["TickSize"],
                    row["Expiry"],
                    int(row["StrikeDiff"])
                    
                ])

        # --- Futures ---
        if Futures == "yes" and future_expiry:
            df_filtered = df[(df["Symbol"] == symbol) & (df["Expiry"] == future_expiry)]
            #df_filtered = df[df["Symbol"] == symbol]
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
                    int(row["LotSize"]),
                    #row["TickSize"],
                    row["Expiry"],
                    int(row["StrikeDiff"])
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
                                 columns=["Exchange", "Symbol", "Token", "Market_ID", "Group_ID", "LotSize", "Expiry", "StrikeDiff"])
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


time.sleep(5)
