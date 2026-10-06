"""Resolve tickers to SEC CIK numbers."""
import os 
from dotenv import load_dotenv
import json
import urllib.request

load_dotenv()
AGENT = os.getenv("SEC_USER_AGENT")
if not AGENT:
    raise SystemExit("SEC_USER_AGENT is not set in .env — the SEC requires a contact address")
    
WANT = {"NKE", "DECK", "ONON", "UAA", "SKX"}

req = urllib.request.Request(
    "https://www.sec.gov/files/company_tickers.json",
    headers={"User-Agent": AGENT},
)
data= json.load(urllib.request.urlopen(req))

for row in data.values():
    if row["ticker"] in WANT:
        print(f'{row["ticker"]:6} {row["cik_str"]:010d} {row["title"]}')

