"""Bring the paper account up to date: fill what can be filled, then mark to market.

A pending order is filled at the OPEN of the first trading day strictly after
the date it was decided on. That single rule is the difference between a paper
trade and a fantasy: the price we transact at could not have been known when
we decided.
"""
import json
import sys
from math import floor
from pathlib import Path

import pandas as pd 

import portfolio
from config import load_universe
from prices import latest_close, opens_on, trading_days

ORDERS = Path("data/orders")
COST_BPS = 8            # spread + comission + slippage, per side


def fill_price(price, side):
    """Costs modelled as slippage: you buy a little above and sell a little below."""
    slip = COST_BPS / 10_000
    return price * (1 + slip) if side == "buy" else price * (1 - slip)


def pending_files():
    out = []
    for p in sorted(ORDERS.glob("*.json")):
        with p.open() as f:
            payload = json.load(f)
        if payload.get("status") == "pending":
            out.append((p, payload))
    return out


def fill_date_for(decided_on, days):
    """The first trading day strictly after the decision. None if it hasn't come."""
    later = days[days > pd.Timestamp(decided_on)]
    return later[0] if len(later) else None


def settle_one(path, payload, days, state):
    decided_on = pd.Timestamp(payload["decided_on"])
    day = fill_date_for(decided_on, days)
    if day is None:
        print(f" {path.name}: no trading after {decided_on.date()} yet - still pending")
        return False

    assert day > decided_on, "fill date must be strictly after the decision date"

    tickers = [o["ticker"] for o in payload["orders"]]
    opens = opens_on(day, tickers)
    rows, short = [], []

    for o in payload["orders"]:
        raw = opens.get(o["ticker"])
        if raw is None:
            short.append(f"{o['ticker']} did not trade")
            continue
        px = fill_price(float(raw), o["side"])
        shares = o["shares"]

        if o["side"] == "buy":
            affordable = floor(state["cash"] / px)
            if affordable < shares:
                short.append(f"{o['ticker']} {shares}->{max(affordable, 0)} (cash)")
                shares = max(affordable, 0)
            if shares == 0:
                continue
            portfolio.buy(state, o["ticker"], shares, px)
        else:
            held = state["positions"].get(o["ticker"], {}).get("shares", 0)
            shares = min(shares, held)
            if shares == 0:
                continue
            portfolio.sell(state, o["ticker"], shares, px)

        rows.append({"date": str(day.date()), "ticker": o["ticker"], "side": o["side"],
                     "shares": shares, "price": round(px, 4),
                     "gross": round(shares * px, 2), "cash_after": round(state["cash"], 2)})

    portfolio.append_ledger(rows)
    payload["status"] = "filled"
    payload["fill_date"] = str(day.date())
    payload["shortfall"] = short
    with path.open("w") as f:
        json.dump(payload, f, indent=2)

    print(f" {path.name}: filled {len(rows)} orders at {day.date()} open"
          + (f" - shortfall: {';'.join(short)}" if short else ""))
    return True


def main(as_of=None):
    days = trading_days(end=as_of)
    as_of = days[-1]
    state = portfolio.load()

    print(f"settling as of {as_of.date()}")
    for path, payload in pending_files():
        settle_one(path, payload, days, state)

    assert state["cash"] >= -0.01, f"cash went negative: {state['cash']}"

    closes = latest_close(as_of, load_universe() + list(state["positions"]))
    value = portfolio.market_value(state, closes)

    today = str(as_of.date())
    if state ["as_of"] is None or today > state["as_of"]:  # forward only, once per day
        portfolio.append_equity(today, state["cash"], value)
        state["as_of"] = today
    portfolio.save(state)

    print(f" cash {state['cash']:,.0f} + positions {value:,.0f} = "
          f"equity {state['cash'] + value:,.0f} across {len(state['positions'])} names")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)




    