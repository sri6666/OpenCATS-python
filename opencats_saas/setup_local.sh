#!/bin/bash

# OpenCATS SaaS - Local Setup Script
# This script automates the local development setup

set -e  # Exit on error

echo "🚀 OpenCATS SaaS - Local Setup"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION found"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠${NC} Docker not found. Will use local MySQL/Redis if available."
    USE_DOCKER=false
else
    echo -e "${GREEN}✓${NC} Docker found"
    USE_DOCKER=true
fi

# Create virtual environment
echo ""
echo "📦 Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet
echo -e "${GREEN}✓${NC} Pip upgraded"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓${NC} Dependencies installed"

# Setup .env file
echo ""
echo "⚙️  Configuring environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env

    # Generate secret key
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

    # Update .env with local settings
    sed -i.bak "s|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
    sed -i.bak "s|FLASK_ENV=.*|FLASK_ENV=development|" .env
    sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=mysql+pymysql://opencats:opencats123@localhost/opencats_dev|" .env
    sed -i.bak "s|REDIS_URL=.*|REDIS_URL=redis://localhost:6379/0|" .env

    rm .env.bak

    echo -e "${GREEN}✓${NC} .env file created"
else
    echo -e "${YELLOW}⚠${NC} .env file already exists"
fi

# Setup database with Docker
if [ "$USE_DOCKER" = true ]; then
    echo ""
    echo "🐳 Setting up MySQL with Docker..."

    # Check if container exists
    if [ "$(docker ps -aq -f name=opencats-mysql)" ]; then
        echo -e "${YELLOW}⚠${NC} MySQL container already exists"
        docker start opencats-mysql 2>/dev/null || true
    else
        docker run --name opencats-mysql \
            -e MYSQL_ROOT_PASSWORD=root \
            -e MYSQL_DATABASE=opencats_dev \
            -e MYSQL_USER=opencats \
            -e MYSQL_PASSWORD=opencats123 \
            -p 3306:3306 \
            -d mysql:8.0

        echo -e "${GREEN}✓${NC} MySQL container started"
        echo "⏳ Waiting for MySQL to be ready..."
        sleep 15
    fi

    # Setup Redis with Docker
    echo ""
    echo "🐳 Setting up Redis with Docker..."

    if [ "$(docker ps -aq -f name=opencats-redis)" ]; then
        echo -e "${YELLOW}⚠${NC} Redis container already exists"
        docker start opencats-redis 2>/dev/null || true
    else
        docker run --name opencats-redis \
            -p 6379:6379 \
            -d redis:alpine

        echo -e "${GREEN}✓${NC} Redis container started"
    fi
else
    echo ""
    echo -e "${YELLOW}⚠${NC} Docker not available. Please ensure MySQL and Redis are running locally."
    echo "   MySQL: localhost:3306 (user: opencats, pass: opencats123, db: opencats_dev)"
    echo "   Redis: localhost:6379"
fi

# Initialize database
echo ""
echo "🗄️  Initializing database..."
export FLASK_APP=run.py

# Wait a bit more for MySQL to be fully ready
if [ "$USE_DOCKER" = true ]; then
    echo "⏳ Ensuring MySQL is fully ready..."
    sleep 5
fi

# Try to initialize database
if flask init_db 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Database initialized"
else
    echo -e "${YELLOW}⚠${NC} Database might already be initialized or connection failed"
fi

# Seed database
echo ""
echo "🌱 Seeding database with demo data..."
if flask seed_db 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Database seeded"
    echo ""
    echo "📝 Demo Login Credentials:"
    echo "   Username: admin"
    echo "   Password: admin123"
else
    echo -e "${YELLOW}⚠${NC} Could not seed database (might already be seeded)"
fi

# Create uploads directory
echo ""
echo "📁 Creating uploads directory..."
mkdir -p uploads
echo -e "${GREEN}✓${NC} Uploads directory ready"

# Summary
echo ""
echo "================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "================================"
echo ""
echo "🎯 Next Steps:"
echo ""
echo "1. Start the application:"
echo "   source venv/bin/activate"
echo "   python run.py"
echo ""
echo "2. Open your browser:"
echo "   http://localhost:5000"
echo ""
echo "3. Login with:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📚 For more details, see LOCAL_SETUP.md"
echo ""

# Check if we should start the server
read -p "🚀 Start the server now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🌐 Starting OpenCATS on http://localhost:5000"
    echo "   Press Ctrl+C to stop"
    echo ""
    python run.py
fi
