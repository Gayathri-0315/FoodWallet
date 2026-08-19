import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Security
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-only-change-this-secret-key"
    )

    # --------------------------------------------------
    # DATABASE
    # --------------------------------------------------
    # If POSTGRES_URI exists, use PostgreSQL.
    # Otherwise use local SQLite.
    POSTGRES_URI = os.getenv("POSTGRES_URI")

    if POSTGRES_URI:
        SQLALCHEMY_DATABASE_URI = POSTGRES_URI
        DB_ENGINE_TYPE = "PostgreSQL"
    else:
        SQLALCHEMY_DATABASE_URI = (
            "sqlite:///"
            + os.path.join(
                os.path.abspath(os.path.dirname(__file__)),
                "foodwallet.db"
            )
        )
        DB_ENGINE_TYPE = "SQLite (Development)"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --------------------------------------------------
    # APPLICATION
    # --------------------------------------------------
    APP_NAME = "FOODWALLET"

    # Vendor
    VENDOR_LOGIN_PATH = os.getenv(
        "VENDOR_LOGIN_PATH",
        "vendor-control-8x92k"
    )

    VENDOR_USERNAME = os.getenv(
        "VENDOR_USERNAME",
        "admin"
    )

    VENDOR_PASSWORD = os.getenv(
        "VENDOR_PASSWORD",
        "vendor123"
    )

    # Wallet
    DEFAULT_LOW_BALANCE_THRESHOLD = float(
        os.getenv(
            "DEFAULT_LOW_BALANCE_THRESHOLD",
            "50.00"
        )
    )