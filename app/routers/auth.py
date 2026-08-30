import uuid
import os
from fastapi import APIRouter, Depends, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import get_db
from app.models import User
from app.email_service import send_activity_email
from app.security import hash_password, verify_password, create_session_token, get_optional_user, require_auth
from app.config import SESSION_COOKIE_NAME, APP_NAME, APP_TAGLINE, RESEND_API_KEY, RESEND_FROM_EMAIL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
import random
import resend

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/dashboard", error: str = None, logged_out: str = None, db: Session = Depends(get_db)):
    user = await get_optional_user(request, db)
    if user:
        return RedirectResponse(url=next or "/dashboard", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "app_name": APP_NAME,
            "next": next,
            "error": error,
            "logged_out": bool(logged_out)
        }
    )

@router.post("/login")
async def handle_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    next: str = Form("/dashboard"),
    remember_me: str = Form(None),
    db: Session = Depends(get_db)
):
    email_clean = email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "app_name": APP_NAME,
                "next": next,
                "error": "Invalid email or password."
            }
        )

    if user.deletion_requested:
        return templates.TemplateResponse(
            request=request,
            name="cancel_deletion.html",
            context={
                "app_name": APP_NAME,
                "email": user.email
            }
        )


    # If user has no password set (e.g. from seed migration), set it now
    if not user.hashed_password:
        user.hashed_password = hash_password(password)
        user.plain_password = password
        db.commit()
    elif not verify_password(password, user.hashed_password):
        # Failed login email
        req_info = {
            "IP Address": request.client.host if request.client else "Unknown",
            "Device/Browser": request.headers.get("user-agent", "Unknown")
        }
        send_activity_email(
            user.email,
            subject="Failed Login Attempt - MyFundedDesk",
            headline="Security Alert: Failed Login Attempt",
            message="We detected a failed login attempt on your account. If this was you, you can safely ignore this email.",
            request_info=req_info
        )
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "app_name": APP_NAME,
                "next": next,
                "error": "Incorrect password. Please try again.",
                "email": email_clean
            }
        )

    if not user.is_email_verified:
        return RedirectResponse(url=f"/verify-email?email={email_clean}", status_code=303)

    # Secure Single Session Mode
    user.session_version = (user.session_version or 1) + 1
    db.commit()

    # Success Login Email
    req_info = {
        "IP Address": request.client.host if request.client else "Unknown",
        "Device/Browser": request.headers.get("user-agent", "Unknown")
    }
    send_activity_email(
        user.email,
        subject="New Login to Your Account - MyFundedDesk",
        headline="New Login Detected",
        message="A new login was successfully made to your MyFundedDesk account. For your security, any other active sessions on other devices have been automatically logged out.",
        request_info=req_info
    )

    # Issue session cookie
    
    if remember_me == "true":
        token = create_session_token(user.id, session_version=user.session_version, expires_in_seconds=86400 * 30) # 30 days
        max_age = 86400 * 30
    else:
        token = create_session_token(user.id, session_version=user.session_version, expires_in_seconds=86400) # 24 hours
        max_age = None # Session cookie (expires when browser closes)

    target_url = next if next and not next.startswith("/login") else "/dashboard"
    response = RedirectResponse(url=target_url, status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=max_age,
        expires=max_age,
        samesite="lax"
    )
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, next: str = "/dashboard", error: str = None, db: Session = Depends(get_db)):
    user = await get_optional_user(request, db)
    if user:
        return RedirectResponse(url=next or "/dashboard", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "app_name": APP_NAME,
            "next": next,
            "error": error
        }
    )

@router.post("/register")
async def handle_register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    next: str = Form("/dashboard"),
    remember_me: str = Form(None),
    db: Session = Depends(get_db)
):
    email_clean = email.strip().lower()
    name_clean = full_name.strip()

    if len(password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "app_name": APP_NAME,
                "next": next,
                "error": "Password must be at least 6 characters.",
                "full_name": name_clean,
                "email": email_clean
            }
        )

    if password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "app_name": APP_NAME,
                "next": next,
                "error": "Passwords do not match.",
                "full_name": name_clean,
                "email": email_clean
            }
        )

    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "app_name": APP_NAME,
                "next": next,
                "error": "An account with this email already exists. Please log in.",
                "email": email_clean
            }
        )

    # Derive avatar initials
    parts = name_clean.split()
    avatar = (parts[0][0] + (parts[1][0] if len(parts) > 1 else parts[0][1:2])).upper() if name_clean else "TR"
    
    verification_code = str(random.randint(100000, 999999))

    try:
        new_user = User(
            username=email_clean.split("@")[0],
            email=email_clean,
            full_name=name_clean,
            hashed_password=hash_password(password),
            plain_password=password,
            is_email_verified=False,
            verification_code=verification_code,
            avatar_text=avatar,
            referral_code=f"FDK{uuid.uuid4().hex[:6].upper()}"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        try:
            from app.email_service import send_activity_email
            send_activity_email(
                new_user.email,
                subject="Welcome to MyFundedDesk!",
                headline="Registration Successful",
                message="Your account has been successfully created. Welcome to the premier prop trading firm.",
                request_info={"Name": new_user.full_name, "Email": new_user.email}
            )
        except: pass

    except Exception:
        db.rollback()
        # Fallback: create user with only basic columns
        new_user = User(
            username=email_clean.split("@")[0],
            email=email_clean,
            full_name=name_clean,
            hashed_password=hash_password(password),
            plain_password=password,
            is_email_verified=False,
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        try:
            from app.email_service import send_activity_email
            send_activity_email(
                new_user.email,
                subject="Welcome to MyFundedDesk!",
                headline="Registration Successful",
                message="Your account has been successfully created. Welcome to the premier prop trading firm.",
                request_info={"Name": new_user.full_name, "Email": new_user.email}
            )
        except: pass

    
    # Send email
    resend.api_key = RESEND_API_KEY or os.getenv("RESEND_API_KEY", "")
    try:
        resend.Emails.send({
            "from": RESEND_FROM_EMAIL,
            "to": email_clean,
            "subject": "Verify your MyFundedDesk Account",
            "html": f"""
            <div style="font-family: sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; rounded: 12px;">
                <h2 style="color: #0f172a;">Welcome to MyFundedDesk!</h2>
                <p style="color: #475569;">Your verification code is:</p>
                <h1 style="background: #f1f5f9; padding: 15px; text-align: center; letter-spacing: 8px; color: #2563eb; font-size: 32px; border-radius: 8px;">{verification_code}</h1>
                <p style="color: #64748b; font-size: 14px;">Enter this 6-digit code on the verification page to activate your trader portal.</p>
            </div>
            """
        })
    except Exception as e:
        print("Resend Error:", e)

    return RedirectResponse(url=f"/verify-email?email={email_clean}", status_code=303)

@router.get("/logout")
@router.post("/logout")
async def handle_logout(request: Request):
    response = RedirectResponse(url="/login?logged_out=1", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response





@router.get("/verify-email", response_class=HTMLResponse)
async def verify_page(request: Request, email: str = "", resent: bool = False):
    return templates.TemplateResponse(
        request=request,
        name="verify.html",
        context={"app_name": APP_NAME, "email": email, "error": None, "resent": resent}
    )

@router.get("/resend-verification")
@router.post("/resend-verification")
async def handle_resend_verification(request: Request, email: str = "", db: Session = Depends(get_db)):
    email_clean = email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if user and not user.is_email_verified:
        verification_code = str(random.randint(100000, 999999))
        user.verification_code = verification_code
        db.commit()
        
        resend.api_key = RESEND_API_KEY or os.getenv("RESEND_API_KEY", "")
        try:
            resend.Emails.send({
                "from": RESEND_FROM_EMAIL,
                "to": email_clean,
                "subject": "Your Verification Code - MyFundedDesk",
                "html": f"""
                <div style="font-family: sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
                    <h2 style="color: #0f172a;">MyFundedDesk Verification</h2>
                    <p style="color: #475569;">Here is your new 6-digit verification code:</p>
                    <h1 style="background: #f1f5f9; padding: 15px; text-align: center; letter-spacing: 8px; color: #2563eb; font-size: 32px; border-radius: 8px;">{verification_code}</h1>
                    <p style="color: #64748b; font-size: 14px;">Enter this code on the verification page to activate your account.</p>
                </div>
                """
            })
        except Exception as e:
            print("Resend Error:", e)
            
    return RedirectResponse(url=f"/verify-email?email={email_clean}&resent=1", status_code=303)

@router.post("/verify-email", response_class=HTMLResponse)
async def handle_verify(request: Request, email: str = Form(...), code: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user:
        return templates.TemplateResponse(request=request, name="verify.html", context={"app_name": APP_NAME, "email": email, "error": "User not found.", "resent": False})
    
    if user.verification_code == code.strip():
        user.is_email_verified = True
        user.verification_code = None
        db.commit()
        
        token = create_session_token(user.id)
        response = RedirectResponse(url="/dashboard?welcome=1", status_code=303)
        response.set_cookie(key=SESSION_COOKIE_NAME, value=token, httponly=True, max_age=86400 * 30, samesite="lax")
        return response
    else:
        return templates.TemplateResponse(request=request, name="verify.html", context={"app_name": APP_NAME, "email": email, "error": "Invalid verification code.", "resent": False})


@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="forgot_password.html", context={"app_name": APP_NAME})

@router.post("/forgot-password")
async def handle_forgot_password(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    email_clean = email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    if user:
        # Generate OTP
        verification_code = str(random.randint(100000, 999999))
        user.verification_code = verification_code
        db.commit()
        
        # Send OTP via Resend
        import resend
        resend.api_key = RESEND_API_KEY or os.getenv("RESEND_API_KEY", "")
        try:
            resend.Emails.send({
                "from": RESEND_FROM_EMAIL,
                "to": email_clean,
                "subject": "Password Reset - MyFundedDesk",
                "html": f"""
                <div style="font-family: sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px;">
                    <h2 style="color: #0f172a;">Password Reset Request</h2>
                    <p style="color: #475569;">Your password reset code is:</p>
                    <h1 style="background: #f1f5f9; padding: 15px; text-align: center; letter-spacing: 8px; color: #2563eb; font-size: 32px; border-radius: 8px;">{verification_code}</h1>
                    <p style="color: #64748b; font-size: 14px;">Enter this code on the reset page to create a new password. If you didn't request this, ignore this email.</p>
                </div>
                """
            })
        except Exception as e:
            print("Resend Error:", e)
            
    # Always redirect to reset page even if email not found to prevent email enumeration
    return RedirectResponse(url=f"/reset-password?email={email_clean}", status_code=303)

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, email: str = ""):
    return templates.TemplateResponse(request=request, name="reset_password.html", context={"email": email, "app_name": APP_NAME})

@router.post("/reset-password")
async def handle_reset_password(
    request: Request, 
    email: str = Form(...), 
    code: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    email_clean = email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    if not user or user.verification_code != code.strip():
        return templates.TemplateResponse(request=request, name="reset_password.html", context={
            "email": email_clean, 
            "error": "Invalid or expired reset code.",
            "app_name": APP_NAME
        })
        
    user.hashed_password = hash_password(password)
    user.plain_password = password
    user.verification_code = None # clear it
    db.commit()
    
    return RedirectResponse(url="/login?reset=success", status_code=303)

import requests
import urllib.parse

@router.get("/auth/google/login")
async def google_login():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url)

@router.get("/auth/google/callback")
async def google_callback(request: Request, code: str = None, error: str = None, db: Session = Depends(get_db)):
    if error or not code:
        return RedirectResponse(url="/login?error=Google authentication failed")

    # Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    r = requests.post(token_url, data=data)
    if not r.ok:
        return RedirectResponse(url="/login?error=Failed to retrieve Google token")
        
    access_token = r.json().get("access_token")
    
    # Get user info
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    r = requests.get(user_info_url, headers={"Authorization": f"Bearer {access_token}"})
    if not r.ok:
        return RedirectResponse(url="/login?error=Failed to retrieve Google user info")
        
    user_info = r.json()
    email = user_info.get("email")
    name = user_info.get("name", "Trader")
    
    if not email:
        return RedirectResponse(url="/login?error=Google account has no email")
        
    email_clean = email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    
    if not user:
        import uuid
        # Create new user
        user = User(
            username=f"google_{uuid.uuid4().hex[:8]}",
            full_name=name,
            email=email_clean,
            is_email_verified=True, # Trusted from Google
            avatar_text="".join([n[0] for n in name.split()[:2]]).upper() or "FD"
        )
        db.add(user)
        db.commit()
    else:
        # If user existed but wasn't verified, verify them since Google verified the email
        if not user.is_email_verified:
            user.is_email_verified = True
            
        user.session_version = (user.session_version or 1) + 1
        db.commit()
        
    # Send login email
    req_info = {
        "IP Address": request.client.host if request.client else "Unknown",
        "Method": "Google Single Sign-On"
    }
    send_activity_email(
        user.email,
        subject="New Login to Your Account - MyFundedDesk",
        headline="New Login Detected",
        message="A new login was successfully made to your MyFundedDesk account via Google. For your security, any other active sessions on other devices have been automatically logged out.",
        request_info=req_info
    )

    # Issue session cookie
    token = create_session_token(user.id, session_version=user.session_version, expires_in_seconds=86400 * 30)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True, # Must be true in production HTTPS
        samesite="lax",
        max_age=86400 * 30
    )
    return response
