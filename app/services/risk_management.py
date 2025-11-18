from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import logging

from app.models.trade import Trade, Position, Order, OrderSide
from app.models.audit import RiskEvent
from app.models.user import User
from config import settings

logger = logging.getLogger(__name__)


class RiskManagementService:
    """Comprehensive risk management for trading operations"""

    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

        # Risk parameters (can be customized per user)
        self.max_position_size_percent = settings.MAX_POSITION_SIZE_PERCENT
        self.stop_loss_percent = settings.STOP_LOSS_PERCENT
        self.take_profit_percent = settings.TAKE_PROFIT_PERCENT
        self.max_daily_loss_percent = settings.MAX_DAILY_LOSS_PERCENT
        self.max_open_trades = settings.MAX_OPEN_TRADES

    async def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        risk_percent: float = 2.0
    ) -> Dict[str, Any]:
        """
        Calculate position size based on risk management rules

        Args:
            account_balance: Total account balance
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price
            risk_percent: Maximum risk per trade as percentage

        Returns:
            Position sizing information
        """
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)

        # Calculate maximum risk amount
        max_risk_amount = account_balance * (risk_percent / 100)

        # Calculate position size
        position_size = max_risk_amount / risk_per_unit if risk_per_unit > 0 else 0

        # Calculate position value
        position_value = position_size * entry_price

        # Check if position exceeds maximum position size
        max_position_value = account_balance * (self.max_position_size_percent / 100)

        if position_value > max_position_value:
            position_size = max_position_value / entry_price
            position_value = max_position_value
            actual_risk_percent = (position_size * risk_per_unit / account_balance) * 100
        else:
            actual_risk_percent = risk_percent

        return {
            'position_size': position_size,
            'position_value': position_value,
            'risk_amount': position_size * risk_per_unit,
            'risk_percent': actual_risk_percent,
            'max_position_size_exceeded': position_value > max_position_value
        }

    async def calculate_stop_loss(
        self,
        entry_price: float,
        side: OrderSide,
        atr: Optional[float] = None,
        method: str = 'fixed'
    ) -> float:
        """
        Calculate stop loss price

        Args:
            entry_price: Entry price
            side: Order side (BUY or SELL)
            atr: Average True Range for ATR-based stop loss
            method: 'fixed', 'trailing', or 'atr'

        Returns:
            Stop loss price
        """
        if method == 'fixed':
            # Fixed percentage stop loss
            if side == OrderSide.BUY:
                stop_loss = entry_price * (1 - self.stop_loss_percent / 100)
            else:
                stop_loss = entry_price * (1 + self.stop_loss_percent / 100)

        elif method == 'atr' and atr:
            # ATR-based stop loss (typically 2x ATR)
            if side == OrderSide.BUY:
                stop_loss = entry_price - (2 * atr)
            else:
                stop_loss = entry_price + (2 * atr)

        elif method == 'trailing':
            # Trailing stop (same as fixed initially, will trail later)
            if side == OrderSide.BUY:
                stop_loss = entry_price * (1 - self.stop_loss_percent / 100)
            else:
                stop_loss = entry_price * (1 + self.stop_loss_percent / 100)

        else:
            # Default to fixed
            if side == OrderSide.BUY:
                stop_loss = entry_price * (1 - self.stop_loss_percent / 100)
            else:
                stop_loss = entry_price * (1 + self.stop_loss_percent / 100)

        return stop_loss

    async def calculate_take_profit(
        self,
        entry_price: float,
        side: OrderSide,
        risk_reward_ratio: float = 2.0
    ) -> float:
        """
        Calculate take profit price

        Args:
            entry_price: Entry price
            side: Order side (BUY or SELL)
            risk_reward_ratio: Risk-reward ratio (default 2:1)

        Returns:
            Take profit price
        """
        profit_percent = self.take_profit_percent

        if side == OrderSide.BUY:
            take_profit = entry_price * (1 + profit_percent / 100)
        else:
            take_profit = entry_price * (1 - profit_percent / 100)

        return take_profit

    async def update_trailing_stop(
        self,
        position: Position,
        current_price: float
    ) -> Optional[float]:
        """
        Update trailing stop loss

        Args:
            position: Position object
            current_price: Current market price

        Returns:
            New stop loss price or None if no update
        """
        if not position.trailing_stop:
            return None

        trailing_percent = settings.TRAILING_STOP_PERCENT / 100

        if position.side == OrderSide.BUY:
            # For long positions, trail stop up
            new_stop = current_price * (1 - trailing_percent)

            if new_stop > position.stop_loss:
                position.stop_loss = new_stop
                await self.db.commit()
                logger.info(f"Trailing stop updated for {position.symbol}: {new_stop}")
                return new_stop

        else:
            # For short positions, trail stop down
            new_stop = current_price * (1 + trailing_percent)

            if new_stop < position.stop_loss:
                position.stop_loss = new_stop
                await self.db.commit()
                logger.info(f"Trailing stop updated for {position.symbol}: {new_stop}")
                return new_stop

        return None

    async def check_daily_loss_limit(self) -> Dict[str, Any]:
        """Check if daily loss limit has been reached"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Get today's trades
        result = await self.db.execute(
            select(Trade)
            .where(
                Trade.user_id == self.user.id,
                Trade.closed_at >= today_start,
                Trade.is_open == False
            )
        )
        today_trades = result.scalars().all()

        # Calculate total P&L
        total_pnl = sum(trade.realized_pnl or 0 for trade in today_trades)

        # Get account balance (simplified - should get from Binance)
        account_balance = 10000  # TODO: Get real balance

        daily_loss_percent = (total_pnl / account_balance) * 100 if account_balance > 0 else 0

        limit_reached = daily_loss_percent <= -self.max_daily_loss_percent

        if limit_reached:
            await self._log_risk_event(
                event_type="MAX_DAILY_LOSS",
                severity="CRITICAL",
                description=f"Daily loss limit reached: {daily_loss_percent:.2f}%",
                threshold_value=self.max_daily_loss_percent,
                current_value=abs(daily_loss_percent)
            )

        return {
            'limit_reached': limit_reached,
            'daily_pnl': total_pnl,
            'daily_loss_percent': daily_loss_percent,
            'max_daily_loss_percent': self.max_daily_loss_percent,
            'trades_count': len(today_trades)
        }

    async def check_max_open_trades(self) -> Dict[str, Any]:
        """Check if maximum open trades limit has been reached"""
        result = await self.db.execute(
            select(func.count(Position.id))
            .where(
                Position.user_id == self.user.id,
                Position.is_open == True
            )
        )
        open_trades_count = result.scalar()

        limit_reached = open_trades_count >= self.max_open_trades

        if limit_reached:
            await self._log_risk_event(
                event_type="MAX_OPEN_TRADES",
                severity="HIGH",
                description=f"Maximum open trades reached: {open_trades_count}",
                threshold_value=self.max_open_trades,
                current_value=open_trades_count
            )

        return {
            'limit_reached': limit_reached,
            'open_trades_count': open_trades_count,
            'max_open_trades': self.max_open_trades,
            'available_slots': max(0, self.max_open_trades - open_trades_count)
        }

    async def check_position_limits(
        self,
        symbol: str,
        position_size: float,
        account_balance: float
    ) -> Dict[str, Any]:
        """Check if position size is within limits"""
        position_value = position_size  # Simplified
        max_position_value = account_balance * (self.max_position_size_percent / 100)

        exceeds_limit = position_value > max_position_value

        if exceeds_limit:
            await self._log_risk_event(
                event_type="POSITION_SIZE_LIMIT",
                severity="MEDIUM",
                symbol=symbol,
                description=f"Position size exceeds limit for {symbol}",
                threshold_value=max_position_value,
                current_value=position_value
            )

        return {
            'exceeds_limit': exceeds_limit,
            'position_value': position_value,
            'max_position_value': max_position_value,
            'position_percent': (position_value / account_balance * 100) if account_balance > 0 else 0
        }

    async def should_allow_trade(
        self,
        symbol: str,
        position_size: float,
        account_balance: float
    ) -> Dict[str, Any]:
        """
        Comprehensive check if trade should be allowed

        Returns:
            Dictionary with allowed status and reasons
        """
        checks = []

        # Check daily loss limit
        daily_loss_check = await self.check_daily_loss_limit()
        if daily_loss_check['limit_reached']:
            checks.append({
                'check': 'daily_loss_limit',
                'passed': False,
                'reason': f"Daily loss limit reached: {daily_loss_check['daily_loss_percent']:.2f}%"
            })

        # Check max open trades
        open_trades_check = await self.check_max_open_trades()
        if open_trades_check['limit_reached']:
            checks.append({
                'check': 'max_open_trades',
                'passed': False,
                'reason': f"Maximum open trades reached: {open_trades_check['open_trades_count']}"
            })

        # Check position size
        position_check = await self.check_position_limits(symbol, position_size, account_balance)
        if position_check['exceeds_limit']:
            checks.append({
                'check': 'position_size',
                'passed': False,
                'reason': f"Position size exceeds {self.max_position_size_percent}% of account"
            })

        # Determine if trade is allowed
        allowed = len([c for c in checks if not c['passed']]) == 0

        return {
            'allowed': allowed,
            'checks': checks,
            'daily_loss_status': daily_loss_check,
            'open_trades_status': open_trades_check,
            'position_size_status': position_check
        }

    async def _log_risk_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        threshold_value: Optional[float] = None,
        current_value: Optional[float] = None,
        symbol: Optional[str] = None
    ):
        """Log risk management event"""
        event = RiskEvent(
            user_id=self.user.id,
            event_type=event_type,
            severity=severity,
            symbol=symbol,
            description=description,
            threshold_value=threshold_value,
            current_value=current_value,
            resolved=False
        )

        self.db.add(event)
        await self.db.commit()
        logger.warning(f"Risk event logged: {event_type} - {description}")


class EmergencyShutdownService:
    """Emergency shutdown mechanism"""

    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.is_shutdown = False

    async def trigger_shutdown(self, reason: str) -> Dict[str, Any]:
        """
        Trigger emergency shutdown

        Args:
            reason: Reason for shutdown

        Returns:
            Shutdown status
        """
        logger.critical(f"EMERGENCY SHUTDOWN TRIGGERED: {reason}")

        self.is_shutdown = True

        # Log the event
        event = RiskEvent(
            user_id=self.user.id,
            event_type="EMERGENCY_SHUTDOWN",
            severity="CRITICAL",
            description=f"Emergency shutdown: {reason}",
            resolved=False
        )
        self.db.add(event)

        # Get all open positions
        result = await self.db.execute(
            select(Position).where(
                Position.user_id == self.user.id,
                Position.is_open == True
            )
        )
        open_positions = result.scalars().all()

        # TODO: Close all positions
        # For now, just log
        logger.info(f"Found {len(open_positions)} open positions to close")

        await self.db.commit()

        return {
            'shutdown_triggered': True,
            'reason': reason,
            'timestamp': datetime.utcnow(),
            'open_positions_count': len(open_positions)
        }

    async def check_shutdown_conditions(self) -> Optional[str]:
        """
        Check if emergency shutdown conditions are met

        Returns:
            Shutdown reason if conditions met, None otherwise
        """
        # Check daily loss
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        result = await self.db.execute(
            select(Trade)
            .where(
                Trade.user_id == self.user.id,
                Trade.closed_at >= today_start,
                Trade.is_open == False
            )
        )
        today_trades = result.scalars().all()

        total_pnl = sum(trade.realized_pnl or 0 for trade in today_trades)
        account_balance = 10000  # TODO: Get real balance

        daily_loss_percent = (total_pnl / account_balance) * 100 if account_balance > 0 else 0

        # Trigger shutdown if daily loss exceeds 2x the limit
        if daily_loss_percent <= -(settings.MAX_DAILY_LOSS_PERCENT * 2):
            return f"Critical daily loss: {daily_loss_percent:.2f}%"

        return None

    def reset_shutdown(self):
        """Reset shutdown state (manual override)"""
        self.is_shutdown = False
        logger.info("Emergency shutdown reset")