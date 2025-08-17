from typing import Optional, Tuple
from starlette.types import ASGIApp, Receive, Scope, Send
from app.security import verify_access_token


PROTECTED_PREFIXES = ("/admin",)
EXEMPT_PATHS = {"/healthz", "/auth/login", "/auth/validate", "/admin"}

class BearerAuthASGIMiddleware:
    """
    Pure ASGI middleware that enforces Bearer JWT auth on protected paths.
    """
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path: str = scope.get("path", "")

        if path in EXEMPT_PATHS or not any(path.startswith(p) for p in PROTECTED_PREFIXES):
            return await self.app(scope, receive, send)

        token = self._extract_bearer(scope)
        if not token:
            return await self._unauthorized(send)

        payload = verify_access_token(token)
        if not payload:
            return await self._unauthorized(send)

        # (Optional) attach identity to scope for downstream use
        scope.setdefault("state", {})
        scope["state"]["user"] = payload.get("sub")
        
        # Debug: Print what we're attaching
        print(f"Middleware: Attaching user {payload.get('sub')} to scope state")
        print(f"Middleware: Scope state after attachment: {scope.get('state')}")

        return await self.app(scope, receive, send)

    @staticmethod
    def _extract_bearer(scope: Scope) -> Optional[str]:
        for k, v in scope.get("headers", []):
            if k == b"authorization":
                auth = v.decode("latin1")
                if auth.lower().startswith("bearer "):
                    return auth.split(" ", 1)[1].strip()
        return None

    @staticmethod
    async def _unauthorized(send: Send):
        body = b'{"detail":"Unauthorized"}'
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
                # No WWW-Authenticate for Bearer unless you want RFC6750 hints
            ],
        })
        await send({"type": "http.response.body", "body": body})
