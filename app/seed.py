from datetime import datetime, timedelta, timezone
from app.database import SessionLocal, engine, Base
from app.models import User, ChallengePackage, TradingAccount, TradePosition, Order, Certificate, AffiliateReferral, utc_now
from app.security import hash_password

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

        

    # Seed challenge packages if missing
    packages = [

            ChallengePackage(
                name="Starter 2-Step", model_type="2-Step", account_size=100000, 
                profit_target_p1=10.0, profit_target_p2=8.0, max_daily_loss=4.0, max_total_loss=8.0, 
                min_trading_days=3, price=499, description="2-Step 1L Evaluation"
            ),
            ChallengePackage(
                name="Standard 2-Step", model_type="2-Step", account_size=500000, 
                profit_target_p1=10.0, profit_target_p2=8.0, max_daily_loss=4.0, max_total_loss=8.0, 
                min_trading_days=3, price=3499, description="2-Step 5L Evaluation"
            ),
            ChallengePackage(
                name="Pro 2-Step", model_type="2-Step", account_size=1000000, 
                profit_target_p1=10.0, profit_target_p2=8.0, max_daily_loss=4.0, max_total_loss=8.0, 
                min_trading_days=3, price=6499, description="2-Step 10L Evaluation"
            ),
            ChallengePackage(
                name="Elite 2-Step", model_type="2-Step", account_size=5000000, 
                profit_target_p1=10.0, profit_target_p2=8.0, max_daily_loss=4.0, max_total_loss=8.0, 
                min_trading_days=3, price=29999, description="2-Step 50L Evaluation", is_popular=True
            ),
            ChallengePackage(
                name="Instant Starter", model_type="Instant", account_size=100000, 
                profit_target_p1=0.0, profit_target_p2=0.0, max_daily_loss=3.0, max_total_loss=5.0, 
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
                profit_target_p1=10.0, 
                profit_target_p2=0.0, 
                max_daily_loss=3.0, 
                max_total_loss=6.0, 
                min_trading_days=3, 
                price=11999, 
                is_popular=True, 
                description="Profit Target: 8% | Daily Loss Limit: 4% | Max Drawdown: 8% | Instruments: Indices, Options, Equities"
            ),
            ChallengePackage(
                name="Master", 
                model_type="1-Step", 
                account_size=5000000, 
                profit_target_p1=10.0, 
                profit_target_p2=0.0, 
                max_daily_loss=3.0, 
                max_total_loss=6.0, 
                min_trading_days=3, 
                price=24999, 
                description="Profit Target: 8% | Daily Loss Limit: 4% | Max Drawdown: 10% | VIP Priority Support"
            )
        ]
    for pkg in packages:
        if not db.query(ChallengePackage).filter(ChallengePackage.name == pkg.name, ChallengePackage.model_type == pkg.model_type).first():
            db.add(pkg)
    db.commit()

    db.close()
