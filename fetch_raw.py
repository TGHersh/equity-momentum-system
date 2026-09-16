import os
from datetime import date, timedelta

import boto3
import pandas as pd 
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from config import all_tickers, load_tickers


TICKERS = [
    "NKE",                                      # the subject
    "SPY", "XLY", "XRT",                        # benchmarks
    "XLK", "XLF", "XLV", "XLC", "XLI",          # sectors
    "XLP", "XLE", "XLU", "XLRE", "XLB",
    "UUP", "USO", "IEF", "GLD",                # macro & commodities
 ]
# Whatever tickers.json asks for plus their sector ETFs, on top of the context list.
TICKERS = sorted(set(TICKERS) | set(all_tickers(load_tickers())))

END_DATE = date.today() - timedelta(days=2)  # 2-day buffer
START_DATE = END_DATE - timedelta(days=365 * 5 - 10)


load_dotenv()
s3 = boto3.Session(
    aws_access_key_id=os.getenv("MASSIVE_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("MASSIVE_SECRET_ACCESS_KEY"),
).client("s3", endpoint_url="https://files.massive.com",
         config=Config(signature_version="s3v4"))


os.makedirs("data/raw", exist_ok=True)
rows, missing = [], 0
current = START_DATE


while current <= END_DATE:
    if current.weekday() < 5:
        key = f"us_stocks_sip/day_aggs_v1/{current:%Y/%m/%Y-%m-%d}.csv.gz"
        local = f"data/raw/{current}.csv.gz"

        if not os.path.exists(local):
            try:
                s3.download_file("flatfiles", key, local)
            except ClientError:
                missing += 1 
                current += timedelta(days=1)
                continue
            
        day = pd.read_csv(local)
        match = day[day["ticker"].isin(TICKERS)]
        if not match.empty:
            rows.append(match)
        print(f"{current} ok", end="\r")
    
    current += timedelta(days=1)


print(f"\nCollected {len(rows)} rows · {missing} files unavailable") #remove line once have s3 access keys



df = pd.concat(rows, ignore_index=True)
df["date"] = pd.to_datetime(df["window_start"], unit="ns").dt.date
df = df[["date", "ticker", "open", "high", "low", "close", "volume", "transactions"]]
df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
df.to_csv(f"data/prices_daily.csv", index=False)

print(f"\n{len(df)} rows across {df['ticker'].nunique()} tickers - {missing} files unavailable")
print(f"{df['date'].min()} → {df['date'].max()}")
print(df.tail())