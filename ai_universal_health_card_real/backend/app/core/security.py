from datetime import datetime, timedelta, timezone
import hashlib, secrets, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(user_id: int, role: str):
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": str(user_id), "role": role, "type": "access", "exp": exp}, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_refresh_token(user_id: int):
    exp = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_days)
    return jwt.encode({"sub": str(user_id), "type": "refresh", "exp": exp}, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str):
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

def random_token() -> str:
    return secrets.token_urlsafe(48)

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
