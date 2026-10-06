"""Decide. Turn the signal into orders and write them to a file, unfilled. 

Writes data/orders/<decided_on>.json with status "pending" and fill_date null.
It does NOT know when those orders will fill -- settle.py works that out from
the first trading day that appears after decided_on. That is the whole
lookahead defence: nothing here can name a price it decided on.
"""
import json
import sys
from math import floor
from pathlib import Path

import pandas as pd 

import portfolio
from config import load_universe
from prices import latest_close, trading_days
from strategy import N_HOLD, is_rebalance_day, target_names

ORDERS = Path("data/orders")
INVESTED = 0.98         # leave a little cash so an opening gap can't overdraw us


def order_path(as_of):
    return ORDERS / f"{pd.Timestamp(as_of).date()}.json"



def build_orders(state, targets, closes):
    """The difference between what we hold and what we want, as whole shares."""
    equity = state["cash"] + portfolio.market_value(state, closes)
    budget = equity * INVESTED / N_HOLD

    wanted = {t: floor(budget / closes[t]) for t in targets if closes.get(t, 0) > 0}
    held = {t: p["shares"] for t, p in state["positions"].items()}

    orders = []
    for ticker in sorted(set(held) | set(wanted)):
        delta = wanted.get(ticker, 0) - held.get(ticker, 0)
        if delta > 0:
            orders.append({"ticker": ticker, "side": "buy", "shares": delta})
        elif delta < 0:
            orders.append({"ticker": ticker, "side": "sell", "shares": -delta})
        # Sells first so the cash they raise is available to the buys 
    return sorted(orders, key=lambda o: o["side"] != "sell")


def main(as_of=None):
    ORDERS.mkdir(parents=True, exist_ok=True)
    days = trading_days(end=as_of)
    as_of = days[-1]

    if not is_rebalance_day(as_of, days):
        print(f"{as_of.date()}: not a rebalance day - no orders")
        return
    if order_path(as_of).exists():
        print(f"{as_of.date()}: orders already written - nothing to do")
        return                                      # idempotent: never decide twice

    state = portfolio.load()
    universe = load_universe()
    closes = latest_close(as_of, universe)
    targets = target_names(as_of, universe)
    if not targets:
        print(f"{as_of.date()}: no ticker has enough history yet - no orders")
        return

    orders = build_orders(state, targets, closes)
    payload = {
        "decided_on": str(as_of.date()),
        "decided_at": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fill_date": None,
        "status": "pending", 
        "targets": targets, 
        "orders": orders, 
    }   
    with order_path(as_of).open("w") as f:
        json.dump(payload, f, indent=2)

    n_buy = sum(1 for o in orders if o["side"] == "buy")
    print(f"{as_of.date()}: wrote {len(orders)} orders ({n_buy} buy, "
          f"{len(orders) - n_buy} sell) -> {order_path(as_of)}")
                                            

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
    

