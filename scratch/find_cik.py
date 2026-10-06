"""Resolve tickers to SEC CIK numbers."""
import json
import urllib.request

AGENT = "Turner Dashboard turnerhershey1@gmail.com"
WANT = {"NKE", "DECK", "ONON", "UAA", "SKX"}

req = urllib.request.Request(
    "https://www.sec.gov/files/company_tickers.json",
    headers={"User-Agent": AGENT},
)
data= json.load(urllib.request.urlopen(req))

for row in data.values():
    if row["ticker"] in WANT:
        print(f'{row["ticker"]:6} {row["cik_str"]:010d} {row["title"]}')

