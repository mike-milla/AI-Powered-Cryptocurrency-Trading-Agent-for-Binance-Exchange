from binance.client import Client
from binance.enums import *
from binance.exceptions import BinanceAPIException
import ccxt
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from config import settings

logger = logging.getLogger(__name__)


class BinanceSpotClient:
    """Binance Spot Trading Client"""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet

        if testnet:
            self.client = Client(
                api_key,
                api_secret,
                testnet=True,
                tld='com'
            )
            self.client.API_URL = 'https://testnet.binance.vision/api'
        else:
            self.client = Client(api_key, api_secret)

        logger.info(f"Binance Spot Client initialized (Testnet: {testnet})")

    async def get_account_balance(self) -> Dict[str, Any]:
        """Get account balance"""
        try:
            account_info = self.client.get_account()
            balances = []
            for balance in account_info['balances']:
                if float(balance['free']) > 0 or float(balance['locked']) > 0:
                    balances.append({
                        'asset': balance['asset'],
                        'free': float(balance['free']),
                        'locked': float(balance['locked']),
                        'total': float(balance['free']) + float(balance['locked'])
                    })
            return {
                'balances': balances,
                'can_trade': account_info['canTrade'],
                'can_withdraw': account_info['canWithdraw'],
                'can_deposit': account_info['canDeposit']
            }
        except BinanceAPIException as e:
            logger.error(f"Error getting account balance: {e}")
            raise

    async def create_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Dict[str, Any]:
        """Create market order"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_MARKET,
                quantity=quantity
            )
            return self._format_order_response(order)
        except BinanceAPIException as e:
            logger.error(f"Error creating market order: {e}")
            raise

    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = TIME_IN_FORCE_GTC
    ) -> Dict[str, Any]:
        """Create limit order"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=time_in_force,
                quantity=quantity,
                price=price
            )
            return self._format_order_response(order)
        except BinanceAPIException as e:
            logger.error(f"Error creating limit order: {e}")
            raise

    async def create_stop_loss_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float
    ) -> Dict[str, Any]:
        """Create stop loss order"""
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_STOP_LOSS,
                quantity=quantity,
                stopPrice=stop_price
            )
            return self._format_order_response(order)
        except BinanceAPIException as e:
            logger.error(f"Error creating stop loss order: {e}")
            raise

    async def create_oco_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        stop_price: float,
        stop_limit_price: float
    ) -> Dict[str, Any]:
        """Create OCO (One-Cancels-the-Other) order"""
        try:
            order = self.client.create_oco_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                stopPrice=stop_price,
                stopLimitPrice=stop_limit_price,
                stopLimitTimeInForce=TIME_IN_FORCE_GTC
            )
            return order
        except BinanceAPIException as e:
            logger.error(f"Error creating OCO order: {e}")
            raise

    async def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an order"""
        try:
            result = self.client.cancel_order(symbol=symbol, orderId=order_id)
            return result
        except BinanceAPIException as e:
            logger.error(f"Error canceling order: {e}")
            raise

    async def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order status"""
        try:
            order = self.client.get_order(symbol=symbol, orderId=order_id)
            return self._format_order_response(order)
        except BinanceAPIException as e:
            logger.error(f"Error getting order status: {e}")
            raise

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open orders"""
        try:
            orders = self.client.get_open_orders(symbol=symbol)
            return [self._format_order_response(order) for order in orders]
        except BinanceAPIException as e:
            logger.error(f"Error getting open orders: {e}")
            raise

    async def get_all_orders(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get all orders for a symbol"""
        try:
            orders = self.client.get_all_orders(symbol=symbol, limit=limit)
            return [self._format_order_response(order) for order in orders]
        except BinanceAPIException as e:
            logger.error(f"Error getting all orders: {e}")
            raise

    async def get_my_trades(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get trade history"""
        try:
            trades = self.client.get_my_trades(symbol=symbol, limit=limit)
            return trades
        except BinanceAPIException as e:
            logger.error(f"Error getting trades: {e}")
            raise

    async def get_symbol_ticker(self, symbol: str) -> Dict[str, Any]:
        """Get current price for a symbol"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return ticker
        except BinanceAPIException as e:
            logger.error(f"Error getting ticker: {e}")
            raise

    async def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """Get order book"""
        try:
            order_book = self.client.get_order_book(symbol=symbol, limit=limit)
            return order_book
        except BinanceAPIException as e:
            logger.error(f"Error getting order book: {e}")
            raise

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> List[List]:
        """Get candlestick data"""
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit,
                startTime=start_time,
                endTime=end_time
            )
            return klines
        except BinanceAPIException as e:
            logger.error(f"Error getting klines: {e}")
            raise

    def _format_order_response(self, order: Dict) -> Dict[str, Any]:
        """Format order response"""
        return {
            'order_id': order.get('orderId'),
            'client_order_id': order.get('clientOrderId'),
            'symbol': order.get('symbol'),
            'side': order.get('side'),
            'type': order.get('type'),
            'status': order.get('status'),
            'price': float(order.get('price', 0)),
            'quantity': float(order.get('origQty', 0)),
            'executed_quantity': float(order.get('executedQty', 0)),
            'executed_price': float(order.get('cummulativeQuoteQty', 0)) / float(order.get('executedQty', 1)) if float(order.get('executedQty', 0)) > 0 else 0,
            'time': order.get('time'),
            'update_time': order.get('updateTime')
        }


class BinanceFuturesClient:
    """Binance Futures Trading Client"""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet

        if testnet:
            self.exchange = ccxt.binanceusdm({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',
                    'test': True
                },
                'urls': {
                    'api': {
                        'public': 'https://testnet.binancefuture.com/fapi/v1',
                        'private': 'https://testnet.binancefuture.com/fapi/v1'
                    }
                }
            })
        else:
            self.exchange = ccxt.binanceusdm({
                'apiKey': api_key,
                'secret': api_secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })

        logger.info(f"Binance Futures Client initialized (Testnet: {testnet})")

    async def get_account_balance(self) -> Dict[str, Any]:
        """Get futures account balance"""
        try:
            balance = self.exchange.fetch_balance()
            return {
                'total_wallet_balance': balance['total'].get('USDT', 0),
                'available_balance': balance['free'].get('USDT', 0),
                'used_margin': balance['used'].get('USDT', 0),
                'balances': balance['total']
            }
        except Exception as e:
            logger.error(f"Error getting futures balance: {e}")
            raise

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get open positions"""
        try:
            positions = self.exchange.fetch_positions()
            open_positions = [
                pos for pos in positions
                if float(pos.get('contracts', 0)) != 0
            ]
            return open_positions
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            raise

    async def create_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float
    ) -> Dict[str, Any]:
        """Create futures market order"""
        try:
            order = self.exchange.create_market_order(symbol, side, quantity)
            return order
        except Exception as e:
            logger.error(f"Error creating futures market order: {e}")
            raise

    async def create_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ) -> Dict[str, Any]:
        """Create futures limit order"""
        try:
            order = self.exchange.create_limit_order(symbol, side, quantity, price)
            return order
        except Exception as e:
            logger.error(f"Error creating futures limit order: {e}")
            raise

    async def set_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Set leverage for a symbol"""
        try:
            result = self.exchange.set_leverage(leverage, symbol)
            return result
        except Exception as e:
            logger.error(f"Error setting leverage: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel a futures order"""
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            return result
        except Exception as e:
            logger.error(f"Error canceling futures order: {e}")
            raise


class BinanceClientManager:
    """Manager for Binance API clients"""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = True
    ):
        self.spot_client = BinanceSpotClient(api_key, api_secret, testnet)
        self.futures_client = BinanceFuturesClient(api_key, api_secret, testnet)

    def get_spot_client(self) -> BinanceSpotClient:
        """Get spot trading client"""
        return self.spot_client

    def get_futures_client(self) -> BinanceFuturesClient:
        """Get futures trading client"""
        return self.futures_client