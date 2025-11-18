from sqlalchemy import Column, Integer, String, Float, DateTime, Index, BigInteger
from sqlalchemy.sql import func
from app.core.database import Base


class Candle(Base):
    """Candlestick/OHLCV data model"""
    __tablename__ = "candles"

    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, index=True)  # 1m, 5m, 15m, 1h, 4h, 1d

    timestamp = Column(BigInteger, nullable=False, index=True)  # Unix timestamp in milliseconds
    open_time = Column(DateTime(timezone=True), nullable=False)
    close_time = Column(DateTime(timezone=True), nullable=False)

    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    quote_volume = Column(Float, nullable=True)
    trades_count = Column(Integer, nullable=True)
    taker_buy_base_volume = Column(Float, nullable=True)
    taker_buy_quote_volume = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index('idx_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp', unique=True),
    )

    def __repr__(self):
        return f"<Candle {self.symbol} {self.timeframe} {self.open_time}>"


class MarketTicker(Base):
    """Real-time market ticker data"""
    __tablename__ = "market_tickers"

    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(String(20), nullable=False, unique=True, index=True)

    last_price = Column(Float, nullable=False)
    bid_price = Column(Float, nullable=True)
    ask_price = Column(Float, nullable=True)

    price_change = Column(Float, nullable=True)
    price_change_percent = Column(Float, nullable=True)

    high_24h = Column(Float, nullable=True)
    low_24h = Column(Float, nullable=True)
    volume_24h = Column(Float, nullable=True)
    quote_volume_24h = Column(Float, nullable=True)

    weighted_avg_price = Column(Float, nullable=True)

    timestamp = Column(BigInteger, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<MarketTicker {self.symbol} ${self.last_price}>"


class OrderBook(Base):
    """Order book snapshot"""
    __tablename__ = "order_books"

    id = Column(Integer, primary_key=True, index=True)

    symbol = Column(String(20), nullable=False, index=True)

    best_bid = Column(Float, nullable=False)
    best_ask = Column(Float, nullable=False)
    spread = Column(Float, nullable=False)

    bid_volume = Column(Float, nullable=True)
    ask_volume = Column(Float, nullable=True)

    timestamp = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<OrderBook {self.symbol} Bid:{self.best_bid} Ask:{self.best_ask}>"