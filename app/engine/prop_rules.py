from sqlalchemy.orm import Session
from app.models import TradingAccount, TradePosition, User, Certificate
from app.email_service import send_activity_email
from app.models import utc_now
from app.engine.market_data import market_engine
import uuid
from datetime import timedelta

def evaluate_account_and_trades(db: Session, account: TradingAccount) -> dict:
    """
    Evaluates open trades, checks SL/TP, updates floating equity,
    and runs prop firm rule evaluations (Daily Drawdown, Max Drawdown, Profit Target).
    """
    # 1. Update prices for all symbols
    market_engine.tick()

    open_trades = db.query(TradePosition).filter(
        TradePosition.account_id == account.id,
        TradePosition.status == "OPEN"
    ).all()

    total_floating_pnl = 0.0
    closed_trades_count = 0
    now = utc_now()

    # Determine Limits based on Account Type
    is_instant = account.model_type == "Instant"
    is_one_step = account.model_type == "1-Step"
    is_two_step = account.model_type == "2-Step"

    max_daily_loss_pct = 3.0 if (is_instant or is_one_step) else 4.0
    max_total_loss_pct = 5.0 if is_instant else (6.0 if is_one_step else 8.0)

    # 2. Evaluate each open trade
    for trade in open_trades:
        pnl, cur_exit_price, pips = market_engine.calculate_pnl(
            trade.symbol, trade.order_type, trade.volume_lots, trade.open_price
        )
        trade.current_price = cur_exit_price
        trade.pnl = pnl

        # Check Stop Loss requirement for Instant Fund
        if is_instant and trade.stop_loss is None and not trade.sl_penalized:
            if (now - trade.open_time).total_seconds() > 60:
                account.soft_breaches_sl += 1
                trade.sl_penalized = True
                if account.soft_breaches_sl > 2:
                    _breach_account(db, account, open_trades, "Missing Stop Loss (Exceeded 2 soft breaches)")
                    break

        # Check Stop Loss & Take Profit
        sl_hit = False
        tp_hit = False

        if trade.order_type == "BUY":
            if trade.stop_loss and cur_exit_price <= trade.stop_loss:
                sl_hit = True
            elif trade.take_profit and cur_exit_price >= trade.take_profit:
                tp_hit = True
        else: # SELL
            if trade.stop_loss and cur_exit_price >= trade.stop_loss:
                sl_hit = True
            elif trade.take_profit and cur_exit_price <= trade.take_profit:
                tp_hit = True

        if sl_hit or tp_hit:
            trade.status = "CLOSED"
            trade.close_price = cur_exit_price
            trade.close_time = now
            account.current_balance += trade.pnl
            closed_trades_count += 1
            
            # Check Minimum Trade Duration (60s)
            duration = (now - trade.open_time).total_seconds()
            if duration < 60:
                account.soft_breaches_duration += 1
                max_duration_breaches = 7 if is_instant else 10
                if account.soft_breaches_duration > max_duration_breaches:
                    _breach_account(db, account, open_trades, f"Minimum Trade Duration (Exceeded {max_duration_breaches} soft breaches)")
                    break
        else:
            total_floating_pnl += trade.pnl

    # If breached during trade loop (SL/Duration), return early
    if account.status == "BREACHED":
        db.commit()
        return _build_response(account, total_floating_pnl, {"type": "BREACH", "reason": account.breach_reason})

    # 3. Handle Daily Rollover (IST)
    ist_now = now + timedelta(hours=5, minutes=30)
    today_str = ist_now.strftime("%Y-%m-%d")
    
    if account.last_trading_day != today_str:
        # Check if previous day was profitable
        day_profit = account.current_balance - account.daily_starting_equity
        profit_pct = (day_profit / account.initial_balance) * 100.0 if account.initial_balance > 0 else 0.0
        
        required_pct = 0.25 if is_instant else 0.1
        if profit_pct >= required_pct:
            account.profit_days_count += 1
            account.days_traded += 1 # Only count profitable days for evaluation
            
        account.last_trading_day = today_str
        account.daily_starting_equity = account.current_balance # reset starting equity
        account.highest_daily_equity = account.current_balance # reset highest daily equity

    # 4. Calculate current Equity and Peaks
    account.current_equity = round(account.current_balance + total_floating_pnl, 2)
    
    # Update trailing peaks
    if account.current_equity > account.highest_account_equity:
        account.highest_account_equity = account.current_equity
    
    if account.current_equity > account.highest_daily_equity:
        account.highest_daily_equity = account.current_equity

    # 5. Check rule breaches if active
    result_event = None

    if account.status == "ACTIVE":
        
        # A. Check Inactivity (21 Days)
        if account.last_trade_time and (now - account.last_trade_time).days > 21:
            _breach_account(db, account, open_trades, "Account Inactivity (21 Days)")
            return _build_response(account, total_floating_pnl, {"type": "BREACH", "reason": account.breach_reason})

        # B. Check Weekend Rule (No open trades Friday 15:35 to Monday 09:15 IST)
        if len(open_trades) > 0:
            ist_now = now + timedelta(hours=5, minutes=30)
            day_of_week = ist_now.weekday()
            hour = ist_now.hour
            minute = ist_now.minute
            
            is_weekend_hold = False
            if day_of_week == 4 and (hour > 15 or (hour == 15 and minute >= 35)):
                is_weekend_hold = True
            elif day_of_week in (5, 6):
                is_weekend_hold = True
            elif day_of_week == 0 and (hour < 9 or (hour == 9 and minute < 15)):
                is_weekend_hold = True
                
            if is_weekend_hold:
                _breach_account(db, account, open_trades, "Weekend Holding Rule Violation")
                return _build_response(account, total_floating_pnl, {"type": "BREACH", "reason": account.breach_reason})

        # C. Check Trailing Daily Loss Breach
        daily_loss_amt = max(0.0, account.highest_daily_equity - account.current_equity)
        daily_loss_pct = (daily_loss_amt / account.highest_daily_equity) * 100.0 if account.highest_daily_equity > 0 else 0.0

        if daily_loss_pct >= max_daily_loss_pct:
            _breach_account(db, account, open_trades, f"Trailing Daily Loss Exceeded: {daily_loss_pct:.2f}% (Limit: {max_daily_loss_pct:.1f}%)")
            return _build_response(account, total_floating_pnl, {"type": "BREACH", "reason": account.breach_reason})

        # C. Check Trailing Maximum Drawdown Breach
        total_loss_amt = max(0.0, account.highest_account_equity - account.current_equity)
        total_loss_pct = (total_loss_amt / account.highest_account_equity) * 100.0 if account.highest_account_equity > 0 else 0.0

        if total_loss_pct >= max_total_loss_pct:
            _breach_account(db, account, open_trades, f"Trailing Maximum Drawdown Exceeded: {total_loss_pct:.2f}% (Limit: {max_total_loss_pct:.1f}%)")
            return _build_response(account, total_floating_pnl, {"type": "BREACH", "reason": account.breach_reason})

        # D. Check Floating Loss Limit (Instant Fund only)
        if is_instant and total_floating_pnl < 0:
            floating_loss_pct = (abs(total_floating_pnl) / account.initial_balance) * 100.0 if account.initial_balance > 0 else 0.0
            if floating_loss_pct > 1.0:
                _breach_account(db, account, open_trades, f"Floating Loss Limit Exceeded: {floating_loss_pct:.2f}% (Limit: 1.0%)")
                return _build_response(account, total_floating_pnl, {"type": "BREACH", "reason": account.breach_reason})

        # E. Check Profit Target Passed (Only for Evaluations, not Funded/Instant)
        if not is_instant and account.phase != "Funded":
            target_pct = account.profit_target_pct
            profit_pct = account.current_profit_pct
            
            if profit_pct >= target_pct and account.days_traded >= account.min_trading_days:
                if account.model_type == "2-Step" and account.phase == "Phase 1":
                    # Advance to Phase 2
                    account.phase = "Phase 2"
                    account.profit_target_pct = 8.0 # Phase 2 target is 8%
                    account.highest_daily_equity = account.current_equity
                    account.highest_account_equity = account.current_equity
                    
                    # Issue Phase 1 Passed Certificate
                    cert = Certificate(
                        cert_id=f"CERT-P1-{uuid.uuid4().hex[:6].upper()}",
                        user_id=account.user_id,
                        account_id=account.id,
                        trader_name=account.user.full_name if account.user else "Alien Trader",
                        account_size=account.initial_balance,
                        challenge_type=f"{account.model_type} Evaluation - Phase 1",
                        phase_passed="Phase 1 Evaluation Passed",
                        profit_achieved=round(account.current_profit, 2),
                        issue_date=utc_now()
                    )
                    db.add(cert)
                    result_event = {"type": "PHASE_PASSED", "phase": "Phase 2"}
                else:
                    # Fully Passed & Funded!
                    account.status = "PASSED"
                    account.phase = "Funded"
                    account.payout_cycle_start = utc_now()
                    account.profit_days_count = 0
                    
                    # Issue Funded Trader Certificate
                    cert = Certificate(
                        cert_id=f"CERT-FUNDED-{uuid.uuid4().hex[:6].upper()}",
                        user_id=account.user_id,
                        account_id=account.id,
                        trader_name=account.user.full_name if account.user else "Alien Trader",
                        account_size=account.initial_balance,
                        challenge_type=f"{account.model_type} Evaluation",
                        phase_passed="Official Funded Trader Certified",
                        profit_achieved=round(account.current_profit, 2),
                        issue_date=utc_now()
                    )
                    db.add(cert)
                    result_event = {"type": "CERTIFIED_FUNDED"}

    db.commit()
    db.refresh(account)
    return _build_response(account, total_floating_pnl, result_event)

def _breach_account(db: Session, account: TradingAccount, open_trades: list, reason: str):
    account.status = "BREACHED"
    account.breach_reason = reason
    
    # Close remaining positions
    for trade in open_trades:
        if trade.status == "OPEN":
            trade.status = "CLOSED"
            trade.close_price = trade.current_price
            trade.close_time = utc_now()
            
    user = db.query(User).filter(User.id == account.user_id).first()
    if user:
        send_activity_email(
            user.email,
            subject=f"Account Breached - {reason.split(':')[0]}",
            headline="Challenge Evaluation Breached",
            message="Unfortunately, your trading account has violated a trading rule.",
            request_info={"Account": account.account_number, "Reason": account.breach_reason, "Equity": f"INR {account.current_equity:,.2f}"}
        )
    db.commit()

def _build_response(account: TradingAccount, floating_pnl: float, result_event: dict):
    return {
        "account_id": account.id,
        "account_number": account.account_number,
        "balance": round(account.current_balance, 2),
        "equity": round(account.current_equity, 2),
        "floating_pnl": round(floating_pnl, 2),
        "profit_amount": round(account.current_profit, 2),
        "profit_pct": round(account.current_profit_pct, 2),
        "status": account.status,
        "phase": account.phase,
        "breach_reason": account.breach_reason,
        "event": result_event
    }
