from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, default="trader")
    email = Column(String(100), unique=True, index=True, default="trader@myfundeddesk.in")
    hashed_password = Column(String(255), nullable=True)
    plain_password = Column(String(255), nullable=True)
    full_name = Column(String(100), default="MyFundedDesk Trader")
    is_email_verified = Column(Boolean, default=False)
    verification_code = Column(String(10), nullable=True)
    is_super_admin = Column(Boolean, default=False)
    avatar_text = Column(String(10), default="FD")
    referral_code = Column(String(20), unique=True, default=lambda: f"FDK{uuid.uuid4().hex[:6].upper()}")
    deletion_requested = Column(Boolean, default=False)
    deletion_reason = Column(String(500), nullable=True)
    deletion_requested_at = Column(DateTime, nullable=True)
    session_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=utc_now)

    accounts = relationship("TradingAccount", back_populates="user")
    orders = relationship("Order", back_populates="user")
    certificates = relationship("Certificate", back_populates="user")
    referrals = relationship("AffiliateReferral", back_populates="referrer")

class ChallengePackage(Base):
    __tablename__ = "challenge_packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100)) # e.g. "₹100,000 2-Step Evaluation"
    model_type = Column(String(50)) # "1-Step", "2-Step", "Instant"
    account_size = Column(Float) # 5000, 10000, 25000, 50000, 100000, 200000
    profit_target_p1 = Column(Float, default=8.0) # 8% or 10%
    profit_target_p2 = Column(Float, default=5.0) # 5% (for 2-Step)
    max_daily_loss = Column(Float, default=5.0) # 5% or 4%
    max_total_loss = Column(Float, default=10.0) # 10% or 6%
    min_trading_days = Column(Integer, default=3) # 3 or 5 days
    leverage = Column(String(20), default="1:100")
    price = Column(Float) # INR price
    profit_split = Column(String(20), default="80/20")
    description = Column(Text, nullable=True)
    is_popular = Column(Boolean, default=False)

    accounts = relationship("TradingAccount", back_populates="package")

class TradingAccount(Base):
    __tablename__ = "trading_accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_number = Column(String(50), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    package_id = Column(Integer, ForeignKey("challenge_packages.id"), nullable=True)
    
    model_type = Column(String(50), default="2-Step") # "1-Step", "2-Step", "Instant"
    platform = Column(String(50), default="WebTrader") # "WebTrader", "MT5", "cTrader"
    
    initial_balance = Column(Float, default=100000.0)
    current_balance = Column(Float, default=100000.0)
    current_equity = Column(Float, default=100000.0)
    daily_starting_equity = Column(Float, default=100000.0)
    highest_recorded_equity = Column(Float, default=100000.0)
    highest_daily_equity = Column(Float, default=100000.0)
    highest_account_equity = Column(Float, default=100000.0)
    soft_breaches_stacking = Column(Integer, default=0)
    soft_breaches_duration = Column(Integer, default=0)
    soft_breaches_sl = Column(Integer, default=0)
    last_trade_time = Column(DateTime, default=utc_now)
    payout_cycle_start = Column(DateTime, nullable=True)
    profit_days_count = Column(Integer, default=0)
    total_payout_profit = Column(Float, default=0.0)
    best_day_profit = Column(Float, default=0.0)

    phase = Column(String(50), default="Phase 1") # "Phase 1", "Phase 2", "Funded"
    status = Column(String(50), default="ACTIVE") # "ACTIVE", "PASSED", "BREACHED"
    breach_reason = Column(String(255), nullable=True)

    profit_target_pct = Column(Float, default=8.0)
    max_daily_loss_pct = Column(Float, default=5.0)
    max_total_loss_pct = Column(Float, default=10.0)
    min_trading_days = Column(Integer, default=3)
    days_traded = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=utc_now)
    last_trading_day = Column(String(20), default=lambda: utc_now().strftime("%Y-%m-%d"))

    user = relationship("User", back_populates="accounts")
    package = relationship("ChallengePackage", back_populates="accounts")
    trades = relationship("TradePosition", back_populates="account", cascade="all, delete-orphan")
    certificate = relationship("Certificate", back_populates="account", uselist=False)

    @property
    def current_profit(self) -> float:
        return self.current_equity - self.initial_balance

    @property
    def current_profit_pct(self) -> float:
        if self.initial_balance == 0:
            return 0.0
        return ((self.current_equity - self.initial_balance) / self.initial_balance) * 100.0

    @property
    def daily_loss_amount(self) -> float:
        return max(0.0, self.daily_starting_equity - self.current_equity)

    @property
    def daily_loss_pct(self) -> float:
        if self.daily_starting_equity == 0:
            return 0.0
        return (self.daily_loss_amount / self.daily_starting_equity) * 100.0

    @property
    def total_loss_amount(self) -> float:
        return max(0.0, self.initial_balance - self.current_equity)

    @property
    def total_loss_pct(self) -> float:
        if self.initial_balance == 0:
            return 0.0
        return (self.total_loss_amount / self.initial_balance) * 100.0

    @property
    def target_amount(self) -> float:
        return self.initial_balance * (self.profit_target_pct / 100.0)

    @property
    def max_daily_loss_limit(self) -> float:
        return self.daily_starting_equity * (self.max_daily_loss_pct / 100.0)

    @property
    def max_total_loss_limit(self) -> float:
        return self.initial_balance * (self.max_total_loss_pct / 100.0)

class TradePosition(Base):
    __tablename__ = "trade_positions"

    id = Column(Integer, primary_key=True, index=True)
    ticket = Column(String(50), unique=True, default=lambda: f"TK-{uuid.uuid4().hex[:8].upper()}")
    account_id = Column(Integer, ForeignKey("trading_accounts.id"))
    
    symbol = Column(String(20)) # "EURINR", "GBPINR", "XAUINR", "BTCINR", "US30"
    order_type = Column(String(10)) # "BUY", "SELL"
    volume_lots = Column(Float, default=1.0)
    
    open_price = Column(Float)
    close_price = Column(Float, nullable=True)
    current_price = Column(Float)
    
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    sl_penalized = Column(Boolean, default=False)
    
    pnl = Column(Float, default=0.0)
    status = Column(String(20), default="OPEN") # "OPEN", "CLOSED"
    
    open_time = Column(DateTime, default=utc_now)
    close_time = Column(DateTime, nullable=True)

    account = relationship("TradingAccount", back_populates="trades")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, default=lambda: f"ORD-{uuid.uuid4().hex[:8].upper()}")
    user_id = Column(Integer, ForeignKey("users.id"))
    package_name = Column(String(100))
    account_size = Column(Float)
    model_type = Column(String(50))
    platform = Column(String(50))
    amount_paid = Column(Float)
    payment_method = Column(String(50), default="Razorpay (Card / UPI / NetBanking)")
    razorpay_order_id = Column(String(100), nullable=True)
    razorpay_payment_id = Column(String(100), nullable=True)
    status = Column(String(50), default="COMPLETED")
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User", back_populates="orders")

class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    cert_id = Column(String(50), unique=True, default=lambda: f"CERT-FDK-{uuid.uuid4().hex[:8].upper()}")
    user_id = Column(Integer, ForeignKey("users.id"))
    account_id = Column(Integer, ForeignKey("trading_accounts.id"), nullable=True)
    
    trader_name = Column(String(100))
    account_size = Column(Float)
    challenge_type = Column(String(100)) # "10L 2-Step Phase 2 Pass"
    phase_passed = Column(String(50)) # "Phase 1 Passed", "Funded Trader Certified"
    profit_achieved = Column(Float)
    issue_date = Column(DateTime, default=utc_now)
    verification_hash = Column(String(64), default=lambda: uuid.uuid4().hex)

    user = relationship("User", back_populates="certificates")
    account = relationship("TradingAccount", back_populates="certificate")

class AffiliateReferral(Base):
    __tablename__ = "affiliate_referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"))
    referred_name = Column(String(100))
    referred_email = Column(String(100))
    challenge_purchased = Column(String(100))
    order_amount = Column(Float)
    commission_earned = Column(Float) # e.g. 15%
    status = Column(String(50), default="PAID") # "PAID", "PENDING"
    created_at = Column(DateTime, default=utc_now)

    referrer = relationship("User", back_populates="referrals")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String(500))
    type = Column(String(50), default="info")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AppSetting(Base):
    __tablename__ = "app_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, index=True)
    value = Column(String(255))


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    is_admin = Column(Boolean, default=False)
    message = Column(String(1000))
    created_at = Column(DateTime, default=utc_now)
    
    user = relationship("User")

class DynamicPage(Base):
    __tablename__ = 'dynamic_pages'
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(255), unique=True, index=True)
    title = Column(String(255))
    content = Column(Text)
    is_published = Column(Boolean, default=True)


class ContactMessage(Base):
    __tablename__ = 'contact_messages'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100))
    subject = Column(String(200))
    message = Column(Text)
    created_at = Column(DateTime, default=utc_now)
