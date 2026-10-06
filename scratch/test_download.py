import os, boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()
s3 = boto3.Session(
    aws_access_key_id=os.getenv("MASSIVE_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("MASSIVE_SECRET_ACCESS_KEY"),
).client("s3", endpoint_url="https://files.massive.com",
    config=Config(signature_version="s3v4"))

key = "us_stocks_sip/day_aggs_v1/2026/07/2026-07-01.csv.gz"
s3.download_file("flatfiles", key, "data/tes.csv.gz")
print("Downloaded OK")