from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings

bearer = HTTPBearer(auto_error=False)


def require_token(settings: Settings):
    """Return a dependency that enforces a bearer token if configured."""

    def _dep(creds: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if not settings.bearer_token:
            return True
        if not creds or creds.scheme.lower() != "bearer" or creds.credentials != settings.bearer_token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return True

    return _dep
