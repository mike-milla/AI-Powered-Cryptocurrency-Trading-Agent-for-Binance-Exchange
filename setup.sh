#!/bin/bash

# AI Trading Bot Setup Script
# This script automates the initial setup

set -e  # Exit on error

echo "🤖 AI Trading Bot - Setup Script"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and configure:"
    echo "   - SECRET_KEY (generate a random string)"
    echo "   - JWT_SECRET_KEY (generate a random string)"
    echo "   - ENCRYPTION_KEY (exactly 32 bytes)"
    echo "   - POSTGRES_PASSWORD"
    echo "   - BINANCE_API_KEY (from testnet.binance.vision)"
    echo "   - BINANCE_API_SECRET"
    echo ""
    read -p "Press Enter when you've configured .env..."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "🐳 Starting Docker containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "🗄️  Running database migrations..."
docker-compose exec -T app alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Services:"
echo "   - API: http://localhost:8000"
echo "   - Swagger Docs: http://localhost:8000/docs"
echo "   - ReDoc: http://localhost:8000/redoc"
echo ""
echo "📝 Next steps:"
echo "   1. Create a user account via POST /auth/register"
echo "   2. Login via POST /auth/login to get access token"
echo "   3. Update your Binance API keys via POST /auth/api-keys"
echo "   4. Start trading or analyzing markets!"
echo ""
echo "📖 For detailed instructions, see README.md and INSTALLATION.md"
echo ""
echo "🔍 To view logs:"
echo "   docker-compose logs -f app"
echo ""