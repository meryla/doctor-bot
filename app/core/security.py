from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

# passlib handles all the bcrypt details for us -- we never touch raw
# hashing algorithms directly.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Turns a plain-text password into a one-way hash for storage.
    You can NEVER get the original password back out of this --
    that's the whole point.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks a plain-text password (typed at login) against the stored hash.
    Returns True/False -- never reveals or reconstructs the real password.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    """
    Builds a JWT for the given subject (we'll pass the user's email).
    The token is signed with our JWT_SECRET, so we can later verify
    it wasn't tampered with -- but note the token is NOT encrypted,
    its contents are just base64 + a signature. Never put secrets
    (like a password) inside the token payload itself.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """
    Verifies a token's signature and expiry, and returns the subject
    (the user's email) if valid. Returns None if the token is invalid,
    tampered with, or expired.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None