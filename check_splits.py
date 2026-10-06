"""Flag any one-day move the splits table doesn't explain.

Runs on ADJUSTED prices, so a split already recorded in data/splits.csv
disappears. What's left is either genuine news or a split nobody has told
me about yet -- and the arithmetic usually says which. 
"""
import pandas as pd

from config import load_universe
from prices import load_prices

THRESHOLD = 0.25       # a one-day move beyond this is a question
WINDOW = 550           # the window the signal actually looks at 

def split_hint(chg):
    """A -90% day is what a 10-for-1 split looks like. If the implied ratio
    is close to a whole number, say so."""
    implied = 1 / (1 + chg)
    for ratio, label in ((implied, "{n}-for-1 split"),
                        (1 / implied, "1-for-{n} reverse split")):
        n = round(ratio)
        if n >= 2 and abs(ratio - n) / n < 0.04:
            return " <- looks like a " + label.format(n=n)
    return " (no round ratio - probably news)"

def main():
    df = load_prices(load_universe())
    df = df[df["date"] >= df["date"].max() - pd.Timedelta(days=WINDOW)]
    df["chg"] = df.groupby("ticker")["close"].pct_change()
    hits = df[df["chg"].abs() > THRESHOLD]

    if hits.empty:
        print("splits check: no unexplained moves")
        return 

    print(f"splits check: {len(hits)} move(s) beyond {THRESHOLD:.0%}")
    for r in hits.itertuples():
        print(f"    {r.date.date()} {r.ticker:6} {r.chg:+.1%}{split_hint(r.chg)}")


if __name__=="__main__":
    main()


