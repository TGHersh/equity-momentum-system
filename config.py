"""The one place that knows which tickers the dashboard is about.

Every script imports load_tickers() from here rather than reading the file itself, 
so the filename and format are decide exactly once.
"""
import json
from pathlib import Path

UNIVERSE_FILE = Path(__file__).with_name("universe.txt")

def load_universe():
    """The stocks the strategy trades. One ticker per line; # comments ignored"""
    with UNIVERSE_FILE.open() as f:
        return [ln.strip().upper() for ln in f
                if ln.strip() and not ln.startswith("#")]

TICKERS_FILE = Path(__file__).with_name("tickers.json")

def load_tickers():
    """Return the config as a dict: {"NKE": {...}, "AAPL": {...}}.
    Insertion order is preserved, so the first entry is the default page."""
    with TICKERS_FILE.open() as f:
        return json.load(f)


def all_tickers(cfg):
    """Every symbol anything needs: dashboard subjects, their sector ETFs, the universe."""
    return sorted(set(cfg) | {c["sector_etf"] for c in cfg.values()} | set(load_universe()))

