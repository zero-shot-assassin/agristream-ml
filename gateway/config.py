# gateway/config.py
from functools import lru_cache
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = Field(default="local")
    aws_region: str = Field(default="us-east-1")

    # Maps to AGRISTREAM_S3_BUCKET in .env
    s3_bucket_name: str = Field(alias="agristream_s3_bucket")

    # Maps to AGRISTREAM_SQS_QUEUE_URL in .env
    sqs_queue_url: AnyHttpUrl = Field(alias="agristream_sqs_queue_url")

    # Optional — if absent, boto3 falls back to IAM role / ~/.aws/credentials
    aws_access_key_id: str | None = Field(default=None)
    aws_secret_access_key: str | None = Field(default=None)

@lru_cache()
def get_settings() -> Settings:
    return Settings()   