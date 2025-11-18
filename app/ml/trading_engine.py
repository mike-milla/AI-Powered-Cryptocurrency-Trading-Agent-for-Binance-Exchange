import pandas as pd
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.price_prediction import EnsemblePricePredictor
from app.utils.technical_indicators import TechnicalIndicators
from app.utils.pattern_recognition import CandlestickPatterns, ChartPatterns
from app.models.audit import AIDecisionLog
from app.models.user import User
from config import settings

logger = logging.getLogger(__name__)


class AITradingEngine:
    """AI-powered trading decision engine with adjustable autonomy"""

    def __init__(
        self,
        db: AsyncSession,
        user: User,
        autonomy_level: str = "semi-auto"
    ):
        """
        Initialize AI Trading Engine

        Args:
            db: Database session
            user: User object
            autonomy_level: 'full-auto', 'semi-auto', or 'signal-only'
        """
        self.db = db
        self.user = user
        self.autonomy_level = autonomy_level

        # Initialize ML models
        self.price_predictor = EnsemblePricePredictor(
            sequence_length=60,
            model_path=settings.ML_MODEL_PATH
        )

        # Decision weights
        self.weights = {
            'ml_prediction': 0.35,
            'technical_indicators': 0.30,
            'candlestick_patterns': 0.15,
            'chart_patterns': 0.10,
            'volume_analysis': 0.10
        }

    async def analyze_market(
        self,
        df: pd.DataFrame,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Comprehensive market analysis

        Args:
            df: DataFrame with OHLCV data
            symbol: Trading symbol

        Returns:
            Complete market analysis
        """
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.utcnow(),
            'current_price': float(df['close'].iloc[-1])
        }

        # 1. ML Price Prediction
        try:
            ml_prediction = self.price_predictor.predict(df)
            analysis['ml_prediction'] = ml_prediction
        except Exception as e:
            logger.warning(f"ML prediction failed: {e}")
            analysis['ml_prediction'] = {
                'confidence': 0,
                'direction': 'UNKNOWN',
                'predicted_change_percent': 0
            }

        # 2. Technical Indicators
        technical_signals = TechnicalIndicators.generate_signals(df)
        analysis['technical_indicators'] = technical_signals

        # 3. Candlestick Patterns
        candlestick_patterns = CandlestickPatterns.detect_all_patterns(df)
        analysis['candlestick_patterns'] = candlestick_patterns

        # 4. Chart Patterns
        support_resistance = ChartPatterns.find_support_resistance(df)
        trend_info = ChartPatterns.detect_trend(df)
        analysis['chart_patterns'] = {
            'support_resistance': support_resistance,
            'trend': trend_info,
            'double_top': ChartPatterns.detect_double_top(df),
            'double_bottom': ChartPatterns.detect_double_bottom(df),
            'head_and_shoulders': ChartPatterns.detect_head_and_shoulders(df)
        }

        # 5. Volume Analysis
        volume_analysis = TechnicalIndicators.calculate_volume_analysis(df)
        analysis['volume_analysis'] = volume_analysis

        return analysis

    def make_trading_decision(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make trading decision based on analysis

        Args:
            analysis: Market analysis from analyze_market()

        Returns:
            Trading decision with confidence and reasoning
        """
        scores = {
            'BUY': 0.0,
            'SELL': 0.0,
            'HOLD': 0.0
        }

        reasoning = []

        # 1. ML Prediction Score
        ml_pred = analysis.get('ml_prediction', {})
        ml_confidence = ml_pred.get('confidence', 0)
        ml_direction = ml_pred.get('direction', 'UNKNOWN')

        if ml_direction == 'UP':
            scores['BUY'] += self.weights['ml_prediction'] * ml_confidence
            reasoning.append(f"ML predicts {ml_pred.get('predicted_change_percent', 0):.2f}% increase (conf: {ml_confidence:.2f})")
        elif ml_direction == 'DOWN':
            scores['SELL'] += self.weights['ml_prediction'] * ml_confidence
            reasoning.append(f"ML predicts {ml_pred.get('predicted_change_percent', 0):.2f}% decrease (conf: {ml_confidence:.2f})")

        # 2. Technical Indicators Score
        tech_signals = analysis.get('technical_indicators', {}).get('signals', {})
        tech_overall = analysis.get('technical_indicators', {}).get('overall_signal', 'HOLD')
        tech_strength = analysis.get('technical_indicators', {}).get('signal_strength', 0.5)

        if tech_overall == 'BUY':
            scores['BUY'] += self.weights['technical_indicators'] * tech_strength
            reasoning.append(f"Technical indicators suggest BUY (strength: {tech_strength:.2f})")
        elif tech_overall == 'SELL':
            scores['SELL'] += self.weights['technical_indicators'] * tech_strength
            reasoning.append(f"Technical indicators suggest SELL (strength: {tech_strength:.2f})")
        else:
            scores['HOLD'] += self.weights['technical_indicators']

        # 3. Candlestick Patterns Score
        candle_patterns = analysis.get('candlestick_patterns', {})
        bullish_count = candle_patterns.get('bullish_count', 0)
        bearish_count = candle_patterns.get('bearish_count', 0)

        if bullish_count > bearish_count:
            pattern_score = min(bullish_count * 0.1, self.weights['candlestick_patterns'])
            scores['BUY'] += pattern_score
            reasoning.append(f"Detected {bullish_count} bullish candlestick patterns")
        elif bearish_count > bullish_count:
            pattern_score = min(bearish_count * 0.1, self.weights['candlestick_patterns'])
            scores['SELL'] += pattern_score
            reasoning.append(f"Detected {bearish_count} bearish candlestick patterns")

        # 4. Chart Patterns Score
        chart_patterns = analysis.get('chart_patterns', {})
        trend = chart_patterns.get('trend', {}).get('trend', 'sideways')
        trend_strength = chart_patterns.get('trend', {}).get('strength', 0)

        if 'uptrend' in trend:
            scores['BUY'] += self.weights['chart_patterns'] * trend_strength
            reasoning.append(f"Chart shows {trend} (strength: {trend_strength:.2f})")
        elif 'downtrend' in trend:
            scores['SELL'] += self.weights['chart_patterns'] * trend_strength
            reasoning.append(f"Chart shows {trend} (strength: {trend_strength:.2f})")

        if chart_patterns.get('double_bottom'):
            scores['BUY'] += 0.05
            reasoning.append("Double bottom pattern detected (bullish)")
        if chart_patterns.get('double_top'):
            scores['SELL'] += 0.05
            reasoning.append("Double top pattern detected (bearish)")

        # 5. Volume Analysis Score
        volume_info = analysis.get('volume_analysis', {})
        if volume_info.get('high_volume'):
            # High volume confirms the trend
            if scores['BUY'] > scores['SELL']:
                scores['BUY'] += self.weights['volume_analysis']
                reasoning.append("High volume confirms bullish sentiment")
            elif scores['SELL'] > scores['BUY']:
                scores['SELL'] += self.weights['volume_analysis']
                reasoning.append("High volume confirms bearish sentiment")

        # Normalize scores
        total_score = sum(scores.values())
        if total_score > 0:
            for key in scores:
                scores[key] /= total_score

        # Make final decision
        max_score = max(scores.values())
        decision = max(scores, key=scores.get)

        # Require minimum confidence threshold
        if max_score < settings.PREDICTION_CONFIDENCE_THRESHOLD:
            decision = 'HOLD'
            reasoning.append(f"Confidence {max_score:.2f} below threshold {settings.PREDICTION_CONFIDENCE_THRESHOLD}")

        return {
            'decision': decision,
            'confidence': max_score,
            'scores': scores,
            'reasoning': reasoning,
            'analysis_summary': {
                'ml_direction': ml_direction,
                'technical_signal': tech_overall,
                'trend': trend,
                'patterns_bullish': bullish_count,
                'patterns_bearish': bearish_count
            }
        }

    async def execute_decision(
        self,
        decision: Dict[str, Any],
        symbol: str,
        analysis: Dict[str, Any]
    ) -> Optional[str]:
        """
        Execute trading decision based on autonomy level

        Args:
            decision: Trading decision from make_trading_decision()
            symbol: Trading symbol
            analysis: Market analysis

        Returns:
            Action taken or None
        """
        action_taken = None

        # Log the AI decision
        await self._log_decision(symbol, decision, analysis)

        if self.autonomy_level == "signal-only":
            # Only generate signals, no execution
            logger.info(f"Signal-only mode: {decision['decision']} signal generated for {symbol}")
            action_taken = "SIGNAL_GENERATED"

        elif self.autonomy_level == "semi-auto":
            # Generate signal and queue for manual approval
            logger.info(f"Semi-auto mode: {decision['decision']} signal queued for approval for {symbol}")
            action_taken = "QUEUED_FOR_APPROVAL"
            # TODO: Implement approval queue

        elif self.autonomy_level == "full-auto":
            # Automatically execute if confidence is high enough
            if decision['confidence'] >= settings.PREDICTION_CONFIDENCE_THRESHOLD:
                logger.info(f"Full-auto mode: Executing {decision['decision']} for {symbol}")
                action_taken = "ORDER_PLACED"
                # TODO: Place actual order through OrderExecutionService
            else:
                logger.info(f"Full-auto mode: Confidence too low, no action taken for {symbol}")
                action_taken = "IGNORED_LOW_CONFIDENCE"

        return action_taken

    async def _log_decision(
        self,
        symbol: str,
        decision: Dict[str, Any],
        analysis: Dict[str, Any]
    ):
        """Log AI decision to database"""
        log = AIDecisionLog(
            user_id=self.user.id,
            symbol=symbol,
            timeframe=analysis.get('timeframe', '1h'),
            decision=decision['decision'],
            confidence=decision['confidence'],
            reasoning="\n".join(decision['reasoning']),
            indicators_used=decision.get('analysis_summary'),
            indicator_values={
                'technical': analysis.get('technical_indicators'),
                'ml_prediction': analysis.get('ml_prediction')
            },
            ml_prediction=analysis.get('ml_prediction', {}).get('predicted_change_percent'),
            patterns_detected=analysis.get('candlestick_patterns', {}).get('patterns'),
            action_taken=None  # Will be updated after execution
        )

        self.db.add(log)
        await self.db.commit()

    def update_autonomy_level(self, new_level: str):
        """Update autonomy level"""
        if new_level not in ['full-auto', 'semi-auto', 'signal-only']:
            raise ValueError("Invalid autonomy level")

        self.autonomy_level = new_level
        logger.info(f"Autonomy level updated to: {new_level}")

    async def run_analysis_cycle(
        self,
        df: pd.DataFrame,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Run complete analysis and decision cycle

        Args:
            df: Market data DataFrame
            symbol: Trading symbol

        Returns:
            Complete cycle results
        """
        # Step 1: Analyze market
        analysis = await self.analyze_market(df, symbol)

        # Step 2: Make decision
        decision = self.make_trading_decision(analysis)

        # Step 3: Execute based on autonomy level
        action = await self.execute_decision(decision, symbol, analysis)

        return {
            'symbol': symbol,
            'timestamp': datetime.utcnow(),
            'analysis': analysis,
            'decision': decision,
            'action_taken': action,
            'autonomy_level': self.autonomy_level
        }