# Systematic Equity Trading System

A self-contained system that reads the US equity market daily, ranks a universe
of 50 large-cap stocks against each other each week, and trades a paper
portfolio of 10 names, with a full audit trail of every decision and fill.

Built from scratch starting August 2026. Runs unattended on a Linux server.

**This is a paper account. No real money is traded, and no claim is made that
the strategy is profitable.** See "What this does not claim" below.

---

## What it does

Every weekday evening:

1. **Fetch:** downloads the previous trading day's market file, which contains
   every US-listed ticker
2. **Settle:** fills any orders left pending from an earlier decision, at that
   morning's opening price, with transaction costs applied
3. **Decide:** on the first trading day of each week, ranks the universe and
   writes the resulting orders
4. **Report:** rebuilds the monitoring pages

Takes under a minute. Scheduled via cron; nobody has to be present.

## The strategy

**12-1 cross-sectional momentum.** Each stock is scored on its return from
twelve months ago to one month ago. The top ten are held, equal-weighted,
rebalanced weekly.

The construction is taken unchanged from Jegadeesh & Titman (1993) and is
**deliberately unfitted**: no parameter was selected by testing variants
against this data. The recent month is skipped because short-horizon returns
tend to reverse.

This is a placeholder chosen from published research, not a strategy derived
here. Replacing it changes one file.

## How lookahead bias is prevented

The decision and the execution are separated by file format, not by care:

- An order file **contains no price**. The component that decides is incapable
  of naming a price.
- Orders can only fill at the **open of a trading day strictly after** the date
  they were decided on. This is asserted on every fill; a violation halts the
  system rather than producing a number.
- Every fill is written to an **append-only ledger** that is never edited.
  Replaying the ledger from zero must reproduce the current portfolio exactly.

Carefulness fails silently and makes results look better. A structural
guarantee fails loudly or not at all.

## Measured facts

- **Turnover:** ~865%/yr one-way (1,729% two-way), measured from a four-month
  replay of the fill ledger
- **Modelled cost:** 1.38%/yr at 8bp per side, an assumption rather than a
  measurement against real fills
- Most of that turnover is position-size maintenance rather than signal
  rotation. A no-trade band is the obvious fix and is not yet implemented.

## What this does not claim

- **Not a validated edge.** The signal is credible published research, not
  something tested on this data.
- **Not a backtest.** Producing one honestly requires a point-in-time universe,
  an untouched holdout, and the discipline not to tweak and rerun. None of
  those are in place, so no performance figure is offered.
- **Not survivorship-bias-free.** The 50 companies were picked from today's
  large caps. That is harmless while trading forward and would be misleading in
  any claim about the past.
- **Dividends are not handled.** Price-only returns understate total return by
  roughly the dividend yield.

## Layout

```
fetch_raw.py        downloads daily market files
prices.py           the only module that reads prices; applies splits
strategy.py         12-1 momentum ranking
portfolio.py        account state, ledger, equity curve
make_orders.py      target vs held, writes orders (no prices)
settle.py           fills pending orders, marks to market
check_splits.py     flags one-day moves the splits table cannot explain
replay.py           runs the loop over history to test the state machine
build_dashboard.py  computes dashboard figures
news.py             SEC filings and newswire
app.py              Flask app: per-stock pages and /paper
universe.txt        the 50 tickers
KILL.md             stop conditions, written before it ran
scratch/            one-off tools from building it
```

## Running it

Requires Python 3.8+, a [Massive](https://massive.com) flat-files subscription,
and credentials in `.env` (see `.env.example`).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./refresh.sh
```

## How this was built

Built with AI assistance throughout, for both design and code. Every design
decision in it is one I can explain and defend, the data verification was done
by hand against issuer filings, and the bugs were found by reading the output
rather than trusting it.

---

*Not investment advice. A system that executes trades correctly will execute
bad decisions correctly.*


