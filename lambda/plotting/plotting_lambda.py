import io
import os
import time
from datetime import datetime, timezone

import boto3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ddb = boto3.client("dynamodb")
s3 = boto3.client("s3")

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
PLOT_KEY = os.getenv("PLOT_KEY", "plot.png")
LOOKBACK_SECONDS = int(os.getenv("LOOKBACK_SECONDS", "10"))
GSI_MAX_NAME = os.getenv("GSI_MAX_NAME", "gsi_max_size")


def query_last_window(bucket_name: str, lookback_seconds: int):
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - lookback_seconds * 1000

    resp = ddb.query(
        TableName=TABLE_NAME,
        KeyConditionExpression="bucket_name = :b AND ts_ms BETWEEN :t0 AND :t1",
        ProjectionExpression="ts_ms, total_size_bytes",
        ExpressionAttributeValues={
            ":b": {"S": bucket_name},
            ":t0": {"N": str(start_ms)},
            ":t1": {"N": str(now_ms)},
        },
        ScanIndexForward=True,
    )

    items = resp.get("Items", [])
    points = []
    for item in items:
        points.append(
            (
                int(item["ts_ms"]["N"]),
                int(item["total_size_bytes"]["N"]),
            )
        )
    return points


def query_global_max():
    resp = ddb.query(
        TableName=TABLE_NAME,
        IndexName=GSI_MAX_NAME,
        KeyConditionExpression="gsi1pk = :p",
        ExpressionAttributeValues={":p": {"S": "MAX"}},
        ScanIndexForward=False,
        Limit=1,
    )
    items = resp.get("Items", [])
    if not items:
        return 0
    return int(items[0]["gsi1sk"]["N"])


def make_plot(points, global_max):
    fig, ax = plt.subplots(figsize=(10, 4))

    if points:
        xs = [datetime.fromtimestamp(ts / 1000, tz=timezone.utc) for ts, _ in points]
        ys = [size for _, size in points]
        ax.plot(xs, ys, marker="o", linewidth=1.5, label=f"{BUCKET_NAME} (last 10s)")
    else:
        ax.text(
            0.5,
            0.5,
            f"No data in last {LOOKBACK_SECONDS}s",
            transform=ax.transAxes,
            ha="center",
            va="center",
        )

    if global_max > 0:
        ax.axhline(global_max, linestyle="--", linewidth=1, label="Historical high (all-time)")

    ax.set_title(f"Bucket size over last 10 s + historical high")
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("Size (bytes)")
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    fig.autofmt_xdate()

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(loc="best")

    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf


def lambda_handler(event, context):
    points = query_last_window(BUCKET_NAME, LOOKBACK_SECONDS)
    global_max = query_global_max()

    image_buffer = make_plot(points, global_max)

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=PLOT_KEY,
        Body=image_buffer.getvalue(),
        ContentType="image/png",
    )

    return {
        "statusCode": 200,
        "body": (
            f'{{"message":"plot saved","bucket":"{BUCKET_NAME}","key":"{PLOT_KEY}",'
            f'"points":{len(points)},"global_max":{global_max}}}'
        ),
    }
