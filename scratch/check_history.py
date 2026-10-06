"""FInd out how far back your Massive plan actually reaches."""
import os 
from datetime import date, timedelta

import boto3
from botocore.config import Config 
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()
s3 = boto3.Session(
    aws_access_key_id=os.getenv("MASSIVE_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("MASSIVE_SECRET_ACCESS_KEY"),
).client("s3", endpoint_url="https://files.massive.com",
         config=Config(signature_version="s3v4"))

today = date.today()
probes = {
    "2 years":  today - timedelta(days=365 * 2),
    "5 years":  today - timedelta(days=365 * 5 ),
    "10 years": today - timedelta(days=365 * 10),
    "15 years": today - timedelta(days=365 * 15),       
    "2003":     date(2003, 9, 10),
}

for label, d in probes.items():
    while d.weekday() >= 5:         # nudge back to a weekdays
        d -= timedelta(days=1)
    key = f"us_stocks_sip/day_aggs_v1/{d:%Y/%m/%Y-%m-%d}.csv.gz"
    try:
        s3.head_object(Bucket="flatfiles", Key=key)
        print(f"{label:9} {d} available")
    except ClientError as e:
        print(f"{label:9} {d} {e.response['Error']['Code']}")
                     