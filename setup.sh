#!/bin/bash
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🛠 Installing Playwright browsers..."
playwright install

echo "✅ Setup complete!"

