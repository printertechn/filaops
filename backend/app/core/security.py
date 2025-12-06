"""
Security utilities for authentication

Provides password hashing, JWT token generation, and validation
"""
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from passlib.context import CryptContext


# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
import os
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days


# ============================================================================
# PASSWORD HASHING
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt

    Args:
        password: Plain text password

    Returns:
        Hashed password (bcrypt format, 60 chars)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash

    Args:
        plain_password: Plain text password to verify
        hashed_password: Bcrypt hash to verify against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT TOKEN GENERATION
# ============================================================================

def create_access_token(
    user_id: int,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token for user authentication

    Args:
        user_id: User ID to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        JWT access token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.utcnow()
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),  # Subject (standard JWT claim)
        "type": "access",  # Token type
        "exp": expire,  # Expiration time
        "iat": now,  # Issued at
        "jti": str(uuid.uuid4()),  # JWT ID (unique identifier)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def create_refresh_token(
    user_id: int,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token for token rotation

    Args:
        user_id: User ID to encode in token
        expires_delta: Optional custom expiration time

    Returns:
        JWT refresh token string
    """
    if expires_delta is None:
        expires_delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    now = datetime.utcnow()
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),  # Subject (standard JWT claim)
        "type": "refresh",  # Token type
        "exp": expire,  # Expiration time
        "iat": now,  # Issued at
        "jti": str(uuid.uuid4()),  # JWT ID (unique identifier)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


# ============================================================================
# JWT TOKEN VALIDATION
# ============================================================================

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate JWT token

    Args:
        token: JWT token string to decode

    Returns:
        Token payload dict if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        return None
    except Exception:
        # Token is invalid (tampered, malformed, etc.)
        # PyJWT raises various exceptions: DecodeError, InvalidTokenError, etc.
        return None


def get_user_from_token(
    token: str,
    expected_type: Optional[str] = None
) -> Optional[int]:
    """
    Extract user ID from JWT token with optional type validation

    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh"), None to skip check

    Returns:
        User ID if token is valid and matches expected type, None otherwise
    """
    payload = decode_token(token)

    if payload is None:
        return None

    # Validate token type if specified
    if expected_type is not None:
        token_type = payload.get("type")
        if token_type != expected_type:
            return None

    # Extract user ID from 'sub' (subject) claim
    user_id_str = payload.get("sub")
    if user_id_str is None:
        return None

    try:
        user_id = int(user_id_str)
        return user_id
    except (ValueError, TypeError):
        return None


# ============================================================================
# REFRESH TOKEN HELPERS
# ============================================================================

def hash_refresh_token(token: str) -> str:
    """
    Hash refresh token for secure storage in database

    Args:
        token: Refresh token string to hash

    Returns:
        SHA256 hash of token (hex string, 64 characters)
    """
    return hashlib.sha256(token.encode()).hexdigest()
