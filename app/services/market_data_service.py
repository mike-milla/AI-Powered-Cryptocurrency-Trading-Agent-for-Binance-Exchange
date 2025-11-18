import asyncio
import websockets
import json
from typing import Dict, List, Callable, Optional
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.market_data import Candle, MarketTicker, OrderBook
from app.core.database import get_redis

logger = logging.getLogger(__name__)


class MarketDataStreamer:
    """Real-time market data streaming using Binance WebSocket"""

    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        if testnet:
            self.ws_base_url = "wss://testnet.binance.vision/ws"
        else:
            self.ws_base_url = "wss://stream.binance.com:9443/ws"

        self.connections: Dict[str, asyncio.Task] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self.running = False

    async def subscribe_ticker(self, symbol: str, callback: Callable):
        """Subscribe to real-time ticker updates"""
        stream_name = f"{symbol.lower()}@ticker"

        if stream_name not in self.callbacks:
            self.callbacks[stream_name] = []
        self.callbacks[stream_name].append(callback)

        if stream_name not in self.connections:
            task = asyncio.create_task(self._connect_stream(stream_name))
            self.connections[stream_name] = task

    async def subscribe_kline(self, symbol: str, interval: str, callback: Callable):
        """Subscribe to real-time candlestick updates"""
        stream_name = f"{symbol.lower()}@kline_{interval}"

        if stream_name not in self.callbacks:
            self.callbacks[stream_name] = []
        self.callbacks[stream_name].append(callback)

        if stream_name not in self.connections:
            task = asyncio.create_task(self._connect_stream(stream_name))
            self.connections[stream_name] = task

    async def subscribe_depth(self, symbol: str, callback: Callable):
        """Subscribe to order book depth updates"""
        stream_name = f"{symbol.lower()}@depth"

        if stream_name not in self.callbacks:
            self.callbacks[stream_name] = []
        self.callbacks[stream_name].append(callback)

        if stream_name not in self.connections:
            task = asyncio.create_task(self._connect_stream(stream_name))
            self.connections[stream_name] = task

    async def subscribe_trades(self, symbol: str, callback: Callable):
        """Subscribe to real-time trade updates"""
        stream_name = f"{symbol.lower()}@trade"

        if stream_name not in self.callbacks:
            self.callbacks[stream_name] = []
        self.callbacks[stream_name].append(callback)

        if stream_name not in self.connections:
            task = asyncio.create_task(self._connect_stream(stream_name))
            self.connections[stream_name] = task

    async def _connect_stream(self, stream_name: str):
        """Connect to a WebSocket stream"""
        url = f"{self.ws_base_url}/{stream_name}"

        while self.running:
            try:
                async with websockets.connect(url) as websocket:
                    logger.info(f"Connected to stream: {stream_name}")

                    async for message in websocket:
                        data = json.loads(message)

                        # Call all registered callbacks
                        if stream_name in self.callbacks:
                            for callback in self.callbacks[stream_name]:
                                try:
                                    await callback(data)
                                except Exception as e:
                                    logger.error(f"Error in callback for {stream_name}: {e}")

            except websockets.exceptions.ConnectionClosed:
                logger.warning(f"Connection closed for {stream_name}, reconnecting...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in stream {stream_name}: {e}")
                await asyncio.sleep(5)

    async def start(self):
        """Start the market data streamer"""
        self.running = True
        logger.info("Market data streamer started")

    async def stop(self):
        """Stop the market data streamer"""
        self.running = False
        for task in self.connections.values():
            task.cancel()
        self.connections.clear()
        logger.info("Market data streamer stopped")


class MarketDataService:
    """Service for managing market data storage and retrieval"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.redis = None

    async def _get_redis(self):
        """Get Redis client"""
        if not self.redis:
            self.redis = await get_redis()
        return self.redis

    async def store_candle(self, candle_data: Dict) -> Candle:
        """Store candlestick data in database"""
        candle = Candle(
            symbol=candle_data['symbol'],
            timeframe=candle_data['timeframe'],
            timestamp=candle_data['timestamp'],
            open_time=datetime.fromtimestamp(candle_data['timestamp'] / 1000),
            close_time=datetime.fromtimestamp(candle_data['close_time'] / 1000),
            open=candle_data['open'],
            high=candle_data['high'],
            low=candle_data['low'],
            close=candle_data['close'],
            volume=candle_data['volume'],
            quote_volume=candle_data.get('quote_volume'),
            trades_count=candle_data.get('trades_count'),
            taker_buy_base_volume=candle_data.get('taker_buy_base_volume'),
            taker_buy_quote_volume=candle_data.get('taker_buy_quote_volume')
        )

        self.db.add(candle)
        await self.db.commit()
        await self.db.refresh(candle)

        return candle

    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100
    ) -> List[Candle]:
        """Retrieve candlestick data from database"""
        result = await self.db.execute(
            select(Candle)
            .where(Candle.symbol == symbol, Candle.timeframe == timeframe)
            .order_by(Candle.timestamp.desc())
            .limit(limit)
        )
        candles = result.scalars().all()
        return list(reversed(candles))

    async def update_ticker(self, ticker_data: Dict) -> MarketTicker:
        """Update market ticker data"""
        result = await self.db.execute(
            select(MarketTicker).where(MarketTicker.symbol == ticker_data['symbol'])
        )
        ticker = result.scalar_one_or_none()

        if ticker:
            ticker.last_price = ticker_data['last_price']
            ticker.bid_price = ticker_data.get('bid_price')
            ticker.ask_price = ticker_data.get('ask_price')
            ticker.price_change = ticker_data.get('price_change')
            ticker.price_change_percent = ticker_data.get('price_change_percent')
            ticker.high_24h = ticker_data.get('high_24h')
            ticker.low_24h = ticker_data.get('low_24h')
            ticker.volume_24h = ticker_data.get('volume_24h')
            ticker.quote_volume_24h = ticker_data.get('quote_volume_24h')
            ticker.weighted_avg_price = ticker_data.get('weighted_avg_price')
            ticker.timestamp = ticker_data['timestamp']
        else:
            ticker = MarketTicker(**ticker_data)
            self.db.add(ticker)

        await self.db.commit()
        await self.db.refresh(ticker)

        # Cache in Redis
        redis_client = await self._get_redis()
        cache_key = f"ticker:{ticker_data['symbol']}"
        await redis_client.setex(
            cache_key,
            60,  # 60 seconds TTL
            json.dumps({
                'last_price': ticker.last_price,
                'bid_price': ticker.bid_price,
                'ask_price': ticker.ask_price,
                'price_change_percent': ticker.price_change_percent
            })
        )

        return ticker

    async def get_ticker(self, symbol: str) -> Optional[MarketTicker]:
        """Get ticker data with Redis caching"""
        # Try cache first
        redis_client = await self._get_redis()
        cache_key = f"ticker:{symbol}"
        cached = await redis_client.get(cache_key)

        if cached:
            return json.loads(cached)

        # Get from database
        result = await self.db.execute(
            select(MarketTicker).where(MarketTicker.symbol == symbol)
        )
        ticker = result.scalar_one_or_none()

        if ticker:
            # Cache the result
            await redis_client.setex(
                cache_key,
                60,
                json.dumps({
                    'last_price': ticker.last_price,
                    'bid_price': ticker.bid_price,
                    'ask_price': ticker.ask_price,
                    'price_change_percent': ticker.price_change_percent
                })
            )

        return ticker

    async def store_order_book(self, order_book_data: Dict) -> OrderBook:
        """Store order book snapshot"""
        order_book = OrderBook(
            symbol=order_book_data['symbol'],
            best_bid=order_book_data['best_bid'],
            best_ask=order_book_data['best_ask'],
            spread=order_book_data['best_ask'] - order_book_data['best_bid'],
            bid_volume=order_book_data.get('bid_volume'),
            ask_volume=order_book_data.get('ask_volume'),
            timestamp=order_book_data['timestamp']
        )

        self.db.add(order_book)
        await self.db.commit()
        await self.db.refresh(order_book)

        return order_book


class HistoricalDataFetcher:
    """Fetch historical market data from Binance"""

    def __init__(self, binance_client):
        self.client = binance_client

    async def fetch_historical_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Fetch historical candlestick data"""
        klines = await self.client.get_klines(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        candles = []
        for kline in klines:
            candles.append({
                'symbol': symbol,
                'timeframe': interval,
                'timestamp': kline[0],
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[5]),
                'close_time': kline[6],
                'quote_volume': float(kline[7]),
                'trades_count': kline[8],
                'taker_buy_base_volume': float(kline[9]),
                'taker_buy_quote_volume': float(kline[10])
            })

        return candles