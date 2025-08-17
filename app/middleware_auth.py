import json
import bcrypt
import base64
from pathlib import Path
from typing import Optional, Tuple


CREDENTIALS_FILE = Path("app/admin_info/login.json")
PROTECTED_PREFIXES = ("/admin",)    
EXEMPT_PATHS = {"/healthz"}


class CredentialStore:
    def __init__(self, file_path: Path):
        data = json.loads(file_path.read_text())
        self.username: Optional[str] = data.get("username")
        self.password_plain: Optional[str] = data.get("password")
        self.password_hash: Optional[str] = data.get("password_hash")

    def verify(self, user: str, password: str) -> bool:
        if user != self.username:
            return False

        if self.password_hash:
            return bcrypt.checkpw(password.encode(), self.password_hash.encode())

        if self.password_plain is not None:
            return password == self.password_plain

        return False


class BasicAuthASGIMiddleware:
    """
    Pure ASGI middleware (no BaseHTTPMiddleware). It intercepts requests for
    protected paths and validates HTTP Basic credentials against auth.json.
    """
    def __init__(self, app, credentials_file: Path = CREDENTIALS_FILE):
        self.app = app
        self.creds = CredentialStore(credentials_file)

    async def __call__(self, scope, receive, send):
        # Only guard HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")

        # Allow explicit exemptions (e.g., health checks)
        if path in EXEMPT_PATHS:
            await self.app(scope, receive, send)
            return

        # Restrict only selected prefixes
        if not any(path.startswith(p) for p in PROTECTED_PREFIXES):
            await self.app(scope, receive, send)
            return

        # Parse Authorization header
        auth_header = None
        for k, v in scope.get("headers", []):
            if k == b"authorization":
                auth_header = v.decode("latin1")
                break

        user_pass = self._parse_basic_auth(auth_header)
        if user_pass is None:
            await self._unauthorized(send)
            return

        user, password = user_pass
        if not self.creds.verify(user, password):
            await self._unauthorized(send)
            return

        # Auth OK -> continue
        await self.app(scope, receive, send)

    @staticmethod
    def _parse_basic_auth(authorization: Optional[str]) -> Optional[Tuple[str, str]]:
        if not authorization or not authorization.lower().startswith("basic "):
            return None
        try:
            b64 = authorization.split(" ", 1)[1]
            decoded = base64.b64decode(b64).decode("utf-8")
            username, password = decoded.split(":", 1)
            return username, password
        except Exception:
            return None

    @staticmethod
    async def _unauthorized(send):
        # Build a minimal ASGI response to avoid any framework layers continuing the pipeline
        body = b'{"detail":"Unauthorized"}'
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
                (b"www-authenticate", b'Basic realm="Restricted"'),
            ],
        })
        await send({"type": "http.response.body", "body": body})
