# worker/main.py
import io
import json
import logging
import signal
import sys
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from gateway.config import get_settings
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agristream.worker")
 
# --- Graceful shutdown flag ---------------------------------------------------
_shutdown = False

def _handle_sigterm(signum: int, frame: object) -> None:
    global _shutdown
    logger.info("SIGTERM received — finishing current message then exiting")
    _shutdown = True


signal.signal(signal.SIGTERM, _handle_sigterm)
signal.signal(signal.SIGINT, _handle_sigterm)


def get_sqs_client() -> boto3.client:
    settings = get_settings()
    return boto3.client(
        "sqs",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def get_s3_client() -> boto3.client:
    settings = get_settings()
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def process_message(s3: boto3.client, payload: dict[str, Any]) -> None:
    bucket = payload["bucket"]
    key = payload["key"]
    request_id = payload.get("request_id", "unknown")
 
    logger.info("Downloading from S3", extra={"bucket": bucket, "key": key})
 
    buffer = io.BytesIO()
    try:
        s3.download_fileobj(Bucket=bucket, Key=key, Fileobj=buffer)
    except (BotoCoreError, ClientError) as exc:
        logger.exception(
            "S3 download failed",
            extra={"request_id": request_id, "key": key},
        )
        raise   # re-raise so poll_loop's except catches it and skips delete
 
    buffer.seek(0)
    image_bytes = buffer.read()
 
    logger.info(
        "Image downloaded successfully",
        extra={"request_id": request_id, "size_bytes": len(image_bytes)},
    )


def poll_loop() -> None:
    settings = get_settings()
    sqs = get_sqs_client()
    s3 = get_s3_client()
    queue_url = str(settings.sqs_queue_url)
 
    logger.info("Worker started — polling queue: %s", queue_url)
 
    while not _shutdown:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,        # long polling
            VisibilityTimeout=60,      # give ourselves 60s to process
        )
 
        messages = response.get("Messages", [])
        if not messages:
            continue                   # nothing in queue, loop again
 
        message = messages[0]
        receipt_handle = message["ReceiptHandle"]
        payload = json.loads(message["Body"])
 
        logger.info("Received message", extra={"payload": payload})
 
        try:
            process_message(s3, payload)
        except Exception:
            logger.exception("Failed to process message — leaving in queue for retry")
            continue                   # do NOT delete — SQS will re-deliver
 
        # --- Delete only after successful processing ------------------------------------------------
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
        logger.info("Message deleted", extra={"request_id": payload.get("request_id")})
 
 
if __name__ == "__main__":
    poll_loop()