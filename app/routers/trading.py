from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
from app.database import get_db
from app.models import User, TradingAccount, TradePosition, utc_now
from app.security import require_auth
from app.engine.market_data import market_engine, INSTRUMENTS
from app.engine.prop_rules import evaluate_account_and_trades
from app.config import APP_NAME
from app.engine.options_engine import calculate_option_price_live, generate_option_chain
import uuid

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

@router.get("/trading", response_class=HTMLResponse)
async def trading_terminal(
    request: Request,
    account_id: int = None,
    symbol: str = "NIFTY50",
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    accounts = db.query(TradingAccount).filter(TradingAccount.user_id == user.id).all()
    
    if not accounts:
        return templates.TemplateResponse(
            request=request,
            name="trading_terminal.html",
            context={
                "app_name": APP_NAME,
                "active_page": "trading",
                "user": user,
                "accounts": [],
                "current_account": None,
                "instruments": INSTRUMENTS,
                "current_symbol": symbol,
                "positions": [],
                "history": []
            }
        )

    current_account = None
    if account_id:
        current_account = db.query(TradingAccount).filter(TradingAccount.id == account_id, TradingAccount.user_id == user.id).first()
    
    if not current_account:
        current_account = next((a for a in accounts if a.status == "ACTIVE"), accounts[0])

    if current_account.status == "ACTIVE":
        evaluate_account_and_trades(db, current_account)

    positions = db.query(TradePosition).filter(
        TradePosition.account_id == current_account.id,
        TradePosition.status == "OPEN"
    ).order_by(TradePosition.open_time.desc()).all()

    history = db.query(TradePosition).filter(
        TradePosition.account_id == current_account.id,
        TradePosition.status == "CLOSED"
    ).order_by(TradePosition.close_time.desc()).limit(30).all()

    return templates.TemplateResponse(
        request=request,
        name="trading_terminal.html",
        context={
            "app_name": APP_NAME,
            "active_page": "trading",
            "user": user,
            "accounts": accounts,
            "current_account": current_account,
            "instruments": INSTRUMENTS,
            "current_symbol": symbol,
            "positions": positions,
            "history": history
        }
    )

@router.post("/api/trade/open")
async def open_trade(
    account_id: int = Form(...),
    symbol: str = Form(...),
    order_type: str = Form(...),
    volume_lots: float = Form(1.0),
    stop_loss: float = Form(None),
    take_profit: float = Form(None),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db)
):
    account = db.query(TradingAccount).filter(TradingAccount.id == account_id, TradingAccount.user_id == user.id).first()
    if not account:
        return JSONResponse(status_code=404, content={"error": "Trading account not found or access denied"})

    if account.status != "ACTIVE":
        return JSONResponse(status_code=400, content={"error": f"Account is not active ({account.status}). Trading disabled."})

    # --- STACKING LIMIT CHECK ---
    open_same_dir = db.query(TradePosition).filter(
        TradePosition.account_id == account.id,
        TradePosition.symbol == symbol,
        TradePosition.order_type == order_type,
        TradePosition.status == "OPEN"
    ).count()

    if open_same_dir >= 3:
        account.soft_breaches_stacking += 1
        if account.soft_breaches_stacking >= 3:
            account.status = "BREACHED"
            account.breach_reason = "Position Stacking Limit Exceeded (3 soft breaches)"
            db.commit()
            return JSONResponse(status_code=400, content={"error": "Account breached due to position stacking limit."})
        db.commit()
        return JSONResponse(status_code=400, content={"error": f"Position stacking limit reached (max 3). Soft breach recorded ({account.soft_breaches_stacking}/3)."})

    account.last_trade_time = utc_now()

    open_price = 0.0
    
    if symbol in INSTRUMENTS:
        prices = market_engine.prices[symbol]
        base_open = prices["ask"] if order_type == "BUY" else prices["bid"]
        slippage_factor = 1.0001 if order_type == "BUY" else 0.9999
        open_price = round(base_open * slippage_factor, 2)
    elif symbol.endswith("CE") or symbol.endswith("PE"):
        if "BANKNIFTY" in symbol:
            underlying = "BANKNIFTY"
        elif "FINNIFTY" in symbol:
            underlying = "FINNIFTY"
        elif "MIDCPNIFTY" in symbol:
            underlying = "MIDCPNIFTY"
        elif "SENSEX" in symbol:
            underlying = "SENSEX"
        elif "NIFTY" in symbol:
            underlying = "NIFTY50"
        else:
            underlying = "NIFTY50" 
        underlying_spot = market_engine.prices[underlying]["mid"]
        opt_price = calculate_option_price_live(symbol, underlying_spot)
        if opt_price is None:
            return JSONResponse(status_code=400, content={"error": "Invalid option symbol"})
        # Add spread for options (0.50 pts)
        base_open = opt_price + 0.25 if order_type == "BUY" else opt_price - 0.25
        open_price = round(base_open, 2)
    else:
        return JSONResponse(status_code=400, content={"error": "Invalid market symbol"})


    # --- MARGIN CHECK ---
    leverage_str = account.leverage if hasattr(account, "leverage") and account.leverage else "1:100"
    try:
        leverage = int(leverage_str.split(':')[1])
    except:
        leverage = 100
        
    is_option_trade = symbol.endswith("CE") or symbol.endswith("PE")
    if "BANKNIFTY" in symbol:
        contract_size = 15
    elif "FINNIFTY" in symbol:
        contract_size = 40
    elif "MIDCPNIFTY" in symbol:
        contract_size = 75
    elif "SENSEX" in symbol:
        contract_size = 10
    elif "NIFTY" in symbol:
        contract_size = 25
    else:
        contract_size = 25
    
    if is_option_trade:
        if order_type == "BUY":
            margin_required = open_price * volume_lots
        else:
            margin_required = 100000.0 * (volume_lots / contract_size)
    else:
        margin_required = (open_price * volume_lots) / leverage
        
    # Calculate currently used margin
    open_trades = db.query(TradePosition).filter(TradePosition.account_id == account.id, TradePosition.status == "OPEN").all()
    used_margin = 0.0
    for t in open_trades:
        t_is_opt = t.symbol.endswith("CE") or t.symbol.endswith("PE")
        t_csize = 25 if "NIFTY" in t.symbol else 15
        if t_is_opt:
            if t.order_type == "BUY":
                used_margin += t.open_price * t.volume_lots
            else:
                used_margin += 100000.0 * (t.volume_lots / t_csize)
        else:
            used_margin += (t.open_price * t.volume_lots) / leverage
            
    free_margin = account.current_equity - used_margin
    
    if free_margin < margin_required:
        return JSONResponse(status_code=400, content={"error": f"Insufficient margin. Required: {margin_required:.2f}, Free: {free_margin:.2f}"})
    # --------------------

    ticket = f"TK-{uuid.uuid4().hex[:8].upper()}"
    new_trade = TradePosition(
        ticket=ticket,
        account_id=account.id,
        symbol=symbol,
        order_type=order_type,
        volume_lots=volume_lots,
        open_price=open_price,
        current_price=open_price,
        stop_loss=stop_loss if stop_loss and stop_loss > 0 else None,
        take_profit=take_profit if take_profit and take_profit > 0 else None,
        pnl=0.0,
        status="OPEN",
        open_time=utc_now()
    )
    db.add(new_trade)
    db.commit()

    state = evaluate_account_and_trades(db, account)

    return JSONResponse(content={
        "success": True,
        "message": f"Order {order_type} {volume_lots} lots {symbol} placed at {open_price}",
        "ticket": ticket,
        "account_state": state
    })

@router.post("/api/trade/close/{trade_id}")
async def close_trade(trade_id: int, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    trade = db.query(TradePosition).join(TradingAccount).filter(
        TradePosition.id == trade_id,
        TradingAccount.user_id == user.id
    ).first()

    if not trade:
        return JSONResponse(status_code=404, content={"error": "Trade not found or access denied"})

    if trade.status != "OPEN":
        return JSONResponse(status_code=400, content={"error": "Trade is already closed"})

    account = trade.account
    pnl, cur_price, pips = market_engine.calculate_pnl(trade.symbol, trade.order_type, trade.volume_lots, trade.open_price)
    
    trade.status = "CLOSED"
    trade.close_price = cur_price
    trade.pnl = pnl
    trade.close_time = utc_now()
    
    # Check Minimum Trade Duration (60s)
    duration = (trade.close_time - trade.open_time).total_seconds()
    if duration < 60:
        account.soft_breaches_duration += 1
        is_instant = account.model_type == "Instant"
        max_duration_breaches = 7 if is_instant else 10
        if account.soft_breaches_duration > max_duration_breaches:
            account.status = "BREACHED"
            account.breach_reason = f"Minimum Trade Duration (Exceeded {max_duration_breaches} soft breaches)"

    account.current_balance += pnl
    db.commit()

    state = evaluate_account_and_trades(db, account)

    return JSONResponse(content={
        "success": True,
        "message": f"Trade {trade.ticket} closed at {cur_price} with PnL ₹{pnl:+.2f}",
        "account_state": state
    })

@router.get("/api/account/{account_id}/state")
async def get_account_state(account_id: int, user: User = Depends(require_auth), db: Session = Depends(get_db)):
    account = db.query(TradingAccount).filter(TradingAccount.id == account_id, TradingAccount.user_id == user.id).first()
    if not account:
        return JSONResponse(status_code=404, content={"error": "Account not found"})

    state = evaluate_account_and_trades(db, account)
    
    open_positions = db.query(TradePosition).filter(
        TradePosition.account_id == account.id,
        TradePosition.status == "OPEN"
    ).order_by(TradePosition.open_time.desc()).all()

    closed_positions = db.query(TradePosition).filter(
        TradePosition.account_id == account.id,
        TradePosition.status == "CLOSED"
    ).order_by(TradePosition.close_time.desc()).limit(50).all()

    positions_data = []
    for p in open_positions:
        positions_data.append({
            "id": p.id,
            "ticket": p.ticket,
            "symbol": p.symbol,
            "order_type": p.order_type,
            "volume_lots": p.volume_lots,
            "open_price": p.open_price,
            "current_price": p.current_price,
            "stop_loss": p.stop_loss,
            "take_profit": p.take_profit,
            "pnl": p.pnl,
            "open_time": p.open_time.strftime("%H:%M:%S") if p.open_time else ""
        })

    history_data = []
    for h in closed_positions:
        history_data.append({
            "id": h.id,
            "ticket": h.ticket,
            "symbol": h.symbol,
            "order_type": h.order_type,
            "volume_lots": h.volume_lots,
            "open_price": h.open_price,
            "close_price": h.close_price,
            "pnl": h.pnl,
            "close_time": h.close_time.strftime("%Y-%m-%d %H:%M:%S") if h.close_time else ""
        })

    from app.engine.market_data import admin_notifications
    user_notifications = admin_notifications.pop(account.user_id, [])
    # also pop global broadcasts (user id 0)
    # to avoid popping it for one person and removing it for everyone, we will just copy it for now 
    # but for true broadcast we would need user read-receipts. For now let's just do user_notifications.
    
    return JSONResponse(content={
        "state": state,
        "positions": positions_data,
        "history": history_data,
        "notifications": user_notifications
    })

@router.get("/api/market/prices")
async def get_prices(active_symbol: str = None):
    prices = market_engine.get_all_prices()
    
    # If the user is viewing an option, calculate its live price and append it to the list
    if active_symbol and (active_symbol.endswith("CE") or active_symbol.endswith("PE")):
        if "BANKNIFTY" in active_symbol:
            underlying = "BANKNIFTY"
        elif "FINNIFTY" in active_symbol:
            underlying = "FINNIFTY"
        elif "MIDCPNIFTY" in active_symbol:
            underlying = "MIDCPNIFTY"
        elif "SENSEX" in active_symbol:
            underlying = "SENSEX"
        elif "NIFTY" in active_symbol:
            underlying = "NIFTY50"
        else:
            underlying = "NIFTY50" 
        underlying_spot = market_engine.prices.get(underlying, {}).get("mid", 0)
        if underlying_spot > 0:
            opt_price = calculate_option_price_live(active_symbol, underlying_spot)
            if opt_price is not None:
                prices.append({
                    "symbol": active_symbol,
                    "bid": round(opt_price - 0.25, 2),
                    "ask": round(opt_price + 0.25, 2),
                    "mid": opt_price
                })
                
    return JSONResponse(content=prices)

@router.get("/api/market/candles/{symbol}")
async def get_candles(symbol: str):
    candles = market_engine.get_candles(symbol)
    return JSONResponse(content=candles)

@router.get("/api/options/{symbol}")
async def get_options_chain(symbol: str):
    if symbol not in ["NIFTY50", "BANKNIFTY"]:
        return JSONResponse(status_code=400, content={"error": "Options only supported for NIFTY50 and BANKNIFTY"})
        
    spot = market_engine.prices[symbol]["mid"]
    step = 50 if symbol == "NIFTY50" else 100
    chain = generate_option_chain(symbol.replace("50", ""), spot, strike_step=step, num_strikes=15)
    
    return JSONResponse(content={
        "symbol": symbol,
        "spot": spot,
        "chain": chain
    })
