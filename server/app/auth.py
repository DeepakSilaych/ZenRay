"""
Authentication utilities for ZenRay.

Supports:
- JWT tokens for dashboard authentication
- API keys for SDK authentication
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.config import get_settings
from app.db import get_pool

security = HTTPBearer(auto_error=False)


# =============================================================================
# JWT Token Operations
# =============================================================================

def create_access_token(user_id: str, email: str) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    settings = get_settings()
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        return None


# =============================================================================
# API Key Operations
# =============================================================================

def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"zenray_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


# =============================================================================
# Authentication Dependencies
# =============================================================================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[dict]:
    """
    Get current user from JWT token or API key.
    
    Returns None if no credentials provided.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    
    # Try JWT token first
    payload = verify_token(token)
    if payload:
        user_id = payload.get("sub")
        if user_id:
            pool = get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT user_id, email, name, picture FROM users WHERE user_id = $1",
                    user_id
                )
                if row:
                    return dict(row)
    
    # Try API key
    key_hash = hash_api_key(token)
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT u.user_id, u.email, u.name, u.picture
            FROM users u
            JOIN api_keys ak ON u.user_id = ak.user_id
            WHERE ak.key_hash = $1
            """,
            key_hash
        )
        if row:
            # Update last_used_at
            await conn.execute(
                "UPDATE api_keys SET last_used_at = NOW() WHERE key_hash = $1",
                key_hash
            )
            return dict(row)
    
    return None


async def require_auth(
    current_user: Optional[dict] = Depends(get_current_user),
) -> dict:
    """Require authentication - raises 401 if not authenticated."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
