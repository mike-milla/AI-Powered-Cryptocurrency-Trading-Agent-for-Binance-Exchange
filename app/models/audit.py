from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class ActionType(str, enum.Enum):
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    ORDER_PLACED = "ORDER_PLACED"
    ORDER_CANCELED = "ORDER_CANCELED"
    ORDER_FILLED = "ORDER_FILLED"
    TRADE_OPENED = "TRADE_OPENED"
    TRADE_CLOSED = "TRADE_CLOSED"
    STRATEGY_CHANGED = "STRATEGY_CHANGED"
    SETTINGS_CHANGED = "SETTINGS_CHANGED"
    API_KEY_UPDATED = "API_KEY_UPDATED"
    RISK_LIMIT_TRIGGERED = "RISK_LIMIT_TRIGGERED"
    EMERGENCY_STOP = "EMERGENCY_STOP"
    AI_DECISION = "AI_DECISION"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class AuditLog(Base):
    """Audit log for tracking all system actions"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    action_type = Column(Enum(ActionType), nullable=False, index=True)
    action_description = Column(Text, nullable=False)

    # Request details
    endpoint = Column(String(255), nullable=True)
    method = Column(String(10), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Additional context
    metadata = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<AuditLog {self.action_type} at {self.timestamp}>"


class AIDecisionLog(Base):
    """Log for AI trading decisions"""
    __tablename__ = "ai_decision_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)

    # Decision details
    decision = Column(String(20), nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Float, nullable=False)
    reasoning = Column(Text, nullable=True)

    # Technical indicators used
    indicators_used = Column(JSON, nullable=True)
    indicator_values = Column(JSON, nullable=True)

    # ML predictions
    ml_prediction = Column(Float, nullable=True)
    ml_model_version = Column(String(50), nullable=True)

    # Pattern recognition
    patterns_detected = Column(JSON, nullable=True)

    # Action taken
    action_taken = Column(String(50), nullable=True)  # ORDER_PLACED, IGNORED, MANUAL_REVIEW
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    # Override info
    was_overridden = Column(String(10), default=False, nullable=False)
    override_reason = Column(Text, nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<AIDecisionLog {self.symbol} {self.decision} conf:{self.confidence}>"


class RiskEvent(Base):
    """Risk management events"""
    __tablename__ = "risk_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    event_type = Column(String(50), nullable=False, index=True)  # STOP_LOSS, MAX_LOSS, DRAWDOWN, etc
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL

    symbol = Column(String(20), nullable=True)
    description = Column(Text, nullable=False)

    # Values
    threshold_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)

    # Action taken
    action_taken = Column(String(100), nullable=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    resolved = Column(String(10), default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<RiskEvent {self.event_type} {self.severity}>"