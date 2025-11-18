import pandas as pd
import numpy as np
from typing import List, Dict, Any


class CandlestickPatterns:
    """Recognize candlestick patterns"""

    @staticmethod
    def is_doji(row: pd.Series, threshold: float = 0.1) -> bool:
        """Detect Doji pattern"""
        body = abs(row['close'] - row['open'])
        range_size = row['high'] - row['low']

        if range_size == 0:
            return False

        return (body / range_size) < threshold

    @staticmethod
    def is_hammer(row: pd.Series) -> bool:
        """Detect Hammer pattern"""
        body = abs(row['close'] - row['open'])
        lower_shadow = min(row['open'], row['close']) - row['low']
        upper_shadow = row['high'] - max(row['open'], row['close'])

        if body == 0:
            return False

        return (lower_shadow > body * 2) and (upper_shadow < body * 0.3)

    @staticmethod
    def is_inverted_hammer(row: pd.Series) -> bool:
        """Detect Inverted Hammer pattern"""
        body = abs(row['close'] - row['open'])
        lower_shadow = min(row['open'], row['close']) - row['low']
        upper_shadow = row['high'] - max(row['open'], row['close'])

        if body == 0:
            return False

        return (upper_shadow > body * 2) and (lower_shadow < body * 0.3)

    @staticmethod
    def is_shooting_star(row: pd.Series) -> bool:
        """Detect Shooting Star pattern"""
        body = abs(row['close'] - row['open'])
        lower_shadow = min(row['open'], row['close']) - row['low']
        upper_shadow = row['high'] - max(row['open'], row['close'])

        if body == 0:
            return False

        return (upper_shadow > body * 2) and (lower_shadow < body * 0.3) and (row['close'] < row['open'])

    @staticmethod
    def is_engulfing_bullish(df: pd.DataFrame, idx: int) -> bool:
        """Detect Bullish Engulfing pattern"""
        if idx < 1:
            return False

        current = df.iloc[idx]
        previous = df.iloc[idx - 1]

        # Previous candle is bearish
        if previous['close'] >= previous['open']:
            return False

        # Current candle is bullish
        if current['close'] <= current['open']:
            return False

        # Current candle engulfs previous
        return (current['open'] < previous['close']) and (current['close'] > previous['open'])

    @staticmethod
    def is_engulfing_bearish(df: pd.DataFrame, idx: int) -> bool:
        """Detect Bearish Engulfing pattern"""
        if idx < 1:
            return False

        current = df.iloc[idx]
        previous = df.iloc[idx - 1]

        # Previous candle is bullish
        if previous['close'] <= previous['open']:
            return False

        # Current candle is bearish
        if current['close'] >= current['open']:
            return False

        # Current candle engulfs previous
        return (current['open'] > previous['close']) and (current['close'] < previous['open'])

    @staticmethod
    def is_morning_star(df: pd.DataFrame, idx: int) -> bool:
        """Detect Morning Star pattern"""
        if idx < 2:
            return False

        first = df.iloc[idx - 2]
        second = df.iloc[idx - 1]
        third = df.iloc[idx]

        # First candle is bearish
        if first['close'] >= first['open']:
            return False

        # Second candle is small (star)
        second_body = abs(second['close'] - second['open'])
        if second_body > abs(first['close'] - first['open']) * 0.3:
            return False

        # Third candle is bullish and closes above midpoint of first
        if third['close'] <= third['open']:
            return False

        midpoint = (first['open'] + first['close']) / 2
        return third['close'] > midpoint

    @staticmethod
    def is_evening_star(df: pd.DataFrame, idx: int) -> bool:
        """Detect Evening Star pattern"""
        if idx < 2:
            return False

        first = df.iloc[idx - 2]
        second = df.iloc[idx - 1]
        third = df.iloc[idx]

        # First candle is bullish
        if first['close'] <= first['open']:
            return False

        # Second candle is small (star)
        second_body = abs(second['close'] - second['open'])
        if second_body > abs(first['close'] - first['open']) * 0.3:
            return False

        # Third candle is bearish and closes below midpoint of first
        if third['close'] >= third['open']:
            return False

        midpoint = (first['open'] + first['close']) / 2
        return third['close'] < midpoint

    @staticmethod
    def detect_all_patterns(df: pd.DataFrame) -> Dict[str, Any]:
        """Detect all candlestick patterns"""
        if len(df) < 3:
            return {'patterns': []}

        patterns = []
        idx = len(df) - 1
        current = df.iloc[idx]

        # Single candle patterns
        if CandlestickPatterns.is_doji(current):
            patterns.append({'name': 'Doji', 'type': 'neutral', 'strength': 'medium'})

        if CandlestickPatterns.is_hammer(current):
            patterns.append({'name': 'Hammer', 'type': 'bullish', 'strength': 'strong'})

        if CandlestickPatterns.is_inverted_hammer(current):
            patterns.append({'name': 'Inverted Hammer', 'type': 'bullish', 'strength': 'medium'})

        if CandlestickPatterns.is_shooting_star(current):
            patterns.append({'name': 'Shooting Star', 'type': 'bearish', 'strength': 'strong'})

        # Multi-candle patterns
        if CandlestickPatterns.is_engulfing_bullish(df, idx):
            patterns.append({'name': 'Bullish Engulfing', 'type': 'bullish', 'strength': 'very_strong'})

        if CandlestickPatterns.is_engulfing_bearish(df, idx):
            patterns.append({'name': 'Bearish Engulfing', 'type': 'bearish', 'strength': 'very_strong'})

        if CandlestickPatterns.is_morning_star(df, idx):
            patterns.append({'name': 'Morning Star', 'type': 'bullish', 'strength': 'very_strong'})

        if CandlestickPatterns.is_evening_star(df, idx):
            patterns.append({'name': 'Evening Star', 'type': 'bearish', 'strength': 'very_strong'})

        return {
            'patterns': patterns,
            'bullish_count': sum(1 for p in patterns if p['type'] == 'bullish'),
            'bearish_count': sum(1 for p in patterns if p['type'] == 'bearish')
        }


class ChartPatterns:
    """Recognize chart patterns"""

    @staticmethod
    def find_support_resistance(df: pd.DataFrame, window: int = 20) -> Dict[str, List[float]]:
        """Find support and resistance levels"""
        # Find local minima (support) and maxima (resistance)
        df_copy = df.copy()

        # Rolling window for local extrema
        df_copy['local_min'] = df_copy['low'].rolling(window=window, center=True).min()
        df_copy['local_max'] = df_copy['high'].rolling(window=window, center=True).max()

        support_levels = []
        resistance_levels = []

        for i in range(window, len(df_copy) - window):
            # Support levels
            if df_copy['low'].iloc[i] == df_copy['local_min'].iloc[i]:
                support_levels.append(df_copy['low'].iloc[i])

            # Resistance levels
            if df_copy['high'].iloc[i] == df_copy['local_max'].iloc[i]:
                resistance_levels.append(df_copy['high'].iloc[i])

        # Cluster nearby levels
        support_levels = ChartPatterns._cluster_levels(support_levels)
        resistance_levels = ChartPatterns._cluster_levels(resistance_levels)

        return {
            'support': support_levels[:5],  # Top 5 support levels
            'resistance': resistance_levels[:5]  # Top 5 resistance levels
        }

    @staticmethod
    def _cluster_levels(levels: List[float], threshold: float = 0.02) -> List[float]:
        """Cluster nearby price levels"""
        if not levels:
            return []

        levels_sorted = sorted(levels)
        clustered = []
        current_cluster = [levels_sorted[0]]

        for level in levels_sorted[1:]:
            if (level - current_cluster[-1]) / current_cluster[-1] < threshold:
                current_cluster.append(level)
            else:
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]

        if current_cluster:
            clustered.append(np.mean(current_cluster))

        return clustered

    @staticmethod
    def detect_trend(df: pd.DataFrame, period: int = 20) -> Dict[str, Any]:
        """Detect trend direction and strength"""
        # Calculate trend using linear regression
        if len(df) < period:
            return {'trend': 'insufficient_data', 'strength': 0}

        recent_df = df.tail(period).copy()
        recent_df['x'] = range(len(recent_df))

        # Linear regression on closing prices
        x = recent_df['x'].values
        y = recent_df['close'].values

        slope, intercept = np.polyfit(x, y, 1)

        # Normalize slope
        avg_price = y.mean()
        normalized_slope = (slope / avg_price) * 100

        # Determine trend
        if normalized_slope > 0.5:
            trend = 'strong_uptrend'
            strength = min(abs(normalized_slope) / 2, 1.0)
        elif normalized_slope > 0.1:
            trend = 'uptrend'
            strength = min(abs(normalized_slope), 0.7)
        elif normalized_slope < -0.5:
            trend = 'strong_downtrend'
            strength = min(abs(normalized_slope) / 2, 1.0)
        elif normalized_slope < -0.1:
            trend = 'downtrend'
            strength = min(abs(normalized_slope), 0.7)
        else:
            trend = 'sideways'
            strength = 0.3

        return {
            'trend': trend,
            'strength': strength,
            'slope': slope,
            'normalized_slope': normalized_slope
        }

    @staticmethod
    def detect_double_top(df: pd.DataFrame, tolerance: float = 0.02) -> bool:
        """Detect double top pattern"""
        if len(df) < 50:
            return False

        recent = df.tail(50)
        peaks = []

        for i in range(10, len(recent) - 10):
            if recent['high'].iloc[i] == recent['high'].iloc[i-10:i+10].max():
                peaks.append(recent['high'].iloc[i])

        if len(peaks) < 2:
            return False

        # Check if last two peaks are similar
        last_two = peaks[-2:]
        if abs(last_two[0] - last_two[1]) / last_two[0] < tolerance:
            return True

        return False

    @staticmethod
    def detect_double_bottom(df: pd.DataFrame, tolerance: float = 0.02) -> bool:
        """Detect double bottom pattern"""
        if len(df) < 50:
            return False

        recent = df.tail(50)
        troughs = []

        for i in range(10, len(recent) - 10):
            if recent['low'].iloc[i] == recent['low'].iloc[i-10:i+10].min():
                troughs.append(recent['low'].iloc[i])

        if len(troughs) < 2:
            return False

        # Check if last two troughs are similar
        last_two = troughs[-2:]
        if abs(last_two[0] - last_two[1]) / last_two[0] < tolerance:
            return True

        return False

    @staticmethod
    def detect_head_and_shoulders(df: pd.DataFrame) -> bool:
        """Detect head and shoulders pattern (simplified)"""
        if len(df) < 60:
            return False

        recent = df.tail(60)
        peaks = []

        for i in range(15, len(recent) - 15):
            if recent['high'].iloc[i] == recent['high'].iloc[i-15:i+15].max():
                peaks.append((i, recent['high'].iloc[i]))

        if len(peaks) < 3:
            return False

        # Check if middle peak is higher than shoulders
        last_three = peaks[-3:]
        head = last_three[1][1]
        left_shoulder = last_three[0][1]
        right_shoulder = last_three[2][1]

        # Head should be higher, shoulders should be similar
        if head > left_shoulder and head > right_shoulder:
            if abs(left_shoulder - right_shoulder) / left_shoulder < 0.05:
                return True

        return False