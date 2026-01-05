"""
Blob storage operations for ZenRay.

Uses S3-compatible storage (MinIO) for candidate sets and artifacts.
"""
import json
import logging
from typing import Optional, Any

import boto3
from botocore.exceptions import ClientError

from app.config import get_settings

logger = logging.getLogger("zenray.blob")

_s3_client = None


# =============================================================================
# Connection Management
# =============================================================================

def init_blob_store():
    """Initialize S3 client and ensure bucket exists."""
    global _s3_client
    settings = get_settings()
    
    _s3_client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
    )
    
    # Ensure bucket exists
    try:
        _s3_client.head_bucket(Bucket=settings.s3_bucket)
    except ClientError:
        _s3_client.create_bucket(Bucket=settings.s3_bucket)
        logger.info(f"Created bucket: {settings.s3_bucket}")
    
    logger.info("Blob store initialized")


def get_s3_client():
    """Get S3 client."""
    if _s3_client is None:
        raise RuntimeError("S3 client not initialized")
    return _s3_client


# =============================================================================
# Candidate Set Operations
# =============================================================================

async def save_candidate_set(step_id: str, candidate_set: dict) -> str:
    """Save candidate set to blob storage."""
    settings = get_settings()
    client = get_s3_client()
    
    key = f"candidates/{step_id}.json"
    body = json.dumps(candidate_set)
    
    client.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
    )
    
    return key


async def load_candidate_set(step_id: str) -> Optional[dict]:
    """Load candidate set from blob storage."""
    settings = get_settings()
    client = get_s3_client()
    
    key = f"candidates/{step_id}.json"
    
    try:
        response = client.get_object(Bucket=settings.s3_bucket, Key=key)
        body = response["Body"].read().decode("utf-8")
        return json.loads(body)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None
        raise


# =============================================================================
# Artifact Operations
# =============================================================================

async def save_artifact(artifact_id: str, artifact: dict) -> str:
    """Save artifact to blob storage."""
    settings = get_settings()
    client = get_s3_client()
    
    key = f"artifacts/{artifact_id}.json"
    body = json.dumps(artifact)
    
    client.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
    )
    
    return key


async def load_artifact(artifact_id: str) -> Optional[dict]:
    """Load artifact from blob storage."""
    settings = get_settings()
    client = get_s3_client()
    
    key = f"artifacts/{artifact_id}.json"
    
    try:
        response = client.get_object(Bucket=settings.s3_bucket, Key=key)
        body = response["Body"].read().decode("utf-8")
        return json.loads(body)
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            return None
        raise
