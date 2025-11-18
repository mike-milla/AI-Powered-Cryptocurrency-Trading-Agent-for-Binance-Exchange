# AI-Powered Cryptocurrency Trading Agent for Binance Exchange

A comprehensive, AI-driven automated cryptocurrency trading system that operates on Binance (Spot and Futures) with machine learning, technical analysis, risk management, and human oversight.

## 🚀 Milestone 1 - Core Infrastructure & AI Trading Engine

### Features Implemented

#### 1. Backend Infrastructure
- ✅ FastAPI backend with async support
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ Redis caching layer for performance
- ✅ Alembic database migrations
- ✅ Comprehensive logging system (JSON + file rotation)

#### 2. Binance API Integration
- ✅ Binance Spot trading client
- ✅ Binance Futures trading client
- ✅ Testnet support for safe testing
- ✅ API authentication and secure key management
- ✅ Market/Limit/Stop-Loss/OCO/Trailing Stop orders
- ✅ Real-time balance and position retrieval
- ✅ Order book data streaming
- ✅ Trade history access

#### 3. Security
- ✅ JWT-based authentication
- ✅ AES-256 encrypted API key storage
- ✅ Password hashing with bcrypt
- ✅ Complete action logging and audit trail

#### 4. Real-Time Market Data
- ✅ WebSocket streaming for live data
- ✅ Multiple timeframe support (1M, 5M, 15M, 30M, 1H, 4H, Daily, Weekly)
- ✅ OHLCV candlestick data
- ✅ Order book snapshots
- ✅ Market ticker updates

#### 5. Technical Analysis
- ✅ Moving Averages (SMA, EMA) - 50, 100, 200 periods
- ✅ RSI with divergence detection
- ✅ MACD with signal line
- ✅ Bollinger Bands
- ✅ ATR for volatility
- ✅ Volume analysis
- ✅ Stochastic Oscillator
- ✅ ADX (Average Directional Index)

#### 6. Pattern Recognition
- ✅ Candlestick patterns (Doji, Hammer, Engulfing, Morning/Evening Star, etc.)
- ✅ Chart patterns (Double Top/Bottom, Head & Shoulders)
- ✅ Support and Resistance levels
- ✅ Trend detection and analysis

#### 7. Machine Learning
- ✅ LSTM neural network for price prediction
- ✅ GRU neural network for price prediction
- ✅ Ensemble prediction (LSTM + GRU)
- ✅ Confidence scoring
- ✅ Model training and persistence

#### 8. AI Trading Engine
- ✅ Comprehensive market analysis
- ✅ Multi-factor decision making
- ✅ Adjustable autonomy levels:
  - **Full-Auto**: Automatic trade execution
  - **Semi-Auto**: Trade approval required
  - **Signal-Only**: Signals without execution
- ✅ Confidence-based filtering
- ✅ Detailed reasoning for decisions

#### 9. Risk Management
- ✅ Position sizing calculator
- ✅ Stop-loss placement (fixed, trailing, ATR-based)
- ✅ Take-profit management
- ✅ Maximum daily loss limits
- ✅ Maximum open trades limitation
- ✅ Emergency shutdown mechanism
- ✅ Risk event logging

#### 10. API Endpoints
- ✅ Authentication (register, login, API key management)
- ✅ Trading (market/limit/stop orders, order management)
- ✅ AI analysis and decision endpoints
- ✅ Risk management status endpoints

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

## 🛠️ Installation

### Option 1: Docker (Recommended)

1. Clone the repository
```bash
git clone <repository-url>
cd AI-Powered-Cryptocurrency-Trading-Agent-for-Binance-Exchange
```

2. Copy environment file
```bash
cp .env.example .env
```

3. Edit `.env` and configure:
- Database credentials
- Binance API keys (testnet or production)
- JWT secret keys
- Encryption key (exactly 32 bytes)

4. Start with Docker Compose
```bash
docker-compose up -d
```

5. Run database migrations
```bash
docker-compose exec app alembic upgrade head
```

### Option 2: Manual Installation

1. Install dependencies
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL and Redis

3. Configure environment variables in `.env`

4. Run migrations
```bash
alembic upgrade head
```

5. Start the application
```bash
python main.py
```

## 🔧 Configuration

### Environment Variables

Key configuration in `.env`:

```env
# Binance API (Testnet)
BINANCE_TESTNET=True
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
ENCRYPTION_KEY=your-32-byte-encryption-key-here

# Trading Configuration
MAX_OPEN_TRADES=5
DEFAULT_POSITION_SIZE=100
MAX_DAILY_LOSS_PERCENT=5.0
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=4.0

# AI Configuration
AI_AUTONOMY_LEVEL=semi-auto
PREDICTION_CONFIDENCE_THRESHOLD=0.7
```

## 📚 API Documentation

Once running, access interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `POST /auth/api-keys` - Update Binance API keys
- `GET /auth/me` - Get current user info

#### Trading
- `POST /trading/orders/market` - Create market order
- `POST /trading/orders/limit` - Create limit order
- `DELETE /trading/orders/{order_id}` - Cancel order
- `GET /trading/orders/{order_id}` - Get order status
- `POST /trading/emergency-shutdown` - Trigger emergency stop
- `GET /trading/risk-status` - Get risk management status

#### AI Analysis
- `POST /ai/analyze` - Run AI market analysis
- `POST /ai/decision` - Get AI trading decision
- `POST /ai/autonomy` - Update autonomy level
- `GET /ai/signals/{symbol}` - Get latest AI signals

## 🧪 Testing with Binance Testnet

1. Get Testnet API keys from: https://testnet.binance.vision/

2. Configure in `.env`:
```env
BINANCE_TESTNET=True
BINANCE_API_KEY=your_testnet_key
BINANCE_API_SECRET=your_testnet_secret
```

3. Test trading without risking real funds!

## 🔐 Security Best Practices

1. **Never commit `.env` file**
2. **Use strong, unique passwords and keys**
3. **Rotate API keys regularly**
4. **Enable IP whitelisting on Binance**
5. **Never enable withdrawal permissions**
6. **Monitor logs regularly**
7. **Test thoroughly on testnet first**

## 📊 Database Schema

Main tables:
- `users` - User accounts and encrypted API keys
- `orders` - All order records
- `trades` - Completed trades with P&L
- `positions` - Open positions
- `candles` - OHLCV market data
- `market_tickers` - Real-time price data
- `audit_logs` - All system actions
- `ai_decision_logs` - AI trading decisions
- `risk_events` - Risk management events
- `trading_strategies` - Strategy configurations
- `backtest_results` - Backtesting results

## 🎯 AI Trading Decision Process

1. **Data Collection**: Gather OHLCV data for analysis
2. **Technical Analysis**: Calculate all technical indicators
3. **Pattern Recognition**: Detect candlestick and chart patterns
4. **ML Prediction**: Run LSTM/GRU ensemble prediction
5. **Decision Making**: Combine all signals with weighted scoring
6. **Risk Check**: Verify against risk management rules
7. **Execution**: Execute based on autonomy level

## ⚠️ Risk Management

The system includes multiple safety mechanisms:

1. **Position Sizing**: Never risk more than configured %
2. **Stop-Loss**: Automatic stop-loss on all positions
3. **Daily Loss Limit**: Trading stops if daily loss exceeds limit
4. **Max Open Trades**: Limit concurrent positions
5. **Emergency Shutdown**: Manual or automatic emergency stop
6. **Confidence Threshold**: Only trade high-confidence signals

## 📝 Logging

Logs are stored in:
- `logs/trading_bot.log` - All logs (JSON format)
- `logs/error.log` - Errors only

Log format includes:
- Timestamp
- Level (INFO, WARNING, ERROR)
- Module and function
- Structured data (JSON)

## 🚦 Next Steps (Milestone 2 & 3)

**Milestone 2** will include:
- 8 trading strategies (scalping, swing, trend-following, etc.)
- Backtesting engine
- Sentiment analysis
- Walk-forward optimization

**Milestone 3** will include:
- React dashboard
- Real-time charts
- Alert system (Email, Telegram)
- Production deployment

## 🤝 Support

For issues or questions:
- Email: beannsofts@gmail.com | info@beannsofts.com
- Phone: 0795557216

## 📄 License

Copyright © 2025 BEANNSOFTS LIMITED
All rights reserved.

---

**⚠️ Disclaimer**: Cryptocurrency trading carries substantial risk. This software is provided "as is" without warranty. The developers are not liable for any trading losses. Always test thoroughly on testnet before using real funds.