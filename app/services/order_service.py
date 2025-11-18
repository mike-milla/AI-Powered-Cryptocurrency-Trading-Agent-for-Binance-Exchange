from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid
import logging

from app.models.trade import Order, Trade, Position, OrderSide, OrderType, OrderStatus, TradeType
from app.models.audit import AuditLog, ActionType
from app.models.user import User
from app.services.binance_client import BinanceClientManager
from app.core.security import api_key_manager

logger = logging.getLogger(__name__)


class OrderExecutionService:
    """Service for executing trading orders"""

    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user

        # Decrypt API keys
        if user.encrypted_binance_api_key and user.encrypted_binance_api_secret:
            api_key, api_secret = api_key_manager.decrypt_api_credentials(
                user.encrypted_binance_api_key,
                user.encrypted_binance_api_secret
            )
            self.binance_manager = BinanceClientManager(
                api_key, api_secret, user.use_testnet
            )
        else:
            self.binance_manager = None
            logger.warning(f"User {user.username} has no Binance API keys configured")

    async def create_market_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        trade_type: TradeType = TradeType.SPOT,
        strategy_name: Optional[str] = None,
        ai_signal: bool = False,
        ai_confidence: Optional[float] = None
    ) -> Order:
        """Create and execute a market order"""
        if not self.binance_manager:
            raise ValueError("Binance API keys not configured")

        # Generate client order ID
        client_order_id = f"{self.user.id}_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"

        # Create order record
        order = Order(
            user_id=self.user.id,
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            trade_type=trade_type,
            quantity=quantity,
            status=OrderStatus.NEW,
            strategy_name=strategy_name,
            ai_signal=ai_signal,
            ai_confidence=ai_confidence
        )

        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        try:
            # Execute order on Binance
            if trade_type == TradeType.SPOT:
                result = await self.binance_manager.spot_client.create_market_order(
                    symbol=symbol,
                    side=side.value,
                    quantity=quantity
                )
            else:
                result = await self.binance_manager.futures_client.create_market_order(
                    symbol=symbol,
                    side=side.value.lower(),
                    quantity=quantity
                )

            # Update order with result
            order.binance_order_id = str(result.get('order_id') or result.get('id'))
            order.status = OrderStatus[result.get('status', 'FILLED')]
            order.executed_quantity = result.get('executed_quantity', quantity)
            order.executed_price = result.get('executed_price', 0)
            order.filled_at = datetime.utcnow()
            order.raw_response = result

            await self.db.commit()

            # Log action
            await self._log_action(ActionType.ORDER_PLACED, f"Market order placed: {symbol} {side.value} {quantity}")

            return order

        except Exception as e:
            logger.error(f"Error executing market order: {e}")
            order.status = OrderStatus.REJECTED
            await self.db.commit()
            raise

    async def create_limit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        trade_type: TradeType = TradeType.SPOT,
        strategy_name: Optional[str] = None,
        ai_signal: bool = False,
        ai_confidence: Optional[float] = None
    ) -> Order:
        """Create a limit order"""
        if not self.binance_manager:
            raise ValueError("Binance API keys not configured")

        client_order_id = f"{self.user.id}_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"

        order = Order(
            user_id=self.user.id,
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            order_type=OrderType.LIMIT,
            trade_type=trade_type,
            quantity=quantity,
            price=price,
            status=OrderStatus.NEW,
            strategy_name=strategy_name,
            ai_signal=ai_signal,
            ai_confidence=ai_confidence
        )

        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        try:
            if trade_type == TradeType.SPOT:
                result = await self.binance_manager.spot_client.create_limit_order(
                    symbol=symbol,
                    side=side.value,
                    quantity=quantity,
                    price=price
                )
            else:
                result = await self.binance_manager.futures_client.create_limit_order(
                    symbol=symbol,
                    side=side.value.lower(),
                    quantity=quantity,
                    price=price
                )

            order.binance_order_id = str(result.get('order_id') or result.get('id'))
            order.status = OrderStatus[result.get('status', 'NEW')]
            order.raw_response = result

            await self.db.commit()
            await self._log_action(ActionType.ORDER_PLACED, f"Limit order placed: {symbol} {side.value} {quantity}@{price}")

            return order

        except Exception as e:
            logger.error(f"Error executing limit order: {e}")
            order.status = OrderStatus.REJECTED
            await self.db.commit()
            raise

    async def create_stop_loss_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        stop_price: float,
        trade_type: TradeType = TradeType.SPOT
    ) -> Order:
        """Create a stop loss order"""
        if not self.binance_manager:
            raise ValueError("Binance API keys not configured")

        client_order_id = f"{self.user.id}_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"

        order = Order(
            user_id=self.user.id,
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            order_type=OrderType.STOP_LOSS,
            trade_type=trade_type,
            quantity=quantity,
            stop_price=stop_price,
            status=OrderStatus.NEW
        )

        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        try:
            result = await self.binance_manager.spot_client.create_stop_loss_order(
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                stop_price=stop_price
            )

            order.binance_order_id = str(result.get('order_id'))
            order.status = OrderStatus[result.get('status', 'NEW')]
            order.raw_response = result

            await self.db.commit()
            await self._log_action(ActionType.ORDER_PLACED, f"Stop loss order placed: {symbol}")

            return order

        except Exception as e:
            logger.error(f"Error creating stop loss order: {e}")
            order.status = OrderStatus.REJECTED
            await self.db.commit()
            raise

    async def create_oco_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        stop_price: float,
        stop_limit_price: float
    ) -> Dict[str, Any]:
        """Create OCO (One-Cancels-the-Other) order"""
        if not self.binance_manager:
            raise ValueError("Binance API keys not configured")

        try:
            result = await self.binance_manager.spot_client.create_oco_order(
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                stop_limit_price=stop_limit_price
            )

            await self._log_action(ActionType.ORDER_PLACED, f"OCO order placed: {symbol}")

            return result

        except Exception as e:
            logger.error(f"Error creating OCO order: {e}")
            raise

    async def cancel_order(self, order_id: int) -> Order:
        """Cancel an order"""
        result = await self.db.execute(
            select(Order).where(Order.id == order_id, Order.user_id == self.user.id)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError("Order not found")

        if order.status in [OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.EXPIRED]:
            raise ValueError(f"Cannot cancel order with status {order.status}")

        try:
            if order.trade_type == TradeType.SPOT:
                await self.binance_manager.spot_client.cancel_order(
                    symbol=order.symbol,
                    order_id=int(order.binance_order_id)
                )
            else:
                await self.binance_manager.futures_client.cancel_order(
                    order_id=order.binance_order_id,
                    symbol=order.symbol
                )

            order.status = OrderStatus.CANCELED
            await self.db.commit()

            await self._log_action(ActionType.ORDER_CANCELED, f"Order canceled: {order.symbol}")

            return order

        except Exception as e:
            logger.error(f"Error canceling order: {e}")
            raise

    async def get_order_status(self, order_id: int) -> Order:
        """Get current order status"""
        result = await self.db.execute(
            select(Order).where(Order.id == order_id, Order.user_id == self.user.id)
        )
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError("Order not found")

        if order.status not in [OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.EXPIRED]:
            try:
                if order.trade_type == TradeType.SPOT:
                    status_result = await self.binance_manager.spot_client.get_order_status(
                        symbol=order.symbol,
                        order_id=int(order.binance_order_id)
                    )
                    order.status = OrderStatus[status_result.get('status')]
                    order.executed_quantity = status_result.get('executed_quantity', 0)
                    order.executed_price = status_result.get('executed_price', 0)

                    await self.db.commit()

            except Exception as e:
                logger.error(f"Error getting order status: {e}")

        return order

    async def _log_action(self, action_type: ActionType, description: str):
        """Log action to audit trail"""
        log = AuditLog(
            user_id=self.user.id,
            action_type=action_type,
            action_description=description
        )
        self.db.add(log)
        await self.db.commit()