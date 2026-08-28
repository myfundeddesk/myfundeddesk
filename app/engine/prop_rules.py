from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import TradingAccount, TradePosition, Certificate, User
from app.email_service import send_activity_email
from app.models import utc_now
from app.engine.market_data import market_engine
import uuid

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

    # 2. Evaluate each open trade
    for trade in open_trades:
        pnl, cur_exit_price, pips = market_engine.calculate_pnl(
            trade.symbol, trade.order_type, trade.volume_lots, trade.open_price
        )
        trade.current_price = cur_exit_price
        trade.pnl = pnl

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
            trade.close_time = utc_now()
            account.current_balance += trade.pnl
            closed_trades_count += 1
        else:
            total_floating_pnl += trade.pnl

    # 3. Calculate current Equity
    account.current_equity = round(account.current_balance + total_floating_pnl, 2)
    if account.current_equity > account.highest_recorded_equity:
        account.highest_recorded_equity = account.current_equity

    # 4. Check rule breaches if active
    result_event = None

    if account.status == "ACTIVE":
        # A. Check Max Daily Loss Breach
        daily_loss_amt = max(0.0, account.daily_starting_equity - account.current_equity)
        daily_loss_pct = (daily_loss_amt / account.daily_starting_equity) * 100.0 if account.daily_starting_equity > 0 else 0.0

        if daily_loss_pct >= account.max_daily_loss_pct:
            account.status = "BREACHED"
            account.breach_reason = f"Max Daily Loss Exceeded: {daily_loss_pct:.2f}% (Limit: {account.max_daily_loss_pct:.1f}%)"
            user = db.query(User).filter(User.id == account.user_id).first()
            if user:
                send_activity_email(
                    user.email,
                    subject="Account Breached - Max Daily Loss",
                    headline="Challenge Evaluation Breached",
                    message="Unfortunately, your trading account has violated the Daily Loss Limit.",
                    request_info={"Account": account.account_number, "Reason": account.breach_reason, "Equity": f"INR {account.current_equity:,.2f}"}
                )
            # Close remaining positions
            for trade in open_trades:
                if trade.status == "OPEN":
                    trade.status = "CLOSED"
                    trade.close_price = trade.current_price
                    trade.close_time = utc_now()
            result_event = {"type": "BREACH", "reason": account.breach_reason}

        # B. Check Max Overall Drawdown Breach
        total_loss_amt = max(0.0, account.initial_balance - account.current_equity)
        total_loss_pct = (total_loss_amt / account.initial_balance) * 100.0 if account.initial_balance > 0 else 0.0

        if total_loss_pct >= account.max_total_loss_pct and account.status != "BREACHED":
            account.status = "BREACHED"
            account.breach_reason = f"Max Overall Drawdown Exceeded: {total_loss_pct:.2f}% (Limit: {account.max_total_loss_pct:.1f}%)"
            user = db.query(User).filter(User.id == account.user_id).first()
            if user:
                send_activity_email(
                    user.email,
                    subject="Account Breached - Max Overall Drawdown",
                    headline="Challenge Evaluation Breached",
                    message="Unfortunately, your trading account has violated the Maximum Overall Loss Limit.",
                    request_info={"Account": account.account_number, "Reason": account.breach_reason, "Equity": f"INR {account.current_equity:,.2f}"}
                )
            # Close remaining positions
            for trade in open_trades:
                if trade.status == "OPEN":
                    trade.status = "CLOSED"
                    trade.close_price = trade.current_price
                    trade.close_time = utc_now()
            result_event = {"type": "BREACH", "reason": account.breach_reason}

        # C. Check Profit Target Passed
        profit_pct = account.current_profit_pct
        if profit_pct >= account.profit_target_pct and account.days_traded >= account.min_trading_days and account.status == "ACTIVE":
            if account.model_type == "2-Step" and account.phase == "Phase 1":
                # Advance to Phase 2
                account.phase = "Phase 2"
                account.profit_target_pct = 5.0 # Phase 2 target is usually 5%
                account.daily_starting_equity = account.current_equity
                
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

    return {
        "account_id": account.id,
        "account_number": account.account_number,
        "balance": round(account.current_balance, 2),
        "equity": round(account.current_equity, 2),
        "floating_pnl": round(total_floating_pnl, 2),
        "profit_amount": round(account.current_profit, 2),
        "profit_pct": round(account.current_profit_pct, 2),
        "daily_loss_amount": round(account.daily_loss_amount, 2),
        "daily_loss_pct": round(account.daily_loss_pct, 2),
        "total_loss_amount": round(account.total_loss_amount, 2),
        "total_loss_pct": round(account.total_loss_pct, 2),
        "status": account.status,
        "phase": account.phase,
        "breach_reason": account.breach_reason,
        "event": result_event
    }
