from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class OrderSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_LIMIT = "STOP_LOSS_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TAKE_PROFIT_LIMIT = "TAKE_PROFIT_LIMIT"
    LIMIT_MAKER = "LIMIT_MAKER"
    TRAILING_STOP = "TRAILING_STOP"
    OCO = "OCO"


class OrderStatus(str, enum.Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    PENDING_CANCEL = "PENDING_CANCEL"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TradeType(str, enum.Enum):
    SPOT = "SPOT"
    FUTURES = "FUTURES"


class Order(Base):
    """Order model for tracking all orders"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Binance order info
    binance_order_id = Column(String(100), unique=True, index=True, nullable=True)
    client_order_id = Column(String(100), unique=True, index=True, nullable=False)

    # Order details
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(Enum(OrderSide), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    trade_type = Column(Enum(TradeType), default=TradeType.SPOT, nullable=False)

    # Pricing
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    executed_quantity = Column(Float, default=0.0, nullable=False)
    executed_price = Column(Float, nullable=True)

    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    filled_at = Column(DateTime(timezone=True), nullable=True)

    # Strategy info
    strategy_name = Column(String(100), nullable=True)
    ai_signal = Column(Boolean, default=False, nullable=False)
    ai_confidence = Column(Float, nullable=True)

    # Additional data
    fees = Column(Float, default=0.0, nullable=False)
    commission = Column(Float, default=0.0, nullable=False)
    raw_response = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<Order {self.symbol} {self.side} {self.order_type}>"


class Trade(Base):
    """Trade model for completed trades"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Trade identifiers
    trade_id = Column(String(100), unique=True, index=True, nullable=False)
    symbol = Column(String(20), nullable=False, index=True)

    # Entry order
    entry_order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    entry_price = Column(Float, nullable=False)
    entry_time = Column(DateTime(timezone=True), nullable=False)

    # Exit order
    exit_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime(timezone=True), nullable=True)

    # Trade details
    side = Column(Enum(OrderSide), nullable=False)
    quantity = Column(Float, nullable=False)
    trade_type = Column(Enum(TradeType), default=TradeType.SPOT, nullable=False)

    # P&L
    realized_pnl = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)

    # Risk management
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    trailing_stop = Column(Float, nullable=True)

    # Status
    is_open = Column(Boolean, default=True, nullable=False)
    is_profitable = Column(Boolean, nullable=True)

    # Strategy info
    strategy_name = Column(String(100), nullable=True)
    ai_signal = Column(Boolean, default=False, nullable=False)
    ai_confidence = Column(Float, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    fees_paid = Column(Float, default=0.0, nullable=False)
    notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Trade {self.symbol} {self.side} PnL: {self.realized_pnl}>"


class Position(Base):
    """Position model for tracking open positions"""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    symbol = Column(String(20), nullable=False, index=True)
    side = Column(Enum(OrderSide), nullable=False)
    trade_type = Column(Enum(TradeType), default=TradeType.SPOT, nullable=False)

    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)

    # P&L
    unrealized_pnl = Column(Float, nullable=True)
    unrealized_pnl_percent = Column(Float, nullable=True)

    # Risk management
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    trailing_stop = Column(Float, nullable=True)

    leverage = Column(Float, default=1.0, nullable=False)
    margin_used = Column(Float, nullable=True)

    is_open = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    strategy_name = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<Position {self.symbol} {self.quantity}@{self.entry_price}>"