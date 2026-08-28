import hmac
import hashlib
import time
import json
import base64
import bcrypt
from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.config import SECRET_KEY, SESSION_COOKIE_NAME
from app.database import get_db
from app.models import User

def hash_password(password: str) -> str:
    """Hash password securely using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_session_token(user_id: int, session_version: int = 1, expires_in_seconds: int = 86400 * 7) -> str:
    """Create a tamper-proof cryptographically signed session token"""
    payload = {
        "user_id": user_id,
        "v": session_version,
        "exp": int(time.time()) + expires_in_seconds
    }
    payload_json = json.dumps(payload)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode('utf-8')).decode('utf-8')
    signature = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"

def verify_session_token(token: str) -> dict | None:
    """Verify signed session token and return payload if valid"""
    if not token or "." not in token:
        return None
    try:
        payload_b64, signature = token.split(".", 1)
        expected_sig = hmac.new(SECRET_KEY.encode('utf-8'), payload_b64.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        
        payload_json = base64.urlsafe_b64decode(payload_b64.encode('utf-8')).decode('utf-8')
        payload = json.loads(payload_json)
        
        if payload.get("exp", 0) < time.time():
            return None # Expired
            
        return payload
    except Exception:
        return None

def get_current_user_from_request(request: Request, db: Session) -> User | None:
    """Extract authenticated user from request cookie and strictly check session concurrency"""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    
    payload = verify_session_token(token)
    if not payload or not payload.get("user_id"):
        return None
        
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    
    if user:
        token_version = payload.get("v", 1)
        # If the user's current session_version is newer than the token's, the token is dead
        if user.session_version and token_version < user.session_version:
            return None
            
    return user

class LoginRequiredRedirect(Exception):
    def __init__(self, redirect_url: str):
        self.redirect_url = redirect_url

async def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    """FastAPI Dependency that enforces strict authentication. Redirects to /login if unauthenticated."""
    user = get_current_user_from_request(request, db)
    if not user:
        next_path = request.url.path
        if request.url.query:
            next_path += f"?{request.url.query}"
        # For API requests returning JSON vs page requests returning redirect
        if request.url.path.startswith("/api/"):
            raise HTTPException(status_code=401, detail="Authentication required. Please log in.")
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": f"/login?next={next_path}"}
        )
    return user

async def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Optional user dependency for public pages"""
    return get_current_user_from_request(request, db)

