from datetime import datetime, timedelta
from typing import Optional, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    TODO: Generate a JWT token with the following requirements:
    - Include user data (sub field should be user email)
    - Include role information for RBAC
    - Set expiration time based on settings or expires_delta
    - Sign with SECRET_KEY using ALGORITHM from settings
    """
    pass

def verify_token(token: str) -> Optional[dict]:
    """
    TODO: Implement token verification with the following requirements:
    - Decode and verify JWT token signature
    - Check token expiration
    - Return payload if valid, None if invalid
    - Handle JWTError exceptions
    """
    pass

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    TODO: Implement password verification using pwd_context
    to verify plain password against hashed password
    """
    pass

def get_password_hash(password: str) -> str:
    """
    TODO: Generate password hash using pwd_context
    with bcrypt scheme
    """
    pass
