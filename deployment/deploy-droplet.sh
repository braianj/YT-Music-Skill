#!/bin/bash
# Deployment script for DigitalOcean Droplet
# Run this on your Droplet to set up the Python service
set -e

echo "Setting up YouTube Music API Service on DigitalOcean Droplet"
echo "============================================================"

# Install system dependencies
echo "Installing system dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx ffmpeg

# Create application directory
echo "Setting up application directory..."
sudo mkdir -p /opt/ytmusic-service
sudo chown $USER:$USER /opt/ytmusic-service

# Copy service files
echo "Copying service files..."
cp -r ytmusic-service/* /opt/ytmusic-service/

# Create virtual environment
echo "Creating Python virtual environment..."
cd /opt/ytmusic-service
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
PORT=8080
API_KEY=CHANGE_ME_TO_A_RANDOM_STRING
EOF
    echo "IMPORTANT: Edit /opt/ytmusic-service/.env and set a strong API_KEY"
fi

# Set up YouTube Music authentication
if [ ! -f oauth.json ]; then
    echo ""
    echo "=== YouTube Music Authentication Setup ==="
    echo "You need to authenticate with your YouTube Premium account."
    echo "Run the following command and follow the instructions:"
    echo ""
    echo "  cd /opt/ytmusic-service && source venv/bin/activate"
    echo "  ytmusicapi oauth"
    echo ""
    echo "This will open a browser for OAuth authentication."
    echo "After authenticating, an oauth.json file will be created."
    echo "============================================"
    echo ""
fi

# Install systemd service
echo "Installing systemd service..."
sudo cp deployment/ytmusic.service /etc/systemd/system/ 2>/dev/null || \
    sudo cp ../deployment/ytmusic.service /etc/systemd/system/ 2>/dev/null || \
    echo "Warning: Could not copy systemd service file. Copy it manually."

sudo systemctl daemon-reload
sudo systemctl enable ytmusic

# Install nginx config
echo "Installing nginx configuration..."
sudo cp deployment/nginx-ytmusic.conf /etc/nginx/sites-available/ytmusic 2>/dev/null || \
    sudo cp ../deployment/nginx-ytmusic.conf /etc/nginx/sites-available/ytmusic 2>/dev/null || \
    echo "Warning: Could not copy nginx config. Copy it manually."

sudo ln -sf /etc/nginx/sites-available/ytmusic /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit /opt/ytmusic-service/.env and set API_KEY"
echo "2. Set up OAuth: cd /opt/ytmusic-service && source venv/bin/activate && ytmusicapi oauth"
echo "3. Edit /etc/nginx/sites-available/ytmusic - change 'your-domain.com'"
echo "4. Set up HTTPS: sudo certbot --nginx -d your-domain.com"
echo "5. Start the service: sudo systemctl start ytmusic"
echo "6. Test: curl https://your-domain.com/health"
