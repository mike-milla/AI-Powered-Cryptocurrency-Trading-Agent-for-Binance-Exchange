from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import pandas as pd

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.ml.trading_engine import AITradingEngine
from app.services.market_data_service import MarketDataService

router = APIRouter(prefix="/ai", tags=["AI Trading"])


class AnalysisRequest(BaseModel):
    symbol: str
    timeframe: str = "1h"
    limit: int = 100


class AutonomyUpdateRequest(BaseModel):
    autonomy_level: str  # 'full-auto', 'semi-auto', 'signal-only'


@router.post("/analyze")
async def analyze_market(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Run AI market analysis"""
    # Get market data
    market_service = MarketDataService(db)
    candles = await market_service.get_candles(
        request.symbol,
        request.timeframe,
        request.limit
    )

    if len(candles) < 50:
        raise HTTPException(
            status_code=400,
            detail="Insufficient market data for analysis"
        )

    # Convert to DataFrame
    df = pd.DataFrame([{
        'timestamp': c.timestamp,
        'open': c.open,
        'high': c.high,
        'low': c.low,
        'close': c.close,
        'volume': c.volume
    } for c in candles])

    # Run AI analysis
    ai_engine = AITradingEngine(db, current_user)
    analysis = await ai_engine.analyze_market(df, request.symbol)

    return analysis


@router.post("/decision")
async def get_trading_decision(
    request: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get AI trading decision"""
    # Get market data
    market_service = MarketDataService(db)
    candles = await market_service.get_candles(
        request.symbol,
        request.timeframe,
        request.limit
    )

    if len(candles) < 50:
        raise HTTPException(
            status_code=400,
            detail="Insufficient market data for decision making"
        )

    # Convert to DataFrame
    df = pd.DataFrame([{
        'timestamp': c.timestamp,
        'open': c.open,
        'high': c.high,
        'low': c.low,
        'close': c.close,
        'volume': c.volume
    } for c in candles])

    # Run complete analysis cycle
    ai_engine = AITradingEngine(db, current_user)
    result = await ai_engine.run_analysis_cycle(df, request.symbol)

    return result


@router.post("/autonomy")
async def update_autonomy_level(
    request: AutonomyUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update AI autonomy level"""
    valid_levels = ['full-auto', 'semi-auto', 'signal-only']

    if request.autonomy_level not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid autonomy level. Must be one of: {', '.join(valid_levels)}"
        )

    # Update in config (TODO: Store per user in database)
    return {
        "message": "Autonomy level updated",
        "autonomy_level": request.autonomy_level
    }


@router.get("/signals/{symbol}")
async def get_ai_signals(
    symbol: str,
    timeframe: str = "1h",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get latest AI signals for a symbol"""
    from app.utils.technical_indicators import TechnicalIndicators

    # Get market data
    market_service = MarketDataService(db)
    candles = await market_service.get_candles(symbol, timeframe, 100)

    if len(candles) < 50:
        raise HTTPException(
            status_code=400,
            detail="Insufficient market data"
        )

    # Convert to DataFrame
    df = pd.DataFrame([{
        'timestamp': c.timestamp,
        'open': c.open,
        'high': c.high,
        'low': c.low,
        'close': c.close,
        'volume': c.volume
    } for c in candles])

    # Generate signals
    signals = TechnicalIndicators.generate_signals(df)

    return signals