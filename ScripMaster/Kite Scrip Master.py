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

#inputs
'''
sym_type = "1" #1 "" 1 for Single Symbol / Empty for List
sym_name = "NIFTY" #NIFTY ""
sym_list = "NSEEquity" # PreMarket2605 Bhav2605 NSEEquity NSEEquityFutures NSEEquity Options (without list)
link_segment = 'Nfo_Index_Derivatives' #  NSE_Equity BSE_Equity Nfo_Equity_Derivatives Nfo_Index_Derivatives Bfo_Derivatives Commodity 
#segment = 'equity' #equity fno
#exchange = 'NSE'

future_expiry = "27-OCT-2026" #DD-MMM-YYYY
option_expiry = "06-OCT-2026" #DD-MMM-YYYY
weekly = "0" # Weekly Expiry 1 Monthly Expiry 0

strikemin = int("22000") # None
strikemax = int("26000") # None

equity_suffix = "" #"-EQ"
future_suffix="-I"
option_suffix = "-I"# -I -II

Futures="yes"
Options="yes"
datafeed="EST"#  "Amifeed"
do_import= "no"

market_id = 1
group_id = 2
broker_symbol = "no"
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

outputlist = fr"C:\API\Files\{output_nam}{file_suffix}Kite.csv"

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

kite_exchange = {
    "NSE_Equity": "NSE",
    "BSE_Equity": "BSE",
    "Nfo_Equity_Derivatives": "NSE",
    "Nfo_Index_Derivatives": "NSE",
    "Bfo_Equity_Derivatives": "BSE",
    "Bfo_Index_Derivatives": "BSE",
    "Commodity": "MCX",
    "Currency_Derivatives": "NSE",
}
exchange = kite_exchange.get(link_segment, link_segment)

kite_segment = {
    "NSE_Equity": "equity",
    "BSE_Equity": "BSE",
    "Nfo_Equity_Derivatives": "NSE",
    "Nfo_Index_Derivatives": "fno",
    "Bfo_Equity_Derivatives": "BSE",
    "Bfo_Index_Derivatives": "BSE",
    "Commodity": "MCX",
    "Currency_Derivatives": "NSE",
}
segment = kite_segment.get(link_segment, link_segment)

#Kite.instruments
def kite_df():

    url = "https://api.kite.trade/instruments"

    response = requests.get(url)
    response.raise_for_status()

    df = pd.read_csv(
        StringIO(response.text),
        low_memory=False
    )

    mapping = {
        "instrument_token": "Token",
        "tradingsymbol": "TradingSymbol",
        "name": "Symbol",
        "expiry": "Expiry",
        "strike": "Strike",
        "lot_size": "LotSize",
        "instrument_type": "OptionType",
        "exchange": "Exchange",
        "segment": "Segment"
    }

    df = df.rename(columns=mapping)
    df["Symbol"] = df["Symbol"].fillna(df["TradingSymbol"])

    df["OptionType"] = df["OptionType"].replace({
        "FUT": "XX"
    })

    df["Expiry"] = pd.to_datetime(
        df["Expiry"],
        errors="coerce"
    ).dt.strftime("%d-%b-%Y").str.upper()

    return df



#Equity
def kite_eq_df():

    df = kite_df()

    eq_df = df[
        (df["OptionType"] == "EQ")
        &
        (df["Exchange"] == exchange)
    ].copy()

    #print(eq_df)

    return eq_df


#FnO
def kite_fno_df():

    df = kite_df()

    df = df[
        df["Segment"].isin(
            [
                "NFO-FUT",
                "NFO-OPT",
                "BFO-FUT",
                "BFO-OPT"
            ]
        )
    ].copy()

    if "Strike" in df.columns:
        df["Strike"] = pd.to_numeric(
            df["Strike"],
            errors="coerce"
        )

    sort_order = [
        "Symbol",
        "Expiry",
        "OptionType",
        "Strike"
    ]

    df = df.sort_values(
        sort_order
    ).reset_index(drop=True)
    #print(df.head)

    strike_diffs = {}

    for sym, group in df.groupby("Symbol"):

        strikes = sorted(
            group.loc[
                group["OptionType"].isin(
                    ["CE", "PE"]
                ),
                "Strike"
            ].dropna().unique()
        )

        if len(strikes) > 1:

            diff = min(
                j - i
                for i, j in zip(
                    strikes[:-1],
                    strikes[1:]
                )
            )

        else:
            diff = 0

        strike_diffs[sym] = diff

    df["StrikeDiff"] = (
        df["Symbol"]
        .map(strike_diffs)
        .fillna(0)
    )
    #print(df.head)
    return df

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
                date = datetime.strptime(date, "%d-%b-%Y")  # e.g.  "03-JUN-2025" - "%d-%b-%Y"   "03-JUN-2025" - "%d-%b-%Y"
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
            option_symbol = f"{name}{strike}{option}{optfix}"

    return {"future": future_symbol, "option": option_symbol}

def get_symbol_name(broker_symbol, formatted_symbol, trading_symbol):
    if broker_symbol == "yes" and pd.notna(trading_symbol):
        return trading_symbol
    return formatted_symbol


def equity_token(input_sym=None,
                 outputlist=None,
                 market_id=None,
                 group_id=None,
                 equity_suffix="-EQ",
                 do_import="no"):

    df = kite_eq_df()
    all_matched = []

    if not (isinstance(input_sym, str) and os.path.exists(input_sym)):
        print(input_sym)
        print("❌ Equity requires symbol list CSV")
        return

    input_df = pd.read_csv(input_sym, header=None, names=["Symbol"])



    not_found = []


    for _, row in input_df.iterrows():

        symbol = str(row["Symbol"]).strip()

        # Try original, then BE, then BZ
        search_symbols = [
            symbol,
            symbol + "-BE",
            symbol + "-BZ"
        ]

        eq_df = pd.DataFrame()

        for search_symbol in search_symbols:
            eq_df = df[df["TradingSymbol"] == search_symbol]
            if not eq_df.empty:
                break

        if eq_df.empty:
            not_found.append(symbol)
            continue

        r = eq_df.iloc[0]

        all_matched.append([
            r["Exchange"],
            get_symbol_name(                
                broker_symbol,
                f"{symbol}{equity_suffix}",   # Original input symbol
                symbol
            ),
            r["Token"],
            market_id,
            group_id
            
        ])

    if all_matched:
        result_df = pd.DataFrame(
            all_matched,
            columns=["Exchange", "Symbol", "Token", "Market_ID", "Group_ID"]
            #columns=["Symbol", "Token"]
        )
        result_df.to_csv(outputlist, mode="w", header=True, index=False)
        print(result_df)
        print(f"✅ Equity data saved to '{outputlist}'")

        if not_found:
            print("\n❌ Symbols not found:")
            for s in not_found:
                print(s)

            print(f"\nTotal Not Found : {len(not_found)}")

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
                  future_suffix="-I",
                  Futures="yes",
                  Options="yes",
                  datafeed="Amifeed",
                  weekly="0",
                  do_import="no"):

    # --- Load the instrument file ---
    df = kite_fno_df()
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
                    int(row["StrikeDiff"]),
                    weekly
                    
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
                    '',#row["TickSize"],
                    '',#Skip
                    int(row["LotSize"]),
                    row["Expiry"],
                    int(row["StrikeDiff"]),
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
                                #columns=["Symbol", "Token"])
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


if segment == 'equity':
    equity_token(
        input_sym=input_sym,
        outputlist=outputlist,
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
        future_suffix=future_suffix,
        Futures=Futures,
        Options=Options,
        datafeed=datafeed,
        weekly=weekly,
        do_import=do_import
    )


time.sleep(5)

#main
#kite_eq_df()
#kite_fno_df()
