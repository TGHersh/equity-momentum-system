"""Test candidate news feeds before adding them."""
import os 
from dotenv import load_dotenv
import feedparser

load_dotenv()
AGENT = os.getenv("SEC_USER_AGENT")

CANDIDATES = [
    ("CNBC markets", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("MarketWatch",  "https://www.marketwatch.com/rss/marketwatch.gif"),
] # MarketWatch url probably wrong.

for label, url in CANDIDATES:
    feed = feedparser.parse(url, agent=AGENT)
    print(f"\n{label}: {len(feed.entries)} entries")
    for e in feed.entries[:3]:
        print("  ", e.get("title", "(none)")[:70])


