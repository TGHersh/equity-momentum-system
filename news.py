"""Fetch RSS feeds, keep what's relevant, write data/news.json."""
import os 
from dotenv import load_dotenv
import json
import re
from datetime import datetime, timezone
import feedparser
import urllib.request

load_dotenv()
AGENT = os.getenv("SEC_USER_AGENT")
if not AGENT:
    raise SystemExit("SEC_USER_AGENT is not set in .env — the SEC requires a contact address")

SUBJECT = "NKE"

ITEM_LABELS = {
    "1.01": "Material agreement entered", "1.02": "Material agreement terminated",
    "2.01": "Acquisition or disposal completed", "2.02": "Results of operations (earnings)",
    "2.05": "Restructuring / exit costs",   "2.06": "Material impairment",
    "3.01": "Listing or delisting notice",  "5.02": "Executive or director change",
    "5.07": "Shareholder vote results",     "7.01": "Regulation FD disclosure",
    "8.01": "Other events",                 "9.01": "Financial statements and exhibits",
}

FORM_LABELS = {
    "8-K": "Current report",        "10-K": "Annual report",
    "10-Q": "Quarterly report",     "6-K": "Foreign issuer report",
    "20-F": "Annual report (foreign issuer)", "DEF 14A": "Proxy statement"
}

# Administrative items that ride along with the real news
BORING = {"Financial statements and exhibits", "Regualtion FD disclosure"}


def describe(form, items):
    """'8-K', '2.02,9.01' -> '8-K' - Results of operations'"""
    codes = [c.strip() for c in (items or "").split(",") if c.strip()]
    labels = [ITEM_LABELS.get(c, f"Item {c}") for c in codes]

    meaningful = [l for l in labels if l not in BORING]
    if meaningful:
        return f"{form} - {'; '.join(meaningful)}"
    if labels:
        return f"{form} - {'; '.join(labels)}"
    return f"{form} - {FORM_LABELS.get(form, 'Filing')}"

def filing_url(cik, accession):
    """Build the human-readable EDGAR page for one filing."""
    plain = accession.replace("-", "")
    return (f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{plain}/"
            f"{accession}-index.htm")

def sec_filings(label, cik, forms=("8-K", "6-K"), limit=8):
    """Recent filings for one company, as dashboard items."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    req = urllib.request.Request(url, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.load(resp)
    
    recent = data["filings"]["recent"]
    n = len(recent["form"])
    items_col = recent.get("items", [""] * n)           # not every response has it 
    
    out = []
    for i in range(n):
        if recent["form"][i] not in forms:
            continue
        out.append({
            "source": label,
            "title": describe(recent["form"][i], items_col[i]),
            "link": filing_url(cik, recent["accessionNumber"][i]),
            "ts": recent["filingDate"][i],
            "when": recent["filingDate"][i],
        })
        if len(out) >= limit:
            break
    return out



def edgar(cik, form, count=10):
    """Build an EDGAR Atom feed URL for one company's filings of one type."""
    return("https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
            f"&CIK={cik}&type={form}&count={count}&output=atom")
COMPANIES = [
    ("Nike filings",    "0000320187"),
    ("Deckers filings", "0000910521"),    #Hoka
    ("On Holding",      "0001858985"),    # foreign issuer: 6-K
]

RSS_FEEDS = [
   # ("CNBC markets", "https://www.cnbc.com/id/100003114/device/rss/rss.html", False),
   # Dropped Oct 2026. The keyword filter was built for a discretionary thesis
   # about one company; a rule-based strategy doesn't consume headlines, so it 
   # matched 0 of 30 every run. SEC filings stay - those are company-specific.
]

KEYWORDS = ["nike", "nke", "jordan brand", "converse",
    "footwear", "sneaker", "trainer", "athleisure", "activewear",
    "on holding", "onon", "hoka", "deckers", "adidas",
    "under armour", "lululemon", "new balance", "asics", "puma",]


PATTERNS = [re.compile(rf"\b{re.escape(k)}\b") for k in KEYWORDS]

MAX_ITEMS = 12


def relevant(entry, always_keep):
    """Feeds we subscribed to on purpose keep everything.
    General newswires have to match a keyword."""
    if always_keep:
        return True
    text = f"{entry.get('title', '')} {entry.get('summary', '')}".lower()
    return any(p.search(text) for p in PATTERNS)
    

def when(entry):
    t = entry.get("published_parsed") or entry.get("updated_parsed")
    if not t:
        return None
    return datetime(*t[:6], tzinfo=timezone.utc)



def main():
    items = []

    for label, cik in COMPANIES:
        try:
            items.extend(sec_filings(label, cik))
            print(f" {label}: ok")
        except Exception as e:
            print(f"  ! {label}: {e}")
            
    for source, url, always_keep in RSS_FEEDS:
        try:
            feed = feedparser.parse(url, agent=AGENT)
        except Exception as e:
            print(f"  ! {source}: {e}")
            continue
        kept = 0 
        for entry in feed.entries:
            if not relevant(entry, always_keep):
                continue
            ts = when(entry)
            items.append({
                "source": source,
                "title": entry.get("title", "(untitled)").strip(),
                "link": entry.get("link", ""),
                "ts": ts.isoformat() if ts else None,
                "when": ts.strftime("%d %b %H:%M") if ts else "",
            })
            kept += 1
        print(f"  {source}: {kept} kept of {len(feed.entries)}")
    
    items.sort(key=lambda i: i["ts"] or "", reverse=True)
    payload = {
        "fetched_at": datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC"),
        "ticker": SUBJECT,
        "items": items[:MAX_ITEMS],
    }
    with open("data/news.json", "w") as f:
        json.dump(payload, f, indent=2)
    print(f"wrote data/news.json - {len(payload['items'])} items")

if __name__ == "__main__":

    main()



            
        
