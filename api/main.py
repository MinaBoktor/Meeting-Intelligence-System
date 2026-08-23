import os
from fastapi import FastAPI, Security, HTTPException, Request
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# 1. Initialize Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 2. Setup API Key Security
API_KEY_NAME = "AUTH"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Read the secret key from your environment variables
MASTER_API_KEY = os.environ.get("AUTH_KEY", "fallback-secret-key-for-dev")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key == MASTER_API_KEY:
        return api_key
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN, 
        detail="Invalid or missing API Key"
    )

# 3. Protect your endpoints with rate limits and the key dependency
@app.post("/extract")
@limiter.limit("5/minute") # Limits clients to 5 extraction calls per minute
async def extract_meeting(request: Request, api_key: str = Security(verify_api_key)):
    # Your existing extraction logic here...
    return {"message": "Extracted successfully"}

@app.post("/approve")
@limiter.limit("10/minute")
async def approve_meeting(request: Request, api_key: str = Security(verify_api_key)):
    # Your existing approval logic here...
    return {"message": "Approved successfully"}