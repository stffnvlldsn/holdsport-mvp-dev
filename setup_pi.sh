#!/bin/bash

# Holdsport Bot Setup Script for Raspberry Pi
echo "🤖 Setting up Holdsport Bot on Raspberry Pi..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python and pip
echo "🐍 Installing Python and pip..."
sudo apt install -y python3 python3-pip python3-venv

# Install git
echo "📚 Installing git..."
sudo apt install -y git

# Create directory for the bot
echo "📁 Creating bot directory..."
mkdir -p ~/holdsport-bot
cd ~/holdsport-bot

# Clone the repository (you'll need to update this URL)
echo "📥 Cloning repository..."
git clone https://github.com/stffnvlldsn/holdsport-mvp-dev.git .

# Create virtual environment
echo "🔧 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Create .env file
echo "🔐 Creating .env file..."
cat > .env << EOF
# Holdsport credentials
HOLDSPORT_USERNAME=Steffen_Villadsen
HOLDSPORT_PASSWORD=Telenor1977

# Telegram settings
TELEGRAM_BOT_TOKEN=7893732165:AAFRrdhmTOLhSHHVHBGCJxE9WIEqbLe9WVk
TELEGRAM_CHAT_ID=6052252183

# Activity settings
HOLDSPORT_ACTIVITY_NAME=Herre 4 træning
EOF

echo "✅ Setup complete!"
echo "🚀 To start the bot, run:"
echo "   cd ~/holdsport-bot"
echo "   source venv/bin/activate"
echo "   python main.py" 