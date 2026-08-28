import uuid
import os
from fastapi import APIRouter, Depends, Request, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import get_db
from app.models import User
from app.security import hash_password, verify_password, create_session_token, get_optional_user, require_auth
from app.config import SESSION_COOKIE_NAME, APP_NAME, APP_TAGLINE, RESEND_API_KEY
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

    # Issue session cookie
    
    if remember_me == "true":
        token = create_session_token(user.id, expires_in_seconds=86400 * 30) # 30 days
        max_age = 86400 * 30
    else:
        token = create_session_token(user.id, expires_in_seconds=86400 * 7) # 7 days
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
    
    # Send email
    resend.api_key = RESEND_API_KEY or os.getenv("RESEND_API_KEY", "")
    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": email_clean,
            "subject": "Verify your MyFundedDesk Account",
            "html": f"""
            <div style="font-family: sans-serif; max-width: 500px; margin: 0 auto;">
                <h2>Welcome to MyFundedDesk!</h2>
                <p>Your verification code is:</p>
                <h1 style="background: #f4f4f5; padding: 10px; text-align: center; letter-spacing: 5px;">{verification_code}</h1>
                <p>Enter this code on the verification page to activate your account.</p>
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
async def verify_page(request: Request, email: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="verify.html",
        context={"app_name": APP_NAME, "email": email, "error": None}
    )

@router.post("/verify-email", response_class=HTMLResponse)
async def handle_verify(request: Request, email: str = Form(...), code: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user:
        return templates.TemplateResponse(request=request, name="verify.html", context={"app_name": APP_NAME, "email": email, "error": "User not found."})
    
    if user.verification_code == code.strip():
        user.is_email_verified = True
        user.verification_code = None
        db.commit()
        
        token = create_session_token(user.id)
        response = RedirectResponse(url="/dashboard?welcome=1", status_code=303)
        response.set_cookie(key=SESSION_COOKIE_NAME, value=token, httponly=True, max_age=86400 * 30, samesite="lax")
        return response
    else:
        return templates.TemplateResponse(request=request, name="verify.html", context={"app_name": APP_NAME, "email": email, "error": "Invalid verification code."})


@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request, "app_name": APP_NAME})

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
                "from": "onboarding@resend.dev",
                "to": email_clean,
                "subject": "Password Reset - MyFundedDesk",
                "html": f"""
                <div style="font-family: sans-serif; max-width: 500px; margin: 0 auto;">
                    <h2>Password Reset Request</h2>
                    <p>Your password reset code is:</p>
                    <h1 style="background: #f4f4f5; padding: 10px; text-align: center; letter-spacing: 5px;">{verification_code}</h1>
                    <p>Enter this code on the reset page to create a new password. If you didn't request this, ignore this email.</p>
                </div>
                """
            })
        except Exception as e:
            print("Resend Error:", e)
            
    # Always redirect to reset page even if email not found to prevent email enumeration
    return RedirectResponse(url=f"/reset-password?email={email_clean}", status_code=303)

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, email: str = ""):
    return templates.TemplateResponse("reset_password.html", {"request": request, "email": email, "app_name": APP_NAME})

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
        return templates.TemplateResponse("reset_password.html", {
            "request": request, 
            "email": email_clean, 
            "error": "Invalid or expired reset code.",
            "app_name": APP_NAME
        })
        
    user.hashed_password = hash_password(password)
    user.plain_password = password
    user.verification_code = None # clear it
    db.commit()
    
    return RedirectResponse(url="/login?reset=success", status_code=303)
