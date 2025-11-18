# Installation Guide

## Quick Start with Docker (Recommended)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Git

### Steps

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd AI-Powered-Cryptocurrency-Trading-Agent-for-Binance-Exchange
```

2. **Create environment file**
```bash
cp .env.example .env
```

3. **Edit .env file**
```bash
nano .env
```

Required configurations:
```env
# IMPORTANT: Change these values!
SECRET_KEY=generate-a-random-32-character-string-here
JWT_SECRET_KEY=generate-another-random-string-here
ENCRYPTION_KEY=exactly-32-bytes-required-here!!

# Database
POSTGRES_PASSWORD=create_strong_password_here

# Binance Testnet (get from https://testnet.binance.vision/)
BINANCE_TESTNET=True
BINANCE_API_KEY=your_binance_testnet_api_key
BINANCE_API_SECRET=your_binance_testnet_secret_key
```

4. **Start the services**
```bash
docker-compose up -d
```

5. **Check if services are running**
```bash
docker-compose ps
```

You should see:
- trading_bot_app (port 8000)
- trading_bot_db (port 5432)
- trading_bot_redis (port 6379)

6. **Run database migrations**
```bash
docker-compose exec app alembic upgrade head
```

7. **Access the API**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Manual Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Steps

1. **Install PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# MacOS
brew install postgresql@15

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql@15  # MacOS
```

2. **Install Redis**
```bash
# Ubuntu/Debian
sudo apt install redis-server

# MacOS
brew install redis

# Start Redis
sudo systemctl start redis  # Linux
brew services start redis  # MacOS
```

3. **Create database**
```bash
sudo -u postgres psql
CREATE DATABASE trading_bot_db;
CREATE USER trading_bot_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE trading_bot_db TO trading_bot_user;
\q
```

4. **Clone repository**
```bash
git clone <your-repo-url>
cd AI-Powered-Cryptocurrency-Trading-Agent-for-Binance-Exchange
```

5. **Create virtual environment**
```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/MacOS
# OR
venv\Scripts\activate  # Windows
```

6. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

7. **Configure environment**
```bash
cp .env.example .env
nano .env  # Edit with your values
```

8. **Run migrations**
```bash
alembic upgrade head
```

9. **Start the application**
```bash
python main.py
```

## Getting Binance Testnet API Keys

1. Go to https://testnet.binance.vision/
2. Click "Generate HMAC_SHA256 Key"
3. Save your API Key and Secret Key
4. Add to your `.env` file

## First-Time Setup

### 1. Create a user account
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader1",
    "email": "trader1@example.com",
    "password": "SecurePassword123",
    "full_name": "Trader One"
  }'
```

### 2. Login and get token
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader1",
    "password": "SecurePassword123"
  }'
```

Save the `access_token` from the response.

### 3. Update API keys
```bash
curl -X POST http://localhost:8000/auth/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "api_key": "your_binance_testnet_api_key",
    "api_secret": "your_binance_testnet_secret",
    "use_testnet": true
  }'
```

## Verification

### Check system health
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00Z"
}
```

### Check risk status
```bash
curl http://localhost:8000/trading/risk-status \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Troubleshooting

### Database connection error
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check connection
psql -U trading_bot_user -d trading_bot_db -h localhost
```

### Redis connection error
```bash
# Check if Redis is running
redis-cli ping

# Should return: PONG
```

### Port already in use
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Module import errors
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Docker issues
```bash
# View logs
docker-compose logs app

# Rebuild containers
docker-compose down
docker-compose up --build -d

# Reset everything
docker-compose down -v
docker-compose up -d
```

## Generating Secure Keys

### SECRET_KEY and JWT_SECRET_KEY
```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### ENCRYPTION_KEY (exactly 32 bytes)
```python
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

## Next Steps

1. Read the [README.md](README.md) for feature overview
2. Explore the API documentation at http://localhost:8000/docs
3. Test with Binance Testnet
4. Monitor logs in `logs/trading_bot.log`

## Support

If you encounter issues:
1. Check the logs: `docker-compose logs app` or `logs/trading_bot.log`
2. Verify all environment variables are set correctly
3. Ensure all services are running
4. Contact support: beannsofts@gmail.com