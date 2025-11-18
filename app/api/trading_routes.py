from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.trade import OrderSide, TradeType
from app.services.order_service import OrderExecutionService
from app.services.risk_management import RiskManagementService, EmergencyShutdownService

router = APIRouter(prefix="/trading", tags=["Trading"])


class MarketOrderRequest(BaseModel):
    symbol: str
    side: OrderSide
    quantity: float
    trade_type: TradeType = TradeType.SPOT


class LimitOrderRequest(BaseModel):
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    trade_type: TradeType = TradeType.SPOT


class StopLossOrderRequest(BaseModel):
    symbol: str
    side: OrderSide
    quantity: float
    stop_price: float
    trade_type: TradeType = TradeType.SPOT


@router.post("/orders/market")
async def create_market_order(
    order_request: MarketOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a market order"""
    order_service = OrderExecutionService(db, current_user)

    # Check risk management
    risk_service = RiskManagementService(db, current_user)
    risk_check = await risk_service.should_allow_trade(
        order_request.symbol,
        order_request.quantity,
        10000  # TODO: Get real account balance
    )

    if not risk_check['allowed']:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Trade not allowed by risk management",
                "checks": risk_check['checks']
            }
        )

    try:
        order = await order_service.create_market_order(
            symbol=order_request.symbol,
            side=order_request.side,
            quantity=order_request.quantity,
            trade_type=order_request.trade_type
        )

        return {
            "order_id": order.id,
            "binance_order_id": order.binance_order_id,
            "symbol": order.symbol,
            "side": order.side,
            "status": order.status,
            "quantity": order.quantity,
            "executed_quantity": order.executed_quantity,
            "executed_price": order.executed_price
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/orders/limit")
async def create_limit_order(
    order_request: LimitOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a limit order"""
    order_service = OrderExecutionService(db, current_user)

    try:
        order = await order_service.create_limit_order(
            symbol=order_request.symbol,
            side=order_request.side,
            quantity=order_request.quantity,
            price=order_request.price,
            trade_type=order_request.trade_type
        )

        return {
            "order_id": order.id,
            "binance_order_id": order.binance_order_id,
            "symbol": order.symbol,
            "side": order.side,
            "status": order.status,
            "price": order.price,
            "quantity": order.quantity
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel an order"""
    order_service = OrderExecutionService(db, current_user)

    try:
        order = await order_service.cancel_order(order_id)
        return {
            "message": "Order canceled successfully",
            "order_id": order.id,
            "status": order.status
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/orders/{order_id}")
async def get_order_status(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get order status"""
    order_service = OrderExecutionService(db, current_user)

    try:
        order = await order_service.get_order_status(order_id)
        return {
            "order_id": order.id,
            "symbol": order.symbol,
            "side": order.side,
            "status": order.status,
            "quantity": order.quantity,
            "executed_quantity": order.executed_quantity,
            "price": order.price
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/emergency-shutdown")
async def trigger_emergency_shutdown(
    reason: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trigger emergency shutdown"""
    shutdown_service = EmergencyShutdownService(db, current_user)

    result = await shutdown_service.trigger_shutdown(reason)

    return result


@router.get("/risk-status")
async def get_risk_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current risk management status"""
    risk_service = RiskManagementService(db, current_user)

    daily_loss = await risk_service.check_daily_loss_limit()
    open_trades = await risk_service.check_max_open_trades()

    return {
        "daily_loss_status": daily_loss,
        "open_trades_status": open_trades
    }