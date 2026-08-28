from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
import random
from app.database import get_db
from app.models import User, ChallengePackage, TradingAccount, Order, utc_now
from app.email_service import send_activity_email
from app.security import require_auth
from app.engine.razorpay_client import create_razorpay_order, verify_razorpay_signature
from app.config import APP_NAME, RAZORPAY_KEY_ID

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

def calculate_discounted_price(base_price: float, coupon_code: str) -> tuple[float, float]:
    coupon_clean = (coupon_code or "").strip().upper()
    discount_pct = 0.0
    if coupon_clean in ["SAVE20", "FUNDEDDESK20", "TRADER20"]:
        discount_pct = 0.20
    elif coupon_clean in ["LAUNCH50", "HALFPRICE"]:
        discount_pct = 0.50
    elif coupon_clean in ["LAUNCH10", "WELCOME10"]:
        discount_pct = 0.10
    
    discount_amount = round(base_price * discount_pct, 2)
    final_price = max(1.0, round(base_price - discount_amount, 2))
    return final_price, discount_amount

@router.get("/buy-challenge", response_class=HTMLResponse)
async def buy_challenge_page(request: Request, model: str = "1-Step", user: User = Depends(require_auth), db: Session = Depends(get_db)):
    packages = db.query(ChallengePackage).all()

    return templates.TemplateResponse(
        request=request,
        name="buy_challenge.html",
        context={
            "app_name": APP_NAME,
            "active_page": "buy_challenge",
            "user": user,
            "packages": packages,
            "selected_model": model,
            "razorpay_key_id": RAZORPAY_KEY_ID
        }
    )

@router.post("/api/payment/create-order")
async def api_create_razorpay_order(
    request: Request,
    package_id: int = Form(...),
    coupon_code: str = Form(""),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    package = db.query(ChallengePackage).filter(ChallengePackage.id == package_id).first()
    if not package:
        return JSONResponse(status_code=404, content={"error": "Invalid challenge package"})

    final_price_inr, discount = calculate_discounted_price(package.price, coupon_code)
    receipt_id = f"rcpt_{user.id}_{random.randint(10000, 99999)}"

    order_info = create_razorpay_order(
        amount_inr=final_price_inr,
        receipt_id=receipt_id,
        notes={
            "user_id": str(user.id),
            "email": user.email,
            "package_id": str(package.id),
            "package_name": package.name
        }
    )

    return JSONResponse(content={
        "success": True,
        "order_id": order_info["order_id"],
        "amount_paise": order_info["amount_paise"],
        "amount_inr": order_info["amount_inr"],
        "currency": order_info["currency"],
        "key_id": RAZORPAY_KEY_ID,
        "user_name": user.full_name,
        "user_email": user.email,
        "package_name": package.name
    })

@router.post("/api/payment/verify")
async def api_verify_razorpay_payment(
    request: Request,
    package_id: int = Form(...),
    platform: str = Form("WebTrader"),
    coupon_code: str = Form(""),
    razorpay_order_id: str = Form(...),
    razorpay_payment_id: str = Form(...),
    razorpay_signature: str = Form(...),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    # Verify cryptographic signature
    is_valid = verify_razorpay_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature)
    if not is_valid:
        req_info = {
            "IP Address": request.client.host if request.client else "Unknown",
            "Order ID": razorpay_order_id
        }
        send_activity_email(
            user.email,
            subject="Failed Payment Attempt - MyFundedDesk",
            headline="Failed Payment Transaction",
            message="A payment attempt on your account failed verification. If this was not you, please secure your account.",
            request_info=req_info
        )
        return JSONResponse(status_code=400, content={"error": "Razorpay payment verification failed. Signature mismatch."})

    package = db.query(ChallengePackage).filter(ChallengePackage.id == package_id).first()
    if not package:
        return JSONResponse(status_code=404, content={"error": "Challenge package not found"})

    final_price_inr, _ = calculate_discounted_price(package.price, coupon_code)

    # 1. Create completed Order record
    order_id = f"ORD-{random.randint(100000, 999999)}"
    new_order = Order(
        order_id=order_id,
        user_id=user.id,
        package_name=package.name,
        account_size=package.account_size,
        model_type=package.model_type,
        platform=platform,
        amount_paid=final_price_inr,
        payment_method="Razorpay (Card / UPI / NetBanking)",
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        status="COMPLETED",
        created_at=utc_now()
    )
    db.add(new_order)

    # 2. Provision new TradingAccount for this user
    acc_num = f"FDK-{random.randint(100000, 999999)}"
    init_phase = "Funded" if package.model_type == "Instant" else "Phase 1"

    new_account = TradingAccount(
        account_number=acc_num,
        user_id=user.id,
        package_id=package.id,
        model_type=package.model_type,
        platform=platform,
        initial_balance=package.account_size,
        current_balance=package.account_size,
        current_equity=package.account_size,
        daily_starting_equity=package.account_size,
        highest_recorded_equity=package.account_size,
        phase=init_phase,
        status="ACTIVE",
        profit_target_pct=package.profit_target_p1,
        max_daily_loss_pct=package.max_daily_loss,
        max_total_loss_pct=package.max_total_loss,
        min_trading_days=package.min_trading_days,
        days_traded=1,
        created_at=utc_now()
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return JSONResponse(content={
        "success": True,
        "message": f"Payment verified! Account {new_account.account_number} provisioned.",
        "account_id": new_account.id,
        "redirect_url": f"/trading?account_id={new_account.id}&purchased=1"
    })

@router.post("/buy-challenge/checkout")
async def checkout_challenge(
    request: Request,
    package_id: int = Form(...),
    platform: str = Form("WebTrader"),
    coupon_code: str = Form(""),
    payment_method: str = Form("Razorpay"),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    package = db.query(ChallengePackage).filter(ChallengePackage.id == package_id).first()
    if not package:
        return RedirectResponse(url="/buy-challenge?error=Invalid+package", status_code=303)

    final_price_inr, _ = calculate_discounted_price(package.price, coupon_code)

    # Provision account & order
    order_id = f"ORD-{random.randint(100000, 999999)}"
    new_order = Order(
        order_id=order_id,
        user_id=user.id,
        package_name=package.name,
        account_size=package.account_size,
        model_type=package.model_type,
        platform=platform,
        amount_paid=final_price_inr,
        payment_method=payment_method,
        status="COMPLETED",
        created_at=utc_now()
    )
    db.add(new_order)

    acc_num = f"FDK-{random.randint(100000, 999999)}"
    init_phase = "Funded" if package.model_type == "Instant" else "Phase 1"

    new_account = TradingAccount(
        account_number=acc_num,
        user_id=user.id,
        package_id=package.id,
        model_type=package.model_type,
        platform=platform,
        initial_balance=package.account_size,
        current_balance=package.account_size,
        current_equity=package.account_size,
        daily_starting_equity=package.account_size,
        highest_recorded_equity=package.account_size,
        phase=init_phase,
        status="ACTIVE",
        profit_target_pct=package.profit_target_p1,
        max_daily_loss_pct=package.max_daily_loss,
        max_total_loss_pct=package.max_total_loss,
        min_trading_days=package.min_trading_days,
        days_traded=1,
        created_at=utc_now()
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return RedirectResponse(url=f"/trading?account_id={new_account.id}&success=1", status_code=303)


@router.get("/api/orders/{order_id}/receipt", response_class=HTMLResponse)
async def view_receipt(request: Request, order_id: int, db: Session = Depends(get_db), user: User = Depends(require_auth)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    return templates.TemplateResponse(
        request=request,
        name="receipt.html",
        context={"order": order, "user": user}
    )
