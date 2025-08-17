import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError  # pip install python-jose[cryptography]
import bcrypt  # if you use password hashes (pip install bcrypt)


CREDENTIALS_FILE = Path("app/admin_info/login.json")
JWT_SECRET = "WAITWHATDOYOUMEANWITHTHIS"  # use env var in prod
JWT_ALG = "HS256"
JWT_TTL_MIN = 30

class CredentialStore:
    def __init__(self, file_path: Path):
        data = json.loads(file_path.read_text())
        self.username: Optional[str] = data.get("username")
        self.password_plain: Optional[str] = data.get("password")
        self.password_hash: Optional[str] = data.get("password_hash")

    def verify_password(self, username: str, password: str) -> bool:
        if username != self.username:
            return False
        if self.password_hash:
            return bcrypt.checkpw(password.encode(), self.password_hash.encode())
        if self.password_plain is not None:
            return password == self.password_plain
        return False

creds = CredentialStore(CREDENTIALS_FILE)

def create_access_token(sub: str, ttl_minutes: int = JWT_TTL_MIN) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def verify_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload
    except JWTError:
        return None
