# 🚀 Quick Start Guide

## Fastest Way to Get Started

### 1. Configure Environment (2 minutes)
```bash
# Edit the .env file
nano .env
```

**MUST CHANGE THESE:**
- `SECRET_KEY` - Any random string (32+ characters)
- `JWT_SECRET_KEY` - Another random string
- `ENCRYPTION_KEY` - Exactly 32 characters
- `POSTGRES_PASSWORD` - Strong password
- `BINANCE_API_KEY` - From testnet.binance.vision
- `BINANCE_API_SECRET` - From testnet.binance.vision

**Generate secure keys:**
```bash
python3 -c "import secrets; print('SECRET_KEY:', secrets.token_urlsafe(32))"
python3 -c "import secrets; print('JWT_SECRET_KEY:', secrets.token_urlsafe(32))"
python3 -c "import secrets; print('ENCRYPTION_KEY:', secrets.token_urlsafe(24))"
```

### 2. Start with Docker (1 command)
```bash
./setup.sh
```

OR manually:
```bash
docker-compose up -d
docker-compose exec app alembic upgrade head
```

### 3. Access the API
- **API:** http://localhost:8000
- **Swagger Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

## First API Call

### 1. Register User
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader1",
    "email": "trader1@example.com",
    "password": "SecurePass123",
    "full_name": "Test Trader"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "trader1",
    "password": "SecurePass123"
  }'
```

**Save the `access_token` from response!**

### 3. Update Binance Keys
```bash
export TOKEN="your_access_token_here"

curl -X POST http://localhost:8000/auth/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "api_key": "your_testnet_api_key",
    "api_secret": "your_testnet_secret",
    "use_testnet": true
  }'
```

### 4. Test AI Analysis
```bash
curl -X POST http://localhost:8000/ai/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "limit": 100
  }'
```

## Common Commands

### View Logs
```bash
docker-compose logs -f app
```

### Restart Services
```bash
docker-compose restart
```

### Stop Everything
```bash
docker-compose down
```

### Access Database
```bash
docker-compose exec postgres psql -U trading_bot_user -d trading_bot_db
```

### Check Redis
```bash
docker-compose exec redis redis-cli ping
```

## Troubleshooting

**Can't connect to database?**
```bash
docker-compose restart postgres
```

**Port 8000 already in use?**
```bash
# Change PORT in .env to 8001 or other
PORT=8001
docker-compose up -d
```

**Need to reset everything?**
```bash
docker-compose down -v  # WARNING: Deletes all data
docker-compose up -d
```

## Next Steps

1. ✅ Explore API docs: http://localhost:8000/docs
2. ✅ Test on Binance Testnet (free funds!)
3. ✅ Read full documentation in README.md
4. ✅ Monitor logs for AI decisions
5. ✅ Adjust risk parameters in .env

## Support

📧 Email: beannsofts@gmail.com | info@beannsofts.com
📱 Phone: 0795557216

**Happy Trading! 🚀📈**