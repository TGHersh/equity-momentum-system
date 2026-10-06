"""Run the whole loop over past dates, one day at a time, to test the machine. 

This is NOT a backtest and its equity curve is not evidence of anything. The
universe was chosen with hindsight and the costs are a guess. What it proves is
that the state machine works: orders get writte, sit pending, fill on a later 
day at a price nobody knew, and the account adds up. 

    python3 replay.py 2026-06-01
"""
import shutil 
import sys 
from pathlib import Path 

import pandas as pd 

import make_orders
import portfolio
import settle
from prices import trading_days


def main(start):
    if input(f"reset the paper account and replay from {start}? [y/N]").lower() != "y":
        return 
    shutil.rmtree(make_orders.ORDERS, ignore_errors=True)
    portfolio.reset()

    days = trading_days()
    days = days[days >= pd.Timestamp(start)]
    print(f"replaying {len(days)} trading days\n")

    for day in days:
        settle.main(day)        # settle first: know what you hold before deciding 
        make_orders.main(day)    # then decide
        print()

    eq = pd.read_csv(portfolio.EQUITY)
    first, last = eq["equity"].iloc[0], eq["equity"].iloc[-1]
    peak = eq["equity"].cummax()
    print("=" * 60)
    print(f"days replayed      {len(eq)}")
    print(f"equity             {first:,.0f} -> {last:,.0f} ({last / first - 1:+.1%})")
    print(f"max drawdown       {(eq['equity'] / peak - 1).min():.1%}")
    print(f"fills              {len(pd.read_csv(portfolio.LEDGER))}")
    print(f"orders written     {len(list(Path(make_orders.ORDERS).glob('*.json')))}")
    print("\nThis is a test of plumbing. It is not evidence of an edge.")


if __name__=="__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-01-02")
