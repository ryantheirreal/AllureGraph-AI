#!/bin/bash
# AllureGraph-AI — Setup Script

set -e

echo "🚀 Setting up AllureGraph-AI..."

# Create virtual environment
python -m venv venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate

# Install dependencies
pip install --upgrade pip
pip install -r api/requirements.txt

# Install Playwright browsers
python -m playwright install chromium

# Copy env template
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file — fill in your API keys"
fi

# Initialize git
if [ ! -d .git ]; then
    git init
    git add .
    git commit -m "🚀 Initial AllureGraph-AI setup"
fi

echo ""
echo "✅ AllureGraph-AI is ready!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys"
echo "  2. Run: uvicorn api.main:app --reload"
echo "  3. Open: http://localhost:8000/docs"
echo ""
