import json
import os
import time
import boto3

s3 = boto3.client("s3")
lambda_client = boto3.client("lambda")

BUCKET_NAME = os.environ["BUCKET_NAME"]
PLOTTING_FUNCTION_NAME = os.environ["PLOTTING_FUNCTION_NAME"]
SLEEP_SECONDS = float(os.getenv("SLEEP_SECONDS", "2"))


def _put_text(key: str, text: str):
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=text.encode("utf-8"),
        ContentType="text/plain",
    )


def _delete(key: str):
    s3.delete_object(Bucket=BUCKET_NAME, Key=key)


def _invoke_plotting_lambda():
    response = lambda_client.invoke(
        FunctionName=PLOTTING_FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=b"{}",
    )
    payload = response["Payload"].read().decode("utf-8", errors="replace")
    return response.get("StatusCode", 0), payload


def lambda_handler(event, context):
    time.sleep(1)
    _put_text("assignment1.txt", "Empty Assignment 1")
    time.sleep(SLEEP_SECONDS)

    _put_text("assignment1.txt", "Empty Assignment 2222222222")
    time.sleep(SLEEP_SECONDS)

    _delete("assignment1.txt")
    time.sleep(SLEEP_SECONDS)

    _put_text("assignment2.txt", "33")
    time.sleep(SLEEP_SECONDS)
    #_wait_for_dynamodb_records()

    status, body = _invoke_plotting_lambda()

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "driver sequence complete",
                "bucket": BUCKET_NAME,
                "plot_lambda_status": status,
                "plot_lambda_response": body,
            }
        ),
    }
