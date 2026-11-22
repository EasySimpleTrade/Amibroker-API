import sys
import gzip
import json
import requests
import pandas as pd
import win32com.client

from io import BytesIO
from collections import Counter

import os
import time


# ============================================================
# INPUTS
# ============================================================
'''
sym_type = "" #1 "" 1 for Single Symbol / Empty for List
sym_name = "NIFTY"
sym_list = "BSEEquity" # NSEEquity BSEEquity NSEEquityFutures Options 

exchange = "BSE" #NSE BSE MCX

future_expiry = "25-AUG-2026"
option_expiry = "25-AUG-2026"

strikemin = 23000
strikemax = 26000

equity_suffix = ""

future_suffix = "-I"
option_suffix = "-I"

Futures = "no"
Options = "no"

datafeed = "EST"
do_import = "no"

market_id = 1 # 1 NSE , 2 BSE, 3 MCX
group_id = 1 # 1 NSE EQ, 2 NSE FO, 3 BSE EQ, 4  BSE FO, 5 MCX, 6 CDS
'''

# ============================================================
# COMMAND LINE ARGUMENTS
# ============================================================


if len(sys.argv) > 1:

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
    future_suffix = sys.argv[11]
    option_suffix = sys.argv[12]

    Futures = sys.argv[13]
    Options = sys.argv[14]

    datafeed = sys.argv[15]
    do_import = sys.argv[16]

    market_id = int(sys.argv[17])
    group_id = int(sys.argv[18])
    broker_symbol = sys.argv[19]

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


#time.sleep(3)

upstox_segment = {
    "NSE_Equity": "NSE",
    "BSE_Equity": "BSE",
    "Nfo_Equity_Derivatives": "NSE",
    "Nfo_Index_Derivatives": "NSE",
    "Bfo_Equity_Derivatives": "BSE",
    "Bfo_Index_Derivatives": "BSE",
    "Commodity": "MCX",
    "Currency_Derivatives": "NSE",
}

exchange = upstox_segment.get(link_segment, link_segment)

# ============================================================
# INPUT SYMBOL / OUTPUT NAME
# ============================================================

if sym_type == "1":

    input_sym = sym_name
    output_nam = sym_name

else:

    input_sym = fr"C:\API\Files\{sym_list}List.csv"
    output_nam = sym_list


# ============================================================
# FILE SUFFIX
# ============================================================

if (
    future_suffix == "-III"
    or option_suffix == "-III"
):

    file_suffix = "-III"

elif (
    future_suffix == "-II"
    or option_suffix == "-II"
):

    file_suffix = "-II"

else:

    file_suffix = ""


# ============================================================
# OUTPUT FILE
# ============================================================

outputlist = fr"C:\API\Files\{output_nam}{file_suffix}Upstox.csv"

# ============================================================
# UPSTOX DOWNLOAD LINK
# ============================================================

link = (
    "https://assets.upstox.com/"
    "market-quote/instruments/exchange/"
    f"{exchange}.json.gz"
)

print(link)
# ============================================================
# DOWNLOAD + EXTRACT + JSON -> DATAFRAME
# ============================================================

def link_to_df(link):

    #print()
    #print("=" * 60)
    print(f"Downloading Upstox {exchange} Instrument Master")
    #print("=" * 60)

    # --------------------------------------------------------
    # Download GZ into memory
    # --------------------------------------------------------

    #print("Downloading...")

    response = requests.get(
        link,
        timeout=120
    )

    response.raise_for_status()

    print(
        f"Downloaded : {len(response.content):,} bytes"
    )

    # --------------------------------------------------------
    # Extract GZ directly in memory
    # --------------------------------------------------------

    print("Extracting...")

    json_bytes = gzip.decompress(
        response.content
    )

    print(
        f"Extracted  : {len(json_bytes):,} bytes"
    )

    # --------------------------------------------------------
    # JSON -> Python object
    # --------------------------------------------------------

    print("Parsing JSON...")

    data = json.loads(
        json_bytes
    )

    # --------------------------------------------------------
    # JSON -> DataFrame
    # --------------------------------------------------------

    df = pd.DataFrame(
        data
    )

    # --------------------------------------------------------
    # Information
    # --------------------------------------------------------
    '''
    print()
    print(
        f"Records : {len(df):,}"
    )

    print(
        f"Columns : {len(df.columns)}"
    )

    print()
    print("Columns:")
    print(
        df.columns.tolist()
    )

    print()
    print("Segment:")
    print(
        df["segment"]
        .value_counts(dropna=False)
    )

    print()'''

    print("Instrument Type:")
    print(
        df["instrument_type"]
        .value_counts(dropna=False)
    )

    print()

    return df


# ============================================================
# FORMAT NUMBER
# ============================================================

def format_number(value):

    if pd.isna(value):
        return ""

    try:

        value = float(value)

        if value.is_integer():

            return str(
                int(value)
            )

        return f"{value:g}"

    except Exception:

        return str(value)


# ============================================================
# CUSTOM SYMBOL FORMAT
# ============================================================

def format_custom_symbol(
    symbol,
    instrument_type,
    strike_price=None
):

    # --------------------------------------------------------
    # Futures
    # --------------------------------------------------------

    if instrument_type == "FUT":

        return (
            f"{symbol}"
            f"{future_suffix}"
        )

    # --------------------------------------------------------
    # Options
    # --------------------------------------------------------

    if instrument_type in [
        "CE",
        "PE"
    ]:

        strike = format_number(
            strike_price
        )

        return (
            f"{symbol}"
            f"{strike}"
            f"{instrument_type}"
            f"{option_suffix}"
        )

    # --------------------------------------------------------
    # Equity / other
    # --------------------------------------------------------

    return symbol


# ============================================================
# DOWNLOAD DATAFRAME
# ============================================================

df = link_to_df(
    link
)


# ============================================================
# TEST
# ============================================================
'''
print()
print("=" * 60)
print("DATAFRAME READY")
print("=" * 60)

print(
    df.head()
)

print()
print(
    f"Total records: {len(df):,}"
)

'''
# ============================================================
# FORMAT NUMBER
# ============================================================

def format_number(value):

    if pd.isna(value):
        return ""

    try:

        value = float(value)

        if value.is_integer():
            return str(int(value))

        return f"{value:g}"

    except Exception:

        return str(value)


# ============================================================
# FORMAT EXPIRY
# ============================================================

def format_expiry(value):

    if pd.isna(value):
        return ""

    try:

        return pd.to_datetime(
            value,
            unit="ms"
        ).strftime(
            "%d-%b-%Y"
        ).upper()

    except Exception:

        return ""


# ============================================================
# FORMAT WEEKLY
# ============================================================

def format_weekly(value):

    if pd.isna(value):
        return 0

    if isinstance(value, str):

        value = value.strip().lower()

        if value in ["true", "1", "yes"]:
            return 1

        return 0

    return 1 if bool(value) else 0


# ============================================================
# CUSTOM SYMBOL
# ============================================================

def format_custom_symbol(
    symbol,
    instrument_type,
    strike_price=None
):

    # --------------------------------------------------------
    # Future
    # --------------------------------------------------------

    if instrument_type == "FUT":

        return (
            f"{symbol}"
            f"{future_suffix}"
        )

    # --------------------------------------------------------
    # Option
    # --------------------------------------------------------

    if instrument_type in ["CE", "PE"]:

        strike = format_number(
            strike_price
        )

        return (
            f"{symbol}"
            f"{strike}"
            f"{instrument_type}"
            f"{option_suffix}"
        )

    return symbol

# ============================================================
# EQUITY TOKEN
# ============================================================

def equity_token(
    input_sym=None,
    outputlist=None,
    df=None,
    exchange=None,
    market_id=None,
    group_id=None,
    equity_suffix="",
    do_import="no"
):

    print()
    print("=" * 20)
    print(f"{exchange} EQUITY")
    print("=" * 20)

    # --------------------------------------------------------
    # Upstox Equity
    # --------------------------------------------------------

    eq_df = df[
        (df["segment"] == f"{exchange}_EQ") 
    ].copy()

    if eq_df.empty:

        print(
            f"❌ No {exchange} equity data found"
        )

        return

    # --------------------------------------------------------
    # Equity requires symbol list CSV
    # --------------------------------------------------------

    if not (
        isinstance(input_sym, str)
        and os.path.exists(input_sym)
    ):

        print(f'{input_sym} not found')
        print(
            "❌ Equity requires symbol list CSV"
        )

        return

    # --------------------------------------------------------
    # Read symbol list
    # --------------------------------------------------------

    input_df = pd.read_csv(
        input_sym,
        header=None,
        names=["Symbol"]
    )

    input_df["Symbol"] = (
        input_df["Symbol"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Process symbols
    # --------------------------------------------------------

    all_matched = []

    for _, input_row in input_df.iterrows():

        symbol = input_row["Symbol"]

        matched = eq_df[
            eq_df["trading_symbol"] == symbol
        ]

        if matched.empty:

            print(
                f"⚠️ Equity not found: {symbol}"
            )

            continue

        row = matched.iloc[0]

        # ----------------------------------------------------
        # Equity symbol
        #
        # Input symbol is retained.
        # ----------------------------------------------------

        output_symbol = (
            f"{symbol}"
            f"{equity_suffix}"
        )

        all_matched.append([

            row["exchange"],

            output_symbol,

            row["exchange_token"],

            market_id,

            group_id,

            row["tick_size"],

            row["instrument_key"]

        ])

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    if all_matched:

        result_df = pd.DataFrame(
            all_matched,
            columns=[
                "Exchange",
                "Symbol",
                "Token",
                "Market_ID",
                "Group_ID",
                "TickSize",
                "Instrument_Key"
            ]
        )

        # ----------------------------------------------------
        # Token numeric
        # ----------------------------------------------------

        result_df["Token"] = pd.to_numeric(
            result_df["Token"],
            errors="coerce"
        )

        result_df = result_df[
            result_df["Token"].notna()
        ].copy()

        result_df["Token"] = (
            result_df["Token"]
            .astype(int)
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        result_df.to_csv(
            outputlist,
            mode="w",
            header=True,
            index=False
        )

        print()
        print(result_df)

        print(
            f"✅ Equity data saved to "
            f"'{outputlist}'"
        )

        # ----------------------------------------------------
        # AmiBroker import
        # ----------------------------------------------------

        if do_import.lower() == "yes":

            try:

                AB = win32com.client.Dispatch(
                    "Broker.Application"
                )

                AB.Import(
                    0,
                    outputlist,
                    "MasterInfo.format"
                )

                print(
                    "📥 Equity import completed"
                )

            except Exception as e:

                print(
                    f"❌ Import error: {str(e)}"
                )

    else:

        print(
            "⚠️ No equity symbols matched"
        )

# ============================================================
# OPTIONS / FUTURES TOKEN
# ============================================================

def options_token(
    input_sym=None,
    outputlist=None,
    df=None,
    exchange=None,
    market_id=None,
    group_id=None,
    option_expiry=None,
    future_expiry=None,
    strikemin=None,
    strikemax=None,
    future_suffix="-I",
    Futures="yes",
    Options="yes",
    datafeed="EST",
    do_import="no"
):

    print()
    print("=" * 70)
    print(f"{exchange} F&O")
    print("=" * 70)

    all_matched = []

    # ========================================================
    # DETERMINE SEGMENT
    # ========================================================

    if exchange == "NSE":

        # ----------------------------------------------------
        # NSE contains:
        #
        # NSE_FO  -> equity/index F&O
        # NCD_FO  -> currency F&O
        #
        # We initially search both.
        # ----------------------------------------------------

        fno_df = df[
            df["segment"].isin(
                [
                    "NSE_FO",
                    "NCD_FO"
                ]
            )
        ].copy()

    elif exchange == "BSE":

        fno_df = df[
            df["segment"] == "BSE_FO"
        ].copy()

    elif exchange == "MCX":

        fno_df = df[
            df["segment"] == "MCX_FO"
        ].copy()

    else:

        print(
            f"❌ Unsupported exchange: {exchange}"
        )

        return

    if fno_df.empty:

        print(
            f"❌ No F&O data found for {exchange}"
        )

        return

    # ========================================================
    # EXPIRY FORMAT
    # ========================================================

    fno_df["ExpiryDate"] = (
        fno_df["expiry"]
        .apply(format_expiry)
    )

    # ========================================================
    # PROCESS ONE SYMBOL
    # ========================================================

    def process_symbol(
        symbol,
        local_strikemin=None,
        local_strikemax=None
    ):

        matched = []

        # ====================================================
        # OPTIONS
        # ====================================================

        if (
            Options.lower() == "yes"
            and option_expiry
        ):

            df_filtered = fno_df[
                (fno_df["underlying_symbol"] == symbol) &
                (
                    fno_df["ExpiryDate"]
                    == option_expiry.upper()
                ) &
                (
                    fno_df["instrument_type"]
                    .isin(["CE", "PE"])
                )
            ].copy()

            # ------------------------------------------------
            # If no options
            # ------------------------------------------------

            if not df_filtered.empty:

                # ============================================
                # STRIKE DIFFERENCE
                # ============================================

                strikes = sorted(
                    pd.to_numeric(
                        df_filtered["strike_price"],
                        errors="coerce"
                    )
                    .dropna()
                    .unique()
                )

                diffs = [
                    round(
                        j - i,
                        2
                    )
                    for i, j in zip(
                        strikes[:-1],
                        strikes[1:]
                    )
                    if j > i
                ]

                diff_count = Counter(
                    diffs
                )

                strike_diff = (
                    diff_count
                    .most_common(1)[0][0]
                    if diff_count
                    else 0
                )

                strike_diff = format_number(
                    strike_diff
                )

                # ============================================
                # APPLY STRIKE RANGE
                # ============================================

                if (
                    local_strikemin is not None
                    and local_strikemax is not None
                ):

                    df_filtered = df_filtered[
                        (
                            df_filtered["strike_price"]
                            >= local_strikemin
                        )
                        &
                        (
                            df_filtered["strike_price"]
                            <= local_strikemax
                        )
                    ]

                # ============================================
                # CREATE OPTION ROWS
                # ============================================

                for _, row in df_filtered.iterrows():

                    output_symbol = (
                        format_custom_symbol(
                            symbol,
                            row["instrument_type"],
                            row["strike_price"]
                        )
                    )

                    # ----------------------------------------
                    # Upstox weekly
                    # ----------------------------------------

                    if "weekly" in row.index:

                        weekly_value = (
                            format_weekly(
                                row["weekly"]
                            )
                        )

                    else:

                        weekly_value = 0

                    matched.append([

                        row["exchange"],

                        output_symbol,

                        row["exchange_token"],

                        market_id,

                        group_id,

                        row["tick_size"],

                        row["instrument_key"],

                        row["lot_size"],

                        row["ExpiryDate"],

                        strike_diff,

                        weekly_value

                    ])

        # ====================================================
        # FUTURES
        # ====================================================

        if (
            Futures.lower() == "yes"
            and future_expiry
        ):

            future_df = fno_df[
                (fno_df["underlying_symbol"] == symbol) &
                (
                    fno_df["ExpiryDate"]
                    == future_expiry.upper()
                ) &
                (
                    fno_df["instrument_type"]
                    == "FUT"
                )
            ].copy()

            if not future_df.empty:

                # --------------------------------------------
                # Determine StrikeDiff from options
                # --------------------------------------------

                option_df = fno_df[
                    (fno_df["underlying_symbol"] == symbol) &
                    (
                        fno_df["ExpiryDate"]
                        == future_expiry.upper()
                    ) &
                    (
                        fno_df["instrument_type"]
                        .isin(["CE", "PE"])
                    )
                ]

                strikes = sorted(
                    pd.to_numeric(
                        option_df["strike_price"],
                        errors="coerce"
                    )
                    .dropna()
                    .unique()
                )

                diffs = [
                    round(
                        j - i,
                        2
                    )
                    for i, j in zip(
                        strikes[:-1],
                        strikes[1:]
                    )
                    if j > i
                ]

                diff_count = Counter(
                    diffs
                )

                strike_diff = (
                    diff_count
                    .most_common(1)[0][0]
                    if diff_count
                    else 0
                )

                strike_diff = format_number(
                    strike_diff
                )

                # --------------------------------------------
                # Future
                # --------------------------------------------

                row = future_df.iloc[0]

                output_symbol = (
                    format_custom_symbol(
                        symbol,
                        "FUT"
                    )
                )

                # --------------------------------------------
                # Futures are not weekly
                # --------------------------------------------

                matched.append([

                    row["exchange"],

                    output_symbol,

                    row["exchange_token"],

                    market_id,

                    group_id,

                    row["tick_size"],

                    row["instrument_key"],

                    row["lot_size"],

                    row["ExpiryDate"],

                    strike_diff,

                    0

                ])

        return matched

    # ========================================================
    # INPUT: LIST OR SINGLE SYMBOL
    # ========================================================

    if isinstance(input_sym, str):

        if os.path.exists(input_sym):

            # ------------------------------------------------
            # LIST
            #
            # Symbol,StrikeMin,StrikeMax
            # ------------------------------------------------

            input_df = pd.read_csv(
                input_sym,
                header=None,
                names=[
                    "Symbol",
                    "strikemin",
                    "strikemax"
                ]
            )

            for _, row in input_df.iterrows():

                symbol = (
                    str(row["Symbol"])
                    .strip()
                )

                local_strikemin = (
                    row["strikemin"]
                    if pd.notna(row["strikemin"])
                    else strikemin
                )

                local_strikemax = (
                    row["strikemax"]
                    if pd.notna(row["strikemax"])
                    else strikemax
                )

                matched = process_symbol(
                    symbol,
                    local_strikemin,
                    local_strikemax
                )

                all_matched.extend(
                    matched
                )

        else:

            # ------------------------------------------------
            # SINGLE SYMBOL
            #
            # Index / Currency / MCX etc.
            # ------------------------------------------------

            matched = process_symbol(
                input_sym,
                strikemin,
                strikemax
            )

            all_matched.extend(
                matched
            )

    else:

        print(
            "❌ Invalid input_sym."
        )

        return

    # ========================================================
    # SAVE RESULT
    # ========================================================

    if all_matched:

        result_df = pd.DataFrame(

            all_matched,

            columns=[
                "Exchange",
                "Symbol",
                "Token",
                "Market_ID",
                "Group_ID",
                "TickSize",
                "Instrument_Key",
                "LotSize",
                "Expiry",
                "StrikeDiff",
                "Weekly"
            ]
        )

        # ----------------------------------------------------
        # Numeric
        # ----------------------------------------------------

        result_df["Token"] = pd.to_numeric(
            result_df["Token"],
            errors="coerce"
        )

        result_df["LotSize"] = pd.to_numeric(
            result_df["LotSize"],
            errors="coerce"
        )

        result_df = result_df[
            result_df["Token"].notna()
        ].copy()

        result_df["Token"] = (
            result_df["Token"]
            .astype(int)
        )

        # ----------------------------------------------------
        # Remove duplicate token
        # ----------------------------------------------------

        result_df = result_df.drop_duplicates(
            subset=["Token"],
            keep="first"
        )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        result_df.to_csv(
            outputlist,
            mode="w",
            header=True,
            index=False
        )

        print()
        print(result_df)

        print()
        print(
            f"✅ F&O data saved to "
            f"'{outputlist}'"
        )

        # ----------------------------------------------------
        # AmiBroker
        # ----------------------------------------------------

        if do_import.lower() == "yes":

            try:

                AB = win32com.client.Dispatch(
                    "Broker.Application"
                )

                AB.Import(
                    0,
                    outputlist,
                    "MasterInfo.format"
                )

                print(
                    "📥 F&O import completed"
                )

            except Exception as e:

                print(
                    f"❌ Import error: {str(e)}"
                )

    else:

        print(
            "⚠️ No matching F&O data found."
        )


if group_id in [1,3]:
    equity_token(
        input_sym=input_sym,
        outputlist=outputlist,
        df=df,
        exchange=exchange,
        market_id=market_id,
        group_id=group_id,
        equity_suffix=equity_suffix,
        do_import=do_import
    )
    
else:
    options_token(
        input_sym=input_sym,
        outputlist=outputlist,
        df=df,
        exchange=exchange,
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
        do_import=do_import
    )
time.sleep(3)
