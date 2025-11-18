from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings"""

    # Application Settings
    APP_NAME: str = "AI Crypto Trading Bot"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = Field(..., min_length=32)
    API_VERSION: str = "v1"

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database Configuration
    POSTGRES_USER: str = "trading_bot_user"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "trading_bot_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None

    # Binance API Configuration
    BINANCE_TESTNET: bool = True
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    BINANCE_SPOT_URL: str = "https://testnet.binance.vision/api"
    BINANCE_FUTURES_URL: str = "https://testnet.binancefuture.com"

    # Binance Production
    BINANCE_PROD_API_KEY: Optional[str] = None
    BINANCE_PROD_API_SECRET: Optional[str] = None
    BINANCE_PROD_SPOT_URL: str = "https://api.binance.com/api"
    BINANCE_PROD_FUTURES_URL: str = "https://fapi.binance.com"

    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Encryption
    ENCRYPTION_KEY: str = Field(..., min_length=32, max_length=32)

    # Trading Configuration
    DEFAULT_TRADING_PAIR: str = "BTCUSDT"
    DEFAULT_TIMEFRAME: str = "1h"
    MAX_OPEN_TRADES: int = 5
    DEFAULT_POSITION_SIZE: float = 100.0
    MAX_DAILY_LOSS_PERCENT: float = 5.0
    ENABLE_TRADING: bool = False

    # AI Configuration
    AI_AUTONOMY_LEVEL: str = "semi-auto"  # full-auto, semi-auto, signal-only
    ML_MODEL_PATH: str = "./models"
    PREDICTION_CONFIDENCE_THRESHOLD: float = 0.7

    # Risk Management
    STOP_LOSS_PERCENT: float = 2.0
    TAKE_PROFIT_PERCENT: float = 4.0
    TRAILING_STOP_PERCENT: float = 1.5
    MAX_POSITION_SIZE_PERCENT: float = 10.0

    # Notifications
    ENABLE_TELEGRAM: bool = False
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    ENABLE_EMAIL: bool = False
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    EMAIL_TO: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "./logs/trading_bot.log"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()