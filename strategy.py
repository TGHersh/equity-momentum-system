"""The trading rule: 12-1 momentum, cross-sectionally ranked.

For each stock, the return from 12 months ago to 1 month ago. The most recent
month is deliberately skipped -- short-horizon returns tend to REVERSE, so 
including them fights the signal. This is the standard construction from the 
academic literature (Jegadeesh & Titman, 1993), used here unchanged.

Nothing here is fitted. No parameter was chosen by looking at my data, so
there is nothing to overfit and nothing to validate.
"""

import pandas as pd

from config import load_universe
from prices import load_prices, trading_days

LOOKBACK = 252         # trading days ~ 12 months
SKIP = 21              # trading days ~ 1 month, dropped from end
N_HOLD = 10            # how many names to hold


def momentum(as_of, tickers=None):
    """Series of 12-1 momentum per ticker, using only data up to as_of."""
    tickers = tickers or load_universe()
    start = pd.Timestamp(as_of) - pd.Timedelta(days=550)
    df = load_prices(tickers, start=start, end=as_of)

    scores = {}
    for ticker, g  in df.groupby("ticker"):
        closes = g["close"].to_numpy()
        if len(closes) < LOOKBACK + 1:
            continue                                        # not enough history yet
        p_recent = closes[-(SKIP + 1)]                      # 21 trading days ago
        p_old = closes[-(LOOKBACK + 1)]                     # 252 trading days ago
        if p_old > 0:
            scores[ticker] = p_recent / p_old - 1
    return pd.Series(scores, dtype="float64").sort_values(ascending=False)



def target_names(as_of, tickers=None):
    """The N_HOLD tickers to hold as of that date."""
    return list(momentum(as_of, tickers).head(N_HOLD).index)


def is_rebalance_day(as_of, days=None):
    """True on the first trading day of an ISO week -- normally Monday, and
    the Tuesday after a Monday holiday, without needing a holiday calendar."""
    as_of = pd.Timestamp(as_of)
    days = trading_days(end=as_of) if days is None else days
    week = [d for d in days if d.isocalendar()[:2] == as_of.isocalendar()[:2]]
    return bool(week) and week[0] == as_of



if __name__ == "__main__":
    days = trading_days()
    as_of = days[-1]
    m = momentum(as_of)
    print(f"as of {as_of.date()} - {len(m)} tickers scored, "
          f"rebalance day: {is_rebalance_day(as_of, days)}")
    print("\nHOLD:")
    for t, v in m.head(N_HOLD).items():
        print(f"  {t:6} {v:+7.1%}")
    print("\nbottom 3 for contrast:")
    for t, v in m.tail(3).items():
        print(f"  {t:6} {v:+7.1%}")
