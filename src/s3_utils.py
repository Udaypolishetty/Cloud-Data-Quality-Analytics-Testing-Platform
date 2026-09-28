import sys
from datetime import date

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

BUCKET_NAME = "uday-dq-platform-raw-2026"
REGION = "ap-south-1"

s3 = boto3.client("s3", region_name=REGION)


def _today():
    return date.today().isoformat()


def upload_file(local_path, key):
    s3.upload_file(local_path, BUCKET_NAME, key)
    print(f"Uploaded {local_path} -> s3://{BUCKET_NAME}/{key}")


def download_file(key, local_path):
    s3.download_file(BUCKET_NAME, key, local_path)
    print(f"Downloaded s3://{BUCKET_NAME}/{key} -> {local_path}")


def list_keys(prefix):
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix):
        keys += [obj["Key"] for obj in page.get("Contents", [])]
    return keys


def upload_raw():
    upload_file("data/orders_source.csv", f"raw/orders/date={_today()}/orders_source.csv")


def download_latest_raw(local_path):
    keys = list_keys("raw/orders/")
    if not keys:
        raise SystemExit("No raw files in S3. Run: python src/s3_utils.py upload-raw")
    latest = max(keys)  # date=YYYY-MM-DD sorts correctly as text
    download_file(latest, local_path)
    return latest


def upload_results():
    for name in ["failed_records.csv", "orders_valid.csv", "validation_summary.csv"]:
        upload_file(f"data/{name}", f"results/date={_today()}/{name}")


COMMANDS = {
    "upload-raw": upload_raw,
    "upload-results": upload_results,
    "list": lambda: print("\n".join(list_keys(""))),
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        raise SystemExit(f"Usage: python src/s3_utils.py [{' | '.join(COMMANDS)}]")
    try:
        COMMANDS[sys.argv[1]]()
    except NoCredentialsError:
        raise SystemExit("AWS credentials not found. Run 'aws configure' first.")
    except ClientError as e:
        raise SystemExit(f"AWS error: {e}")