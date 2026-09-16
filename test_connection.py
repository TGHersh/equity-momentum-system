import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()     # reads .env into environment

session = boto3.Session(
    aws_access_key_id=os.getenv("MASSIVE_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("MASSIVE_SECRET_ACCESS_KEY")
)

s3 = session.client(
    "s3",
    endpoint_url="https://files.massive.com",
    config=Config(signature_version="s3v4"),

)

response = s3.list_objects_v2(
    Bucket="flatfiles",
    Prefix="us_stocks_sip/day_aggs_v1/2026/07/",
    MaxKeys=5,

)

for obj in response.get("Contents", []):
    print(obj["Key"], round(obj["Size"] / 1024), "KB")

