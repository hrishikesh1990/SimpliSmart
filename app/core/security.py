from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    TODO: Implement JWT token creation
    """
    pass

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    TODO: Implement password verification
    """
    pass

def get_password_hash(password: str) -> str:
    """
    TODO: Implement password hashing
    """
    pass
