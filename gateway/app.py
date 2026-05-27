# gateway/app.py
import asyncio
import json
import logging
from uuid import uuid4

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from pydantic import BaseModel

from gateway.aws import get_s3_client, get_sqs_client
from gateway.config import Settings, get_settings
 
logger = logging.getLogger("agristream.gateway")
logging.basicConfig(level=logging.INFO)


class UploadResponse(BaseModel):
    request_id: str
    s3_bucket: str
    s3_key: str
    message_id: str | None = None


app = FastAPI(
    title="AgriStream ML Gateway",
    version="0.1.0",
    description="Async image ingestion gateway for AgriStream ML.",
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/v1/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_image(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> UploadResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image uploads are supported.",
        )
 
    request_id = str(uuid4())
    s3_key = f"raw/{request_id}_{file.filename}"
    s3_client = get_s3_client()
    sqs_client = get_sqs_client()
 
    # ---- Phase 1: stream upload to S3 ---------------------------------------
    file.file.seek(0)
    try:
        await asyncio.to_thread(
            s3_client.upload_fileobj,
            file.file,
            settings.s3_bucket_name,
            s3_key,
        )
    except (BotoCoreError, ClientError) as exc:
        logger.exception("S3 upload failed", extra={"request_id": request_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to store image.",
        ) from exc
 
    # ---- Phase 2: enqueue SQS event ---------------------------------------
    payload = {
        "request_id": request_id,
        "bucket": settings.s3_bucket_name,
        "key": s3_key,
        "original_filename": file.filename,
        "content_type": file.content_type,
    }
    try:
        response = await asyncio.to_thread(
            sqs_client.send_message,
            QueueUrl=str(settings.sqs_queue_url),
            MessageBody=json.dumps(payload),
        )
    except (BotoCoreError, ClientError) as exc:
        logger.exception("SQS enqueue failed", extra={"request_id": request_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enqueue work item.",
        ) from exc
 
    logger.info("Upload accepted", extra={"request_id": request_id, "s3_key": s3_key})
    return UploadResponse(
        request_id=request_id,
        s3_bucket=settings.s3_bucket_name,
        s3_key=s3_key,
        message_id=response.get("MessageId"),
    )