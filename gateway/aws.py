# gateway/aws.py
import logging
from functools import lru_cache
 
import boto3
from botocore.client import BaseClient
 
from gateway.config import get_settings
 
logger = logging.getLogger(__name__)


@lru_cache()
def get_boto3_session() -> boto3.session.Session:
    settings = get_settings()
 
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        logger.info("Building boto3 session with explicit credentials")
        return boto3.session.Session(
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
 
    logger.info("Building boto3 session via default credentials chain (IAM role / ~/.aws)")
    return boto3.session.Session(region_name=settings.aws_region)


@lru_cache()
def get_s3_client() -> BaseClient:
    return get_boto3_session().client("s3")


@lru_cache()
def get_sqs_client() -> BaseClient:
    return get_boto3_session().client("sqs")