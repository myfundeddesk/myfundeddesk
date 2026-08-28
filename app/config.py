import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if present
env_file = BASE_DIR / ".env"
if env_file.exists():
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except Exception:
        pass

# Check if Render persistent disk is mounted at /data
if os.path.exists("/data"):
    DB_PATH = Path("/data/propfirm.db")
else:
    DB_PATH = BASE_DIR / "propfirm.db"

# Allow overriding with a PostgreSQL DATABASE_URL env var
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Force SQLAlchemy to use modern psycopg (v3) driver
if DATABASE_URL.startswith("postgres"):
    base_url = DATABASE_URL.split("://", 1)[1]
    DATABASE_URL = f"postgresql+pg8000://{base_url}"

# Security & Sessions
SECRET_KEY = os.getenv("SECRET_KEY", "myfundeddesk_super_secure_jwt_session_secret_2026")
SESSION_COOKIE_NAME = "myfundeddesk_session"

# Brand Identity
APP_NAME = "MyFundedDesk"
APP_SUB_NAME = "INDIA'S PREMIER PROP FIRM"
APP_TAGLINE = "Empowering Indian Traders with Institutional Capital"

# Razorpay Credentials
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_TSjqPvwaeUHguA")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "DxYT3GsAqCAN4JIzpcvjU7fN")

# Resend Email Service
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "MyFundedDesk <auth@myfundeddesk.com>")
