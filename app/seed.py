from datetime import datetime, timedelta, timezone
from app.database import SessionLocal, engine, Base
from app.models import User, ChallengePackage, TradingAccount, TradePosition, Order, Certificate, AffiliateReferral, utc_now
from app.security import hash_password

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Seed or update default test user with password "trader123"
    user = db.query(User).filter(User.email == "demo@myfundeddesk.in").first()
    if not user:
        user = User(
            username="trader",
            email="demo@myfundeddesk.in",
            full_name="Rajesh Kumar",
            hashed_password=hash_password("trader123"),
            is_email_verified=True,
            avatar_text="RK",
            referral_code="FDK8821"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.hashed_password:
            user.hashed_password = hash_password("trader123")
            db.commit()

    # Seed challenge packages if empty
    if db.query(ChallengePackage).count() == 0:
        packages = [

            ChallengePackage(
                name="Starter 2-Step", model_type="2-Step", account_size=100000, 
                profit_target_p1=8.0, profit_target_p2=5.0, max_daily_loss=5.0, max_total_loss=10.0, 
                min_trading_days=3, price=499, description="2-Step 1L Evaluation"
            ),
            ChallengePackage(
                name="Standard 2-Step", model_type="2-Step", account_size=500000, 
                profit_target_p1=8.0, profit_target_p2=5.0, max_daily_loss=5.0, max_total_loss=10.0, 
                min_trading_days=3, price=3499, description="2-Step 5L Evaluation"
            ),
            ChallengePackage(
                name="Pro 2-Step", model_type="2-Step", account_size=1000000, 
                profit_target_p1=8.0, profit_target_p2=5.0, max_daily_loss=5.0, max_total_loss=10.0, 
                min_trading_days=3, price=6499, description="2-Step 10L Evaluation"
            ),
            ChallengePackage(
                name="Elite 2-Step", model_type="2-Step", account_size=5000000, 
                profit_target_p1=8.0, profit_target_p2=5.0, max_daily_loss=5.0, max_total_loss=10.0, 
                min_trading_days=3, price=29999, description="2-Step 50L Evaluation", is_popular=True
            ),
            ChallengePackage(
                name="Instant Starter", model_type="Instant", account_size=100000, 
                profit_target_p1=0.0, profit_target_p2=0.0, max_daily_loss=3.0, max_total_loss=6.0, 
                min_trading_days=0, price=2499, description="Trade live instantly"
            ),

            ChallengePackage(
                name="Starter", 
                model_type="1-Step", 
                account_size=500000, 
                profit_target_p1=10.0, 
                profit_target_p2=0.0, 
                max_daily_loss=3.0, 
                max_total_loss=6.0, 
                min_trading_days=3, 
                price=3999, 
                description="Profit Target: 10% | Daily Loss Limit: 3% | Max Drawdown: 6% | Instruments: NIFTY, BANKNIFTY"
            ),
            ChallengePackage(
                name="Executive", 
                model_type="1-Step", 
                account_size=2000000, 
                profit_target_p1=8.0, 
                profit_target_p2=0.0, 
                max_daily_loss=4.0, 
                max_total_loss=8.0, 
                min_trading_days=3, 
                price=11999, 
                is_popular=True, 
                description="Profit Target: 8% | Daily Loss Limit: 4% | Max Drawdown: 8% | Instruments: Indices, Options, Equities"
            ),
            ChallengePackage(
                name="Master", 
                model_type="1-Step", 
                account_size=5000000, 
                profit_target_p1=8.0, 
                profit_target_p2=0.0, 
                max_daily_loss=4.0, 
                max_total_loss=10.0, 
                min_trading_days=3, 
                price=24999, 
                description="Profit Target: 8% | Daily Loss Limit: 4% | Max Drawdown: 10% | VIP Priority Support"
            )
        ]
        db.add_all(packages)
        db.commit()

    # Seed sample account if none exist
    if db.query(TradingAccount).filter(TradingAccount.user_id == user.id).count() == 0:
        pkg_1cr = db.query(ChallengePackage).filter(ChallengePackage.account_size == 10000000, ChallengePackage.model_type == "2-Step").first()
        
        acc_active = TradingAccount(
            account_number="FDK-100842",
            user_id=user.id,
            package_id=pkg_1cr.id if pkg_1cr else None,
            model_type="2-Step",
            platform="WebTrader",
            initial_balance=10000000.0,
            current_balance=10345000.0,
            current_equity=10412000.0,
            daily_starting_equity=10345000.0,
            highest_recorded_equity=10420000.0,
            phase="Phase 1",
            status="ACTIVE",
            profit_target_pct=8.0,
            max_daily_loss_pct=5.0,
            max_total_loss_pct=10.0,
            min_trading_days=3,
            days_traded=2,
            created_at=utc_now() - timedelta(days=2)
        )
        db.add(acc_active)
        db.commit()
        db.refresh(acc_active)

        t1 = TradePosition(
            ticket="TK-782910",
            account_id=acc_active.id,
            symbol="NIFTY50",
            order_type="BUY",
            volume_lots=2.0,
            open_price=22400.50,
            current_price=22550.80,
            stop_loss=22350.00,
            take_profit=22600.00,
            pnl=160000.0,
            status="OPEN",
            open_time=utc_now() - timedelta(hours=3)
        )
        t2 = TradePosition(
            ticket="TK-782911",
            account_id=acc_active.id,
            symbol="BANKNIFTY",
            order_type="BUY",
            volume_lots=5.0,
            open_price=48000.20,
            close_price=48200.65,
            current_price=48200.65,
            pnl=225000.0,
            status="CLOSED",
            open_time=utc_now() - timedelta(days=1),
            close_time=utc_now() - timedelta(hours=8)
        )
        db.add_all([t1, t2])

        # Passed Account
        acc_passed = TradingAccount(
            account_number="FDK-509312",
            user_id=user.id,
            model_type="2-Step",
            platform="WebTrader",
            initial_balance=5000000.0,
            current_balance=5420000.0,
            current_equity=5420000.0,
            daily_starting_equity=5420000.0,
            highest_recorded_equity=5450000.0,
            phase="Funded",
            status="PASSED",
            profit_target_pct=8.0,
            max_daily_loss_pct=5.0,
            max_total_loss_pct=10.0,
            min_trading_days=3,
            days_traded=5,
            created_at=utc_now() - timedelta(days=14)
        )
        db.add(acc_passed)
        db.commit()
        db.refresh(acc_passed)

        cert = Certificate(
            cert_id="CERT-FDK-904128",
            user_id=user.id,
            account_id=acc_passed.id,
            trader_name="Rajesh Kumar",
            account_size=5000000.0,
            challenge_type="₹50,00,000 2-Step Evaluation",
            phase_passed="Official MyFundedDesk Trader",
            profit_achieved=420000.0,
            issue_date=utc_now() - timedelta(days=2)
        )
        if not db.query(Certificate).filter_by(cert_id=cert.cert_id).first():
            db.add(cert)

        ord1 = Order(
            order_id="ORD-882190",
            user_id=user.id,
            package_name="₹1,00,00,000 2-Step Evaluation",
            account_size=10000000.0,
            model_type="2-Step",
            platform="WebTrader",
            amount_paid=44999.0,
            payment_method="Razorpay (Card / UPI / NetBanking)",
            status="COMPLETED",
            created_at=utc_now() - timedelta(days=2)
        )
        db.add(ord1)

        ref1 = AffiliateReferral(
            referrer_id=user.id,
            referred_name="Amit Singh",
            referred_email="amit.singh@gmail.com",
            challenge_purchased="₹1,00,00,000 2-Step Evaluation",
            order_amount=44999.0,
            commission_earned=6749.85,
            status="PAID",
            created_at=utc_now() - timedelta(days=5)
        )
        db.add(ref1)
        db.commit()

    db.close()
