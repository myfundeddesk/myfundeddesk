from app.models import Notification
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import get_db
from app.models import User, TradingAccount, ChallengePackage, Certificate
from app.security import require_auth
from app.engine.prop_rules import evaluate_account_and_trades
from app.config import APP_NAME, APP_TAGLINE

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

from fastapi import Query
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, model: str = Query(None), user: User = Depends(require_auth), db: Session = Depends(get_db)):
    accounts_query = db.query(TradingAccount).filter(TradingAccount.user_id == user.id)
    if model:
        # Some accounts might have model_type like '1-Step', '2-Step', 'Instant'
        accounts_query = accounts_query.filter(TradingAccount.model_type == model)
    accounts = accounts_query.all()
    notifications = db.query(Notification).filter(Notification.user_id.is_(None)).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Evaluate live metrics for active accounts
    for acc in accounts:
        if acc.status == "ACTIVE":
            evaluate_account_and_trades(db, acc)

    
    active_evaluations = [a for a in accounts if a.status == "ACTIVE" and a.phase in ["Phase 1", "Phase 2"]]
    funded_accounts = [a for a in accounts if a.status == "ACTIVE" and a.phase == "Funded"]
    breached_accounts = [a for a in accounts if a.status == "BREACHED"]
    
    # Calculate summary stats
    total_balance = sum(a.current_balance for a in accounts)
    total_equity = sum(a.current_equity for a in accounts)
    total_profit = sum(a.current_profit for a in accounts)
    
    class DummyMetrics:
        win_rate = 65.4
        profit_factor = 1.8
        total_trades = 124
        
    metrics = DummyMetrics()


    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
        "app_name": APP_NAME,
        "app_tagline": APP_TAGLINE,
        "active_page": "dashboard",
        "user": user,
        "accounts": accounts,
        "notifications": notifications,
        "active_evaluations": active_evaluations,
        "funded_accounts": funded_accounts,
        "breached_accounts": breached_accounts,
        "total_balance": round(total_balance, 2),
        "total_equity": round(total_equity, 2),
        "total_profit": round(total_profit, 2),
        "metrics": metrics
    }
    )


@router.post("/api/payout/request")
async def request_payout(account_id: int = Form(...), user: User = Depends(require_auth), db: Session = Depends(get_db)):
    account = db.query(TradingAccount).filter(TradingAccount.id == account_id, TradingAccount.user_id == user.id).first()
    if not account or account.phase != "Funded":
        raise HTTPException(status_code=400, detail="Invalid account for payout")
    
    if account.current_profit <= 0:
        raise HTTPException(status_code=400, detail="No profits available for payout")
        
    # Mock payout deduction
    payout_amt = account.current_profit
    account.current_balance -= payout_amt
    account.current_equity -= payout_amt
    db.commit()
    
    return RedirectResponse(url="/dashboard?payout_success=1", status_code=303)

from fastapi.responses import JSONResponse, RedirectResponse

@router.post("/api/notifications/{notif_id}/dismiss")
async def dismiss_notification(notif_id: int, request: Request, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notif_id).first()
    if not notif:
        return JSONResponse({"success": False})
    
    # Delete the notification
    db.delete(notif)
    db.commit()
    
    return JSONResponse({"success": True})

@router.get("/api/notifications")
async def get_notifications(request: Request, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(
        (Notification.user_id == user.id) | (Notification.user_id.is_(None))
    ).order_by(Notification.created_at.desc()).limit(20).all()
    
    return JSONResponse([
        {"id": n.id, "message": n.message, "type": n.type if hasattr(n, 'type') else "info", "created_at": n.created_at.isoformat() if n.created_at else ""}
        for n in notifications
    ])


@router.get("/accounts/{account_type}", response_class=HTMLResponse)
async def view_accounts(request: Request, account_type: str, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    accounts_query = db.query(TradingAccount).filter(TradingAccount.user_id == user.id)
    
    if account_type == "challenge":
        accounts_query = accounts_query.filter(TradingAccount.model_type != 'Instant')
    elif account_type == "instant":
        accounts_query = accounts_query.filter(TradingAccount.model_type == 'Instant')
    elif account_type == "pending":
        accounts_query = accounts_query.filter(TradingAccount.status == 'PENDING')
        
    accounts = accounts_query.all()
    
    # Calculate stats for these specific accounts
    total_balance = sum(a.initial_balance for a in accounts)
    total_equity = sum(a.current_equity for a in accounts)
    total_profit = sum(a.current_profit for a in accounts)
    active_accounts = [a for a in accounts if a.status == 'ACTIVE']
    passed_accounts = [a for a in accounts if a.status == 'PASSED']

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "app_name": APP_NAME,
            "user": user,
            "accounts": accounts,
            "total_balance": total_balance,
            "total_equity": total_equity,
            "total_profit": total_profit,
            "active_accounts": active_accounts,
            "passed_accounts": passed_accounts,
            "filter_type": account_type.title()
        }
    )

@router.get('/rules', response_class=HTMLResponse)
async def rules_page(request: Request):
    return templates.TemplateResponse(request=request, name='rules.html', context={'app_name': APP_NAME})


@router.get('/api/chat/messages')
async def get_chat_messages(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    from app.models import ChatMessage
    msgs = db.query(ChatMessage).filter(ChatMessage.user_id == user.id).order_by(ChatMessage.created_at.asc()).all()
    return [{"id": m.id, "is_admin": m.is_admin, "message": m.message, "time": m.created_at.isoformat()} for m in msgs]

from pydantic import BaseModel
class ChatPayload(BaseModel):
    message: str

@router.post('/api/chat/send')
async def send_chat_message(payload: ChatPayload, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    from app.models import ChatMessage
    msg = ChatMessage(user_id=user.id, is_admin=False, message=payload.message)
    db.add(msg)
    db.commit()
    return {"success": True}

@router.get('/api/notifications')
async def get_notifications(user: User = Depends(require_auth), db: Session = Depends(get_db)):
    from app.models import Notification
    notifs = db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == False).all()
    res = [{"id": n.id, "message": n.message, "type": n.type} for n in notifs]
    for n in notifs:
        n.is_read = True
    db.commit()
    return res
