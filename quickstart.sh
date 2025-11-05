#!/bin/bash

# Quick start script for SERP Tracker
# Usage: ./quickstart.sh

set -e

echo "=================================="
echo "SERP Tracker Quick Start"
echo "=================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

echo "✓ Python found: $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# Create directories
echo ""
echo "📁 Creating directories..."
mkdir -p data reports logs exports

# Initialize database
echo ""
echo "🗄️  Initializing database..."
python3 -c "from database import RankingDatabase; RankingDatabase()"

# Check if config exists
if [ ! -f "config.yaml" ]; then
    echo ""
    echo "⚠️  No config.yaml found. Please create one based on the example in README.md"
    exit 1
fi

# Run test
echo ""
echo "🧪 Running test check..."
python tracker.py --test

echo ""
echo "=================================="
echo "✅ Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit config.yaml with your keywords"
echo "2. Run: python tracker.py --test"
echo "3. View: python report.py"
echo ""
echo "See USAGE.md for more examples"
