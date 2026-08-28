from sqlalchemy import text
import os
from pathlib import Path
from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.seed import seed_database
from app.routers import (
    landing,
    auth,
    dashboard,
    challenges,
    trading,
    store,
    certificates,
    affiliate,
    billing,
    profile,
    admin_sim,
    admin_dashboard,
    features
)

# Initialize Database Schema & Seed Data
Base.metadata.create_all(bind=engine)

# Auto-migrate: add any missing columns to existing tables
from sqlalchemy import text, inspect
with engine.connect() as conn:
    inspector = inspect(engine)
    if 'users' in inspector.get_table_names():
        existing_cols = [c['name'] for c in inspector.get_columns('users')]
        migrations = {
            'verification_code': "ALTER TABLE users ADD COLUMN verification_code VARCHAR(10)",
            'avatar_text': "ALTER TABLE users ADD COLUMN avatar_text VARCHAR(10) DEFAULT 'TR'",
            'referral_code': "ALTER TABLE users ADD COLUMN referral_code VARCHAR(20)",
        }
        for col_name, sql in migrations.items():
            if col_name not in existing_cols:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"[Migration] Added missing column: {col_name}")
                except Exception as e:
                    print(f"[Migration] Column {col_name} skipped: {e}")

seed_database()


app = FastAPI(
    title="MyFundedDesk - India's Premier Quantitative Prop Firm",
    description="Production-Ready Proprietary Trading Evaluation & Capital Funding Platform",
    version="2.0.0"
)

# Custom Jinja filter for Indian numbering system
def inr_format(value, decimal_places=0):
    try:
        val = float(value)
        is_negative = val < 0
        val = abs(val)
        
        if decimal_places > 0:
            formatted = f"{val:,.{decimal_places}f}"
            parts = formatted.split('.')
            int_part = parts[0]
            dec_part = f".{parts[1]}"
        else:
            int_part = f"{int(val):,}"
            dec_part = ""
            
        # Convert US commas to Indian commas (e.g. 10,000,000 -> 1,00,00,000)
        s = str(int(val))
        if len(s) > 3:
            last_3 = s[-3:]
            other = s[:-3]
            other = ','.join([other[max(i-2, 0):i] for i in range(len(other), 0, -2)][::-1])
            int_part = f"{other},{last_3}"
        else:
            int_part = s
            
        res = f"{int_part}{dec_part}"
        return f"-{res}" if is_negative else res
    except (ValueError, TypeError):
        return value

# Apply filter to templates
from app.routers.auth import templates as auth_templates
from app.routers.store import templates as store_templates
from app.routers.dashboard import templates as dashboard_templates
from app.routers.trading import templates as trading_templates
from app.routers.admin_sim import templates as admin_templates
from app.routers.challenges import templates as challenges_templates
from app.routers.certificates import templates as certificates_templates
from app.routers.affiliate import templates as affiliate_templates
from app.routers.billing import templates as billing_templates
from app.routers.profile import templates as profile_templates

for tmpl in (
    landing.templates, auth_templates, store_templates, dashboard_templates, 
    trading_templates, admin_templates, challenges_templates,
    certificates_templates, affiliate_templates, billing_templates, profile_templates
):
    tmpl.env.filters["inr"] = inr_format

# Enable CORS for Cloudflare tunnels & all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

import asyncio
from datetime import datetime, timedelta, timezone
from app.database import SessionLocal
from app.models import TradingAccount

async def daily_equity_reset_worker():
    while True:
        now = datetime.now(timezone.utc)
        next_reset = datetime(now.year, now.month, now.day, tzinfo=timezone.utc) + timedelta(days=1)
        sleep_seconds = (next_reset - now).total_seconds()
        
        await asyncio.sleep(sleep_seconds)
        
        db = SessionLocal()
        try:
            accounts = db.query(TradingAccount).filter(TradingAccount.status == "ACTIVE").all()
            for acc in accounts:
                acc.daily_starting_equity = acc.current_balance
                acc.days_traded += 1
            db.commit()
            print(f"[{datetime.now()}] Daily Drawdown limit reset for {len(accounts)} accounts.")
        except Exception as e:
            print(f"Error resetting daily equity: {e}")
        finally:
            db.close()


@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN plain_password VARCHAR(255)"))
        db.commit()
    except Exception:
        db.rollback()
        
    try:
        db.execute(text("ALTER TABLE users ADD COLUMN deletion_requested BOOLEAN DEFAULT FALSE"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        db.execute(text("ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE"))
        db.commit()
    except Exception:
        db.rollback()
        


    try:
        from datetime import datetime, timedelta
        from app.models import User
        cutoff_date = datetime.utcnow() - timedelta(days=15)
        users_to_delete = db.query(User).filter(User.deletion_requested == True, User.deletion_requested_at <= cutoff_date).all()
        for u in users_to_delete:
            db.delete(u)
        db.commit()
    except Exception as e:
        db.rollback()
        print("Auto-delete failed:", e)


    try:
        db.execute(text("CREATE TABLE IF NOT EXISTS chat_messages (id SERIAL PRIMARY KEY, user_id INTEGER, is_admin BOOLEAN DEFAULT FALSE, message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
        db.commit()
    except Exception:
        db.rollback()
        try:
            db.execute(text("CREATE TABLE IF NOT EXISTS chat_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, is_admin BOOLEAN DEFAULT 0, message TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"))
            db.commit()
        except Exception:
            db.rollback()

    try:
        db.execute(text("ALTER TABLE users ADD COLUMN deletion_requested_at TIMESTAMP"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        db.execute(text("ALTER TABLE users ADD COLUMN deletion_reason VARCHAR(500)"))
        db.commit()
    except Exception:
        db.rollback()

    try:
        db.execute(text("CREATE TABLE IF NOT EXISTS notifications (id SERIAL PRIMARY KEY, user_id INTEGER, message VARCHAR(500), type VARCHAR(50) DEFAULT 'info', is_read BOOLEAN DEFAULT FALSE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
        db.commit()
    except Exception:
        db.rollback()
        try:
            db.execute(text("CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, message VARCHAR(500), type VARCHAR(50) DEFAULT 'info', is_read BOOLEAN DEFAULT 0, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"))
            db.commit()
        except Exception as e:
            db.rollback()
            print("Notification migration failed:", e)

    finally:
        db.close()
    
    asyncio.create_task(daily_equity_reset_worker())


# Include Routers
app.include_router(landing.router)
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(challenges.router)
app.include_router(trading.router)
app.include_router(store.router)
app.include_router(certificates.router)
app.include_router(features.router)
app.include_router(affiliate.router)
app.include_router(billing.router)
app.include_router(profile.router)
app.include_router(admin_sim.router)
app.include_router(admin_dashboard.router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
