"""The paper account's state, and the only code that changes it.

data/portfolio.json   cash, positions, the date it is current to 
data/ledger.csv       every fill that has ever happened
data/equity.csv       one row per day: cash, positions value, total
"""
import csv
import json
from pathlib import Path

STATE = Path("data/portfolio.json")
LEDGER = Path("data/ledger.csv")
EQUITY = Path("data/equity.csv")

START_CASH = 100_000.0

LEDGER_COLUMNS = ["date", "ticker", "side", "shares", "price", "gross", "cash_after"]
EQUITY_COLUMNS = ["date", "cash", "positions_value", "equity"]


def fresh():
    return {"as_of": None, "cash": START_CASH, "positions": {}}


def load():
    if not STATE.exists():
        return fresh()
    with STATE.open() as f:
        return json.load(f)


def save(state):
    STATE.parent.mkdir(exist_ok=True)
    with STATE.open("w") as f:
        json.dump(state, f, indent=2)


def reset():
    """Start the paper account over. Used by replay.py and nothing else."""
    for p in (LEDGER, EQUITY):
        p.unlink(missing_ok=True)
    save(fresh())


def buy(state, ticker, shares, price):
    """Add shares at price, updating the average cost."""
    pos = state["positions"].get(ticker, {"shares": 0, "avg_price": 0.0})
    total = pos["shares"] + shares
    pos["avg_price"] = (pos["shares"] * pos["avg_price"] + shares * price) / total
    pos["shares"] = total
    state["positions"][ticker] = pos
    state["cash"] -= shares * price


def sell(state, ticker, shares, price):
    """Remove shares at price. Average cost is unchanged by a sale."""
    pos = state["positions"][ticker]
    pos["shares"] -= shares
    state["cash"] += shares * price
    if pos["shares"] <= 0:
        del state["positions"][ticker]


def append_ledger(rows):
    LEDGER.parent.mkdir(exist_ok=True)
    new = not LEDGER.exists()
    with LEDGER.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS)
        if new:
            w.writeheader()
        w.writerows(rows)


def append_equity(date, cash, positions_value):
    EQUITY.parent.mkdir(exist_ok=True)
    new = not EQUITY.exists()
    with EQUITY.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=EQUITY_COLUMNS)
        if new:
            w.writeheader()
        w.writerow({"date": date, "cash": round(cash, 2),
                    "positions_value": round(positions_value, 2),
                    "equity": round(cash + positions_value, 2)})


def market_value(state, closes):
    """What the positions are worth at the given {ticker: close}."""
    return sum(p["shares"] * closes[t] for t, p in state["positions"].items() if t in closes)



