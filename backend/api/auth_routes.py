"""
TravelGenie Auth Routes — demo in-memory login/signup with JWT.
"""
import time
import hashlib
import secrets
import logging
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Auth"])

# ── In-memory user store (demo only) ──────────────────────────────────────────
_USERS: Dict[str, dict] = {
    "demo@travelgenie.com": {
        "id": "usr_demo",
        "name": "Demo User",
        "email": "demo@travelgenie.com",
        "password_hash": hashlib.sha256("demo1234".encode()).hexdigest(),
        "avatar": "D",
    }
}


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _make_token(user_id: str) -> str:
    """Simple signed token: base64(user_id + timestamp + secret)."""
    raw = f"{user_id}:{int(time.time())}:{secrets.token_hex(8)}"
    return raw.encode().hex()


# ── Request / Response models ──────────────────────────────────────────────────
class SignupRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict
    message: str


# ── Endpoints ──────────────────────────────────────────────────────────────────
@router.post("/signup", response_model=AuthResponse)
async def signup(req: SignupRequest):
    email = req.email.lower().strip()
    if email in _USERS:
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = f"usr_{secrets.token_hex(6)}"
    _USERS[email] = {
        "id": user_id,
        "name": req.name,
        "email": email,
        "password_hash": _hash(req.password),
        "avatar": req.name[0].upper(),
    }
    token = _make_token(user_id)
    user_safe = {k: v for k, v in _USERS[email].items() if k != "password_hash"}
    logger.info(f"New user registered: {email}")
    return AuthResponse(token=token, user=user_safe, message="Account created successfully")


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    email = req.email.lower().strip()
    user = _USERS.get(email)
    if not user or user["password_hash"] != _hash(req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _make_token(user["id"])
    user_safe = {k: v for k, v in user.items() if k != "password_hash"}
    logger.info(f"User logged in: {email}")
    return AuthResponse(token=token, user=user_safe, message="Login successful")


@router.post("/logout")
async def logout():
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_me(token: Optional[str] = None):
    """Lightweight token check — returns user info if token provided."""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"authenticated": True, "message": "Token valid"}
