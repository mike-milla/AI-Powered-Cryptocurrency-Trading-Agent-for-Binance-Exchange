import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any
import pandas_ta as ta


class TechnicalIndicators:
    """Calculate technical indicators for trading signals"""

    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
        """Calculate Simple Moving Average"""
        return df[column].rolling(window=period).mean()

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
        """Calculate Exponential Moving Average"""
        return df[column].ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = df[column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def calculate_rsi_divergence(df: pd.DataFrame, rsi: pd.Series) -> Dict[str, bool]:
        """Detect RSI divergences"""
        # Simplified divergence detection
        bullish_divergence = False
        bearish_divergence = False

        if len(df) > 30:
            # Check last 30 bars for divergence patterns
            price_lows = df['close'].tail(30).rolling(window=5).min()
            rsi_lows = rsi.tail(30).rolling(window=5).min()

            # Bullish divergence: price making lower lows, RSI making higher lows
            if price_lows.iloc[-1] < price_lows.iloc[-10] and rsi_lows.iloc[-1] > rsi_lows.iloc[-10]:
                bullish_divergence = True

            # Bearish divergence: price making higher highs, RSI making lower highs
            price_highs = df['close'].tail(30).rolling(window=5).max()
            rsi_highs = rsi.tail(30).rolling(window=5).max()

            if price_highs.iloc[-1] > price_highs.iloc[-10] and rsi_highs.iloc[-1] < rsi_highs.iloc[-10]:
                bearish_divergence = True

        return {
            'bullish_divergence': bullish_divergence,
            'bearish_divergence': bearish_divergence
        }

    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = 'close'
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_fast = df[column].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df[column].ewm(span=slow_period, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        column: str = 'close'
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands"""
        middle_band = df[column].rolling(window=period).mean()
        std = df[column].rolling(window=period).std()

        upper_band = middle_band + (std_dev * std)
        lower_band = middle_band - (std_dev * std)

        return upper_band, middle_band, lower_band

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range (volatility indicator)"""
        high = df['high']
        low = df['low']
        close = df['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()

        return atr

    @staticmethod
    def calculate_volume_analysis(df: pd.DataFrame, period: int = 20) -> Dict[str, Any]:
        """Analyze volume patterns"""
        avg_volume = df['volume'].rolling(window=period).mean()
        current_volume = df['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume.iloc[-1] if avg_volume.iloc[-1] > 0 else 1

        return {
            'current_volume': current_volume,
            'average_volume': avg_volume.iloc[-1],
            'volume_ratio': volume_ratio,
            'high_volume': volume_ratio > 1.5,
            'low_volume': volume_ratio < 0.5
        }

    @staticmethod
    def calculate_stochastic(
        df: pd.DataFrame,
        k_period: int = 14,
        d_period: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """Calculate Stochastic Oscillator"""
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()

        k_percent = 100 * ((df['close'] - low_min) / (high_max - low_min))
        d_percent = k_percent.rolling(window=d_period).mean()

        return k_percent, d_percent

    @staticmethod
    def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index (trend strength)"""
        high = df['high']
        low = df['low']
        close = df['close']

        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        tr = TechnicalIndicators.calculate_atr(df, period)

        plus_di = 100 * (plus_dm.rolling(window=period).mean() / tr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / tr)

        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()

        return adx

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators at once"""
        result_df = df.copy()

        # Moving Averages
        result_df['sma_50'] = TechnicalIndicators.calculate_sma(df, 50)
        result_df['sma_100'] = TechnicalIndicators.calculate_sma(df, 100)
        result_df['sma_200'] = TechnicalIndicators.calculate_sma(df, 200)

        result_df['ema_12'] = TechnicalIndicators.calculate_ema(df, 12)
        result_df['ema_26'] = TechnicalIndicators.calculate_ema(df, 26)
        result_df['ema_50'] = TechnicalIndicators.calculate_ema(df, 50)

        # RSI
        result_df['rsi'] = TechnicalIndicators.calculate_rsi(df, 14)

        # MACD
        macd, signal, histogram = TechnicalIndicators.calculate_macd(df)
        result_df['macd'] = macd
        result_df['macd_signal'] = signal
        result_df['macd_histogram'] = histogram

        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.calculate_bollinger_bands(df)
        result_df['bb_upper'] = bb_upper
        result_df['bb_middle'] = bb_middle
        result_df['bb_lower'] = bb_lower

        # ATR
        result_df['atr'] = TechnicalIndicators.calculate_atr(df, 14)

        # Stochastic
        k, d = TechnicalIndicators.calculate_stochastic(df)
        result_df['stoch_k'] = k
        result_df['stoch_d'] = d

        # ADX
        result_df['adx'] = TechnicalIndicators.calculate_adx(df, 14)

        return result_df

    @staticmethod
    def generate_signals(df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading signals based on indicators"""
        df_with_indicators = TechnicalIndicators.calculate_all_indicators(df)

        latest = df_with_indicators.iloc[-1]

        signals = {
            'timestamp': df.index[-1],
            'price': latest['close'],
            'signals': {}
        }

        # RSI signals
        if latest['rsi'] < 30:
            signals['signals']['rsi'] = 'oversold_buy'
        elif latest['rsi'] > 70:
            signals['signals']['rsi'] = 'overbought_sell'
        else:
            signals['signals']['rsi'] = 'neutral'

        # MACD signals
        if latest['macd'] > latest['macd_signal']:
            signals['signals']['macd'] = 'bullish'
        else:
            signals['signals']['macd'] = 'bearish'

        # Moving Average signals
        if latest['close'] > latest['sma_50'] > latest['sma_200']:
            signals['signals']['ma_trend'] = 'strong_uptrend'
        elif latest['close'] < latest['sma_50'] < latest['sma_200']:
            signals['signals']['ma_trend'] = 'strong_downtrend'
        else:
            signals['signals']['ma_trend'] = 'sideways'

        # Bollinger Bands signals
        if latest['close'] < latest['bb_lower']:
            signals['signals']['bollinger'] = 'oversold'
        elif latest['close'] > latest['bb_upper']:
            signals['signals']['bollinger'] = 'overbought'
        else:
            signals['signals']['bollinger'] = 'neutral'

        # Stochastic signals
        if latest['stoch_k'] < 20 and latest['stoch_d'] < 20:
            signals['signals']['stochastic'] = 'oversold'
        elif latest['stoch_k'] > 80 and latest['stoch_d'] > 80:
            signals['signals']['stochastic'] = 'overbought'
        else:
            signals['signals']['stochastic'] = 'neutral'

        # Overall signal strength
        buy_signals = sum(1 for s in signals['signals'].values()
                         if 'buy' in str(s).lower() or 'oversold' in str(s).lower() or 'bullish' in str(s).lower())
        sell_signals = sum(1 for s in signals['signals'].values()
                          if 'sell' in str(s).lower() or 'overbought' in str(s).lower() or 'bearish' in str(s).lower())

        if buy_signals > sell_signals:
            signals['overall_signal'] = 'BUY'
            signals['signal_strength'] = buy_signals / len(signals['signals'])
        elif sell_signals > buy_signals:
            signals['overall_signal'] = 'SELL'
            signals['signal_strength'] = sell_signals / len(signals['signals'])
        else:
            signals['overall_signal'] = 'HOLD'
            signals['signal_strength'] = 0.5

        return signals