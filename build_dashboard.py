"""Turn data/prices_daily.csv into data/dashboard.json - every number the page needs.
Runs on a schedule, not on request. The web app only reads the result.
"""

import json 
from datetime import date, datetime, timezone

import pandas as pd

from config import load_tickers

MARKET = "SPY"         # every subject is compared to this

SECTORS = {
    "XLK": "Technology",      "XLF": "Financials",     "XLV": "Health care",
    "XLY": "Cons. disc.",     "XLC": "Comms",          "XLI": "Industrials",
    "XLP": "Cons. staples",   "XLE": "Energy",         "XLU": "Utilities",
    "XLRE": "Real estate",    "XLB": "Materials",
}
MACRO = {
    "UUP": "US dollar", "USO": "Oil", "XRT": "Retail", 
    "IEF": "Treasuries (7-10y)", "GLD": "Gold",
}


SPLITS = {
    "XLK": [("2025-12-05", 2)],
    "XLY": [("2025-12-05", 2)],
    "XLE": [("2025-12-05", 2)],
    "XLU": [("2025-12-05", 2)],
    "XLB": [("2025-12-05", 2)],
}
CHART_DAYS = 120

def load():
    df = pd.read_csv("data/prices_daily.csv", parse_dates=["date"])
    df = df.sort_values(["ticker", "date"])
    for tkr, events in SPLITS.items():
        for eff, ratio in events:
            earlier = (df["ticker"] == tkr) & (df["date"] < pd.Timestamp(eff))
            df.loc[earlier, ["open", "high", "low", "close"]] /= ratio
            df.loc[earlier, "volume"] *= ratio
    return df

def pct(new, old):
    return None if old in (0, None) else (new / old - 1) * 100


def series(df, ticker):
    return df[df["ticker"] == ticker].reset_index(drop=True)


def change_over(s, days):
    """Percentage change over the last N trading rows"""
    if len(s) <= days:
        return None
    return pct(s["close"].iloc[-1], s["close"].iloc[-1 - days])


def build_subject(df, ticker, cfg):
    """One dashboard block for one ticker. cfg is its record tickers.json"""
    s = series(df, ticker)
    last = s.iloc[-1]
    year = s[s["date"] >= s["date"].max() - pd.Timedelta(days=365)]
    hi, lo = year["close"].max(), year["close"].min()
    avg_vol = s["volume"].tail(20).mean()

    nxt = date.fromisoformat(cfg["next_earnings"]) if cfg.get("next_earnings") else None

    return {
        "ticker": ticker, 
        "name": cfg["name"],
        "sector_etf": cfg["sector_etf"], 
        "price": round(float(last["close"]), 2),
        "as_of": last["date"].strftime("%d %b %Y"),
        "chg_1d": change_over(s, 1),
        "chg_1m": change_over(s, 21),
        "chg_all": pct(float(last["close"]), float(s["close"].iloc[0])),
        "high_52w": round(float(hi), 2),
        "low_52w": round(float(lo), 2),
        "range_pos": float((last["close"] - lo) / (hi - lo) * 100) if hi > lo else None,
        "off_high": pct(float(last["close"]), float(hi)),
        "above_low": pct(float(last["close"]), float(lo)),
        "vol_vs_avg": pct(float(last["volume"]), float(avg_vol)),
        "days_to_earnings": (nxt - last["date"].date()).days if nxt else None,
        "earnings_date": nxt.strftime("%d %b %Y") if nxt else None,
        "relative": build_relative(df, [ticker, MARKET, cfg["sector_etf"]]),
    }
   


def build_relative(df, tickers):
    """Each ticker over the last CHART_DAYS, rebased to 100 at the start of that
    window so the chart and its labels describe the same thing."""
    out = []
    for t in tickers:
        s = series(df, t).tail(CHART_DAYS)
        if s.empty:
            continue
        base = float(s["close"].iloc[0])
        rebased = [round(float(c) / base * 100, 2) for c in s["close"]]
        out.append({"ticker": t, "indexed": rebased[-1], "spark": rebased})
    return out


def build_rows(df, mapping):
    rows = []
    for tkr, label in mapping.items():
        s = series(df, tkr)
        if len(s) < 2:
            continue
        rows.append({
            "ticker": tkr, "label": label,
            "price": round(float(s["close"].iloc[-1]), 2),
            "chg_1d": change_over(s, 1),
            "chg_1m": change_over(s, 21),
        })
    return sorted(rows, key=lambda r: (r["chg_1d"] is None, -(r["chg_1d"] or 0)))



def realised_vol(df, ticker="SPY", window=20):
    s = series(df, ticker)
    if len(s) < window + 1:
        return None
    daily = s["close"].pct_change().tail(window)
    return float(daily.std() * (252 ** 0.5) * 100)



def main():
    df = load()
    cfg = load_tickers()
    have = set(df["ticker"])

    subjects = {}
    for ticker, record in cfg.items():
        if ticker not in have:
            print(f" ! {ticker} is in tickers.json but no in the price data - run fetch first")
            continue
        subjects[ticker] = build_subject(df, ticker, record)

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC"),
        "data_through": df["date"].max().strftime("%d %b %Y"),
        "tickers": list(subjects),
        "subjects": subjects, 
        "sectors": build_rows(df, SECTORS),
        "macro": build_rows(df, MACRO),
        "spy_vol_20d": realised_vol(df),
    }
    with open("data/dashboard.json", "w") as f:
        json.dump(payload, f, indent=2)
    print(f"wrote data/dashboard.json - {len(subjects)} tickers, data through {payload['data_through']}")

if __name__ == "__main__":
    main()

   
