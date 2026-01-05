import json
from typing import Any, Optional
from contextlib import asynccontextmanager

import aioboto3
from botocore.config import Config

from app.config import get_settings

_session: Optional[aioboto3.Session] = None


def init_blob_store():
    """Initialize the S3/MinIO session."""
    global _session
    _session = aioboto3.Session()


def get_session() -> aioboto3.Session:
    if _session is None:
        raise RuntimeError("Blob store not initialized")
    return _session


@asynccontextmanager
async def get_s3_client():
    """Get an async S3 client configured for MinIO."""
    settings = get_settings()
    session = get_session()
    
    async with session.client(
        's3',
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        config=Config(signature_version='s3v4'),
    ) as client:
        yield client


def _blob_key(blob_id: str) -> str:
    """Generate S3 key with prefix for better partitioning."""
    prefix = blob_id[:2] if len(blob_id) >= 2 else "00"
    return f"{prefix}/{blob_id}.json"


async def save_blob(blob_id: str, data: Any) -> str:
    """Save data to S3/MinIO, returns the blob key."""
    settings = get_settings()
    key = _blob_key(blob_id)
    body = json.dumps(data, default=str)
    
    async with get_s3_client() as s3:
        await s3.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=body.encode('utf-8'),
            ContentType='application/json',
        )
    
    return key


async def load_blob(blob_id: str) -> Optional[Any]:
    """Load data from S3/MinIO."""
    settings = get_settings()
    key = _blob_key(blob_id)
    
    try:
        async with get_s3_client() as s3:
            response = await s3.get_object(
                Bucket=settings.s3_bucket,
                Key=key,
            )
            body = await response['Body'].read()
            return json.loads(body.decode('utf-8'))
    except Exception:
        return None


async def delete_blob(blob_id: str) -> bool:
    """Delete blob from S3/MinIO."""
    settings = get_settings()
    key = _blob_key(blob_id)
    
    try:
        async with get_s3_client() as s3:
            await s3.delete_object(
                Bucket=settings.s3_bucket,
                Key=key,
            )
        return True
    except Exception:
        return False


async def blob_exists(blob_id: str) -> bool:
    """Check if blob exists in S3/MinIO."""
    settings = get_settings()
    key = _blob_key(blob_id)
    
    try:
        async with get_s3_client() as s3:
            await s3.head_object(
                Bucket=settings.s3_bucket,
                Key=key,
            )
        return True
    except Exception:
        return False


# --- Candidate Set helpers ---

async def save_candidate_set(step_id: str, candidate_set: dict) -> str:
    """Save candidate set, returns blob reference."""
    blob_id = f"cs_{step_id}"
    return await save_blob(blob_id, candidate_set)


async def load_candidate_set(step_id: str) -> Optional[dict]:
    """Load candidate set for a step."""
    blob_id = f"cs_{step_id}"
    return await load_blob(blob_id)


# --- Artifact helpers ---

async def save_artifact(artifact_id: str, content: Any) -> str:
    """Save artifact, returns blob reference."""
    blob_id = f"art_{artifact_id}"
    return await save_blob(blob_id, content)


async def load_artifact(artifact_id: str) -> Optional[Any]:
    """Load artifact content."""
    blob_id = f"art_{artifact_id}"
    return await load_blob(blob_id)
