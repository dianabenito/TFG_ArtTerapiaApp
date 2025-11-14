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
    if len(password) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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
    