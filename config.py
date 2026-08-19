import os
from dotenv import load_dotenv

load_dotenv()

def is_postgres_available(uri):
    if not uri or not uri.startswith('postgresql'):
        return False
    try:
        import psycopg2
        conn = psycopg2.connect(uri, connect_timeout=2)
        conn.close()
        return True
    except Exception:
        return False

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'foodwallet-super-secret-key-2026')
    
    POSTGRES_HOST = os.getenv('DB_HOST', 'localhost')
    POSTGRES_PORT = os.getenv('DB_PORT', '5432')
    POSTGRES_DB = os.getenv('DB_NAME', 'foodwallet')
    POSTGRES_USER = os.getenv('DB_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    
    TARGET_POSTGRES_URI = os.getenv('POSTGRES_URI', f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    SQLITE_FALLBACK_URI = f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'foodwallet.db')}"

    # Auto-detect PostgreSQL availability, fallback to SQLite if offline
    if is_postgres_available(TARGET_POSTGRES_URI):
        SQLALCHEMY_DATABASE_URI = TARGET_POSTGRES_URI
        DB_ENGINE_TYPE = "PostgreSQL"
    else:
        SQLALCHEMY_DATABASE_URI = SQLITE_FALLBACK_URI
        DB_ENGINE_TYPE = "SQLite (Fallback)"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Application branding
    APP_NAME = "FOODWALLET"
    VENDOR_LOGIN_PATH = os.getenv('VENDOR_LOGIN_PATH', 'vendor-control-8x92k')
    VENDOR_USERNAME = os.getenv('VENDOR_USERNAME', 'admin')
    VENDOR_PASSWORD = os.getenv('VENDOR_PASSWORD', 'vendor123')
    
    DEFAULT_LOW_BALANCE_THRESHOLD = float(os.getenv('DEFAULT_LOW_BALANCE_THRESHOLD', '50.00'))
