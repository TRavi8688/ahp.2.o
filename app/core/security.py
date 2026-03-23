import bcrypt
import hashlib
import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from app.core.config import settings

logger = logging.getLogger(__name__)

def create_access_token(subject: Union[str, Any], role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a standardized access token with short expiry."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "role": role,
        "type": "access",
        "iss": settings.PROJECT_NAME,
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, settings.ACCESS_TOKEN_SECRET, algorithm=settings.ALGORITHM)

def create_refresh_token(subject: Union[str, Any], role: str) -> str:
    """Create a long-lived refresh token."""
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire, 
        "sub": str(subject), 
        "role": role, 
        "type": "refresh",
        "iss": settings.PROJECT_NAME,
        "iat": datetime.utcnow()
    }
    return jwt.encode(to_encode, settings.REFRESH_TOKEN_SECRET, algorithm=settings.ALGORITHM)

def _get_hashable_password(password: str) -> bytes:
    """
    Pre-hash the password with SHA256 to avoid the 72-byte bcrypt limit.
    """
    sha256_hash = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(sha256_hash)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_bytes = _get_hashable_password(plain_password)
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    password_bytes = _get_hashable_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")

def decode_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Decodes a token using the appropriate secret based on its designated type.
    Enforces 'type' claim validation to prevent token substitution attacks.
    """
    try:
        secret = settings.ACCESS_TOKEN_SECRET if token_type == "access" else settings.REFRESH_TOKEN_SECRET
        payload = jwt.decode(token, secret, algorithms=[settings.ALGORITHM])
        
        if payload.get("type") != token_type:
            logger.warning(f"TOKEN_SECURITY: Type mismatch. Expected {token_type}, got {payload.get('type')}")
            return None
            
        return payload
    except JWTError as e:
        logger.debug(f"TOKEN_DECODE_ERR: {str(e)}")
        return None

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_current_user(token: str = Depends(reusable_oauth2)) -> dict:
    payload = decode_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    return payload

def require_role(role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return current_user
    return role_checker

def calculate_content_checksum(content: str) -> str:
    """
    Generates a SHA-256 checksum for data integrity verification.
    Used to detect unauthorized modification of encrypted fields.
    """
    if not content:
        return ""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
