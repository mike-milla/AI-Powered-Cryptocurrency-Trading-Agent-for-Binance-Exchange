#!/bin/bash

# AI Trading Bot Setup Script
# This script automates the initial setup

echo "🤖 AI Trading Bot - Setup Script"
echo "================================"
echo ""

# Function to install Docker on Ubuntu/Debian
install_docker() {
    echo "📦 Installing Docker..."

    # Remove old versions
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    # Update package index
    sudo apt-get update

    # Install dependencies
    sudo apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release

    # Add Docker's official GPG key
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg

    # Set up the repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add current user to docker group
    sudo usermod -aG docker $USER

    echo "✅ Docker installed successfully!"
    echo "⚠️  You may need to log out and back in for group changes to take effect"
    echo ""
}

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
if ! command -v docker &> /dev/null && ! sudo docker --version &> /dev/null; then
    echo "⚠️  Docker is not installed on this system"
    echo ""
    read -p "Would you like to install Docker now? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_docker
    else
        echo "❌ Docker is required to run this application"
        echo "Please install Docker manually: https://docs.docker.com/get-docker/"
        exit 1
    fi
fi

# Check if Docker Compose is installed (both old and new syntax)
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null && ! sudo docker compose version &> /dev/null; then
    echo "⚠️  Docker Compose is not installed on this system"
    echo ""
    read -p "Would you like to install Docker Compose now? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 Installing Docker Compose plugin..."
        sudo apt-get update
        sudo apt-get install -y docker-compose-plugin
        echo "✅ Docker Compose installed successfully!"
        echo ""
    else
        echo "❌ Docker Compose is required to run this application"
        echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
fi

# Determine which Docker Compose command to use
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="sudo docker compose"
fi

echo "✅ Docker and Docker Compose are ready!"
echo ""
echo "🐳 Starting Docker containers..."

# Check if we need sudo for docker
if ! docker ps &> /dev/null 2>&1; then
    echo "⚠️  Running Docker with sudo (you may need to log out and back in to use Docker without sudo)"
    DOCKER_COMPOSE="sudo docker compose"
    $DOCKER_COMPOSE up -d
else
    $DOCKER_COMPOSE up -d
fi

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "🗄️  Running database migrations..."
$DOCKER_COMPOSE exec -T app alembic upgrade head

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
echo "   $DOCKER_COMPOSE logs -f app"
echo ""