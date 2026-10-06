"""Read prices. The only module that knows where they live.

Sprint version: reads data/prices_daily.csv and applies data/splits.csv on read.
Phase B replaces the inside of load_prices() with a parquet store. The signature
does not change, so nothing that calls it needs to.
"""
from pathlib import Path

import pandas as pd 

STORE = Path("data/prices_daily.csv")
SPLITS = Path("data/splits.csv")
CALENDAR_TICKER = "SPY"         # whose dates define "a trading day"


def load_splits():
    """ticker, date, ratio. Ratio 4 means 4-for-1; 0.1 a 1-for-10 reverse split."""
    if not SPLITS.exists():
        return pd.DataFrame(columns=["ticker", "date", "ratio"])
    return pd.read_csv(SPLITS, parse_dates=["date"])


def adjust(df):
    """Put every price on today's share basis: rows BEFORE a split are divided
    by its ratio. Two splits both apply to the oldest rows, which is what
    cumulative means."""
    splits = load_splits()
    splits = splits[splits["ticker"].isin(df["ticker"].unique())]
    tickers = df["ticker"].values
    for row in splits.itertuples():
        earlier = (tickers == row.ticker) & (df["date"] < row.date).values
        df.loc[earlier, ["open", "high", "low", "close"]] /= row.ratio
        df.loc[earlier, "volume"] = (df.loc[earlier, "volume"] * row.ratio).round().astype("int64")
    return df


def load_prices(tickers=None, start=None, end=None, adjusted=True):
    """Rows for the given tickers (all if None), between start and end inclusive.

    `end` is the as-of date: nothing after it is returned. Every script in the 
    loop passes it, which is what makes the whole thing replayable.
    """
    if not STORE.exists():
        raise FileNotFoundError(f"{STORE} not found - run fetch_raw.py")
    df = pd.read_csv(STORE, parse_dates=["date"])
    if tickers is not None:
        df = df[df["ticker"].isin(list(tickers))]
    if start is not None:
        df = df[df["date"] >= pd.Timestamp(start)]
    if end is not None:
        df = df[df["date"] <= pd.Timestamp(end)]
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    return adjust(df) if adjusted else df

def trading_days(end=None):
    """The market calendar as the store saw it: every date SPY has a row for."""
    spy = load_prices([CALENDAR_TICKER], end=end, adjusted=False)
    if spy.empty:
        raise ValueError(f"no {CALENDAR_TICKER} rows - the calendar ticker must be in the store")
    return pd.DatetimeIndex(sorted(spy["date"].unique()))


def latest_close(as_of, tickers):
    """{ticker: close} on the last day at or before as_of that each one traded."""
    df = load_prices(tickers, end=as_of)
    return df.groupby("ticker")["close"].last().to_dict()


def opens_on(day, tickers):
    """{ticker: open} for exactly that date. Missing tickers are simply absent."""
    df = load_prices(tickers, start=day, end=day)
    return df.set_index("ticker")["open"].to_dict()


