import json
import os
import time
import boto3

s3 = boto3.client("s3")
ddb = boto3.client("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]


def compute_bucket_size_and_count(bucket_name: str):
    paginator = s3.get_paginator("list_objects_v2")
    total_size = 0
    total_count = 0

    for page in paginator.paginate(Bucket=bucket_name):
        contents = page.get("Contents", [])
        total_count += len(contents)
        for obj in contents:
            total_size += obj.get("Size", 0)

    return total_size, total_count


def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    for record in event.get("Records", []):
        bucket_name = record["s3"]["bucket"]["name"]
        object_key = record["s3"]["object"]["key"]

        if object_key == "plot.png":
            continue

        total_size, total_count = compute_bucket_size_and_count(bucket_name)
        ts_ms = int(time.time() * 1000)

        print(f"Bucket={bucket_name}, size={total_size}, count={total_count}, ts_ms={ts_ms}")

        ddb.put_item(
            TableName=TABLE_NAME,
            Item={
                "bucket_name": {"S": bucket_name},
                "ts_ms": {"N": str(ts_ms)},
                "total_size_bytes": {"N": str(total_size)},
                "object_count": {"N": str(total_count)},
                "gsi1pk": {"S": "MAX"},
                "gsi1sk": {"N": str(total_size)},
            },
        )

    return {"statusCode": 200, "body": "OK"}
