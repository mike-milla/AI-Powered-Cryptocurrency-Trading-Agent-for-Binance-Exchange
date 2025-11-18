from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class TradingStrategy(Base):
    """Trading strategy configuration"""
    __tablename__ = "trading_strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    strategy_type = Column(String(50), nullable=False)  # scalping, swing, trend_following, etc
    is_active = Column(Boolean, default=False, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    # Configuration parameters
    config = Column(JSON, nullable=False)

    # Performance tracking
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    losing_trades = Column(Integer, default=0, nullable=False)
    total_pnl = Column(Float, default=0.0, nullable=False)
    win_rate = Column(Float, nullable=True)

    # Risk parameters
    max_position_size = Column(Float, nullable=True)
    stop_loss_percent = Column(Float, nullable=True)
    take_profit_percent = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<TradingStrategy {self.name} {self.strategy_type}>"


class BacktestResult(Base):
    """Backtest results for strategies"""
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("trading_strategies.id"), nullable=True)

    strategy_name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)

    # Test period
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    # Performance metrics
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    win_rate = Column(Float, nullable=False)

    total_pnl = Column(Float, nullable=False)
    total_return_percent = Column(Float, nullable=False)

    max_drawdown = Column(Float, nullable=False)
    max_drawdown_percent = Column(Float, nullable=False)

    profit_factor = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    expectancy = Column(Float, nullable=True)

    # Additional metrics
    avg_win = Column(Float, nullable=True)
    avg_loss = Column(Float, nullable=True)
    largest_win = Column(Float, nullable=True)
    largest_loss = Column(Float, nullable=True)

    # Configuration used
    config = Column(JSON, nullable=True)

    # Detailed results
    trades_data = Column(JSON, nullable=True)
    equity_curve = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<BacktestResult {self.strategy_name} WinRate:{self.win_rate}%>"