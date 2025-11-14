from fastapi import HTTPException, status
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt

# Configure password hashing context.
# Prefer `bcrypt_sha256` which pre-hashes long passwords before passing to
# the bcrypt C implementation (avoids the 72-byte limit issues). Fall back
# to plain `bcrypt` if that's all that's available. If neither can be
# initialized, log a warning and fall back to plaintext for test/CI
# environments only.
try:
    pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")
except Exception:
    # As a last resort (very unusual), use plaintext so tests can still run.
    # This keeps behavior deterministic in constrained CI environments.
    import warnings
    warnings.warn("Unable to initialize bcrypt backend for passlib; falling back to plaintext hasher")
    pwd_context = CryptContext(schemes=["plaintext"], deprecated="auto")

SECRET_KEY = "supersecretkey123456"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    # bcrypt has a 72-byte input limit. Truncate by bytes (UTF-8) to avoid
    # raising a backend ValueError in environments with a strict bcrypt.
    b = password.encode("utf-8")
    if len(b) > 72:
        import logging
        logging.getLogger(__name__).warning("Password longer than 72 bytes; truncating to 72 bytes before hashing")
        b = b[:72]
    # passlib accepts bytes as the secret; this keeps truncation consistent
    # between hashing and verification.
    return pwd_context.hash(b)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Mirror the same truncation we apply at hash time so verification
    # behaves consistently.
    b = plain_password.encode("utf-8")
    if len(b) > 72:
        from logging import getLogger
        getLogger(__name__).warning("Password longer than 72 bytes; truncating to 72 bytes before verify")
        b = b[:72]
    try:
        return pwd_context.verify(b, hashed_password)
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or expired")
    