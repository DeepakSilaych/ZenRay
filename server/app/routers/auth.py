import secrets
from typing import Optional
import httpx
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from app.auth import (
    create_access_token,
    require_auth,
    generate_api_key,
    hash_api_key,
)
from app.db import get_pool
from app.config import get_settings

router = APIRouter()

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


# --- Request/Response Models ---

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: Optional[str]
    picture: Optional[str]
    created_at: str


class CreateApiKeyRequest(BaseModel):
    name: str


class ApiKeyResponse(BaseModel):
    key_id: str
    key_name: str
    api_key: str  # Only returned on creation
    created_at: str
    last_used_at: Optional[str] = None


class ApiKeyListResponse(BaseModel):
    key_id: str
    key_name: str
    created_at: str
    last_used_at: Optional[str] = None


# --- Google OAuth Routes ---

@router.get("/google/url")
async def get_google_auth_url():
    """Get the Google OAuth authorization URL."""
    settings = get_settings()
    
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    redirect_uri = f"{settings.frontend_url}/auth"
    
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    
    query = "&".join(f"{k}={v}" for k, v in params.items())
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query}"
    
    return {"url": auth_url}


@router.post("/google/callback", response_model=TokenResponse)
async def google_callback(code: str = Query(...)):
    """Exchange Google authorization code for tokens and create/login user."""
    settings = get_settings()
    
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    redirect_uri = f"{settings.frontend_url}/auth"
    
    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for tokens"
            )
        
        tokens = token_response.json()
        access_token = tokens.get("access_token")
        
        # Get user info from Google
        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        if userinfo_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Google"
            )
        
        google_user = userinfo_response.json()
    
    email = google_user.get("email")
    name = google_user.get("name")
    picture = google_user.get("picture")
    google_id = google_user.get("id")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by Google"
        )
    
    pool = get_pool()
    
    async with pool.acquire() as conn:
        # Check if user exists
        row = await conn.fetchrow(
            "SELECT user_id, email, name, picture FROM users WHERE email = $1",
            email
        )
        
        if row:
            # User exists - update info and login
            user_id = row["user_id"]
            await conn.execute("""
                UPDATE users SET name = $1, picture = $2, google_id = $3, updated_at = NOW()
                WHERE user_id = $4
            """, name, picture, google_id, user_id)
        else:
            # Create new user
            user_id = f"user_{secrets.token_urlsafe(16)}"
            await conn.execute("""
                INSERT INTO users (user_id, email, name, picture, google_id)
                VALUES ($1, $2, $3, $4, $5)
            """, user_id, email, name, picture, google_id)
        
        # Create JWT token
        jwt_token = create_access_token(user_id, email)
        
        return TokenResponse(
            access_token=jwt_token,
            user={
                "user_id": user_id,
                "email": email,
                "name": name,
                "picture": picture,
            }
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(require_auth)):
    """Get current user information."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT user_id, email, name, picture, created_at FROM users WHERE user_id = $1",
            current_user["user_id"]
        )
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            user_id=row["user_id"],
            email=row["email"],
            name=row["name"],
            picture=row["picture"],
            created_at=row["created_at"].isoformat(),
        )


# --- API Key Management ---

@router.post("/api-keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateApiKeyRequest,
    current_user: dict = Depends(require_auth)
):
    """Create a new API key."""
    pool = get_pool()
    
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    key_id = f"key_{secrets.token_urlsafe(16)}"
    
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO api_keys (key_id, user_id, key_name, key_hash)
            VALUES ($1, $2, $3, $4)
        """, key_id, current_user["user_id"], request.name, key_hash)
        
        row = await conn.fetchrow(
            "SELECT created_at FROM api_keys WHERE key_id = $1",
            key_id
        )
        
        return ApiKeyResponse(
            key_id=key_id,
            key_name=request.name,
            api_key=api_key,  # Only time the full key is returned
            created_at=row["created_at"].isoformat(),
        )


@router.get("/api-keys", response_model=list[ApiKeyListResponse])
async def list_api_keys(current_user: dict = Depends(require_auth)):
    """List all API keys for the current user."""
    pool = get_pool()
    
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT key_id, key_name, created_at, last_used_at
            FROM api_keys
            WHERE user_id = $1
            ORDER BY created_at DESC
        """, current_user["user_id"])
        
        return [
            ApiKeyListResponse(
                key_id=row["key_id"],
                key_name=row["key_name"],
                created_at=row["created_at"].isoformat(),
                last_used_at=row["last_used_at"].isoformat() if row["last_used_at"] else None,
            )
            for row in rows
        ]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    key_id: str,
    current_user: dict = Depends(require_auth)
):
    """Delete an API key."""
    pool = get_pool()
    
    async with pool.acquire() as conn:
        # Verify ownership
        row = await conn.fetchrow(
            "SELECT key_id FROM api_keys WHERE key_id = $1 AND user_id = $2",
            key_id,
            current_user["user_id"]
        )
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )
        
        await conn.execute(
            "DELETE FROM api_keys WHERE key_id = $1",
            key_id
        )
