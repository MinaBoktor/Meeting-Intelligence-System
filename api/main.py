import os
from fastapi import FastAPI, Security, HTTPException, Request
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from src.routes import router  # adjust import path to match your project layout

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

API_KEY_NAME = "AUTH"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
MASTER_API_KEY = os.environ.get("AUTH_KEY", "fallback-secret-key-for-dev")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key == MASTER_API_KEY:
        return api_key
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid or missing API Key")

app.include_router(
    router,
    dependencies=[Security(verify_api_key)],
)