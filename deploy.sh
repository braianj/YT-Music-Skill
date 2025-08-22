#!/bin/bash

# Deployment script for YouTube Music Alexa Skill
# Configures AWS Lambda on the free tier

set -e

echo "🚀 Deploying YouTube Music Alexa Skill"
echo "======================================"

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check ASK CLI
if ! command -v ask &> /dev/null; then
    echo "❌ ASK CLI not found. Install with: npm install -g ask-cli"
    exit 1
fi

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Install from: https://nodejs.org/"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Check AWS configuration
echo "🔧 Checking AWS configuration..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS not configured. Run: aws configure"
    exit 1
fi

echo "✅ AWS configuration found"

# Install dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Check that the Python service is available
echo "🐍 Checking Python service..."
cd ytmusic-service

if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

# Install Python dependencies if not installed
if ! python3 -c "import ytmusicapi" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

cd ..

# Configure environment variables for Lambda
echo "🔧 Setting up environment variables..."

# Create configuration file for lambda
cat > lambda/env.json << EOF
{
  "YTMUSIC_API_ENDPOINT": "https://your-ytmusic-service.herokuapp.com",
  "NODE_ENV": "production"
}
EOF

echo "⚠️  IMPORTANT: Update YTMUSIC_API_ENDPOINT in lambda/env.json with your Python service URL"

# Deploy skill
echo "🚀 Deploying skill to AWS Lambda..."

# Use Lambda free tier
export ASK_LAMBDA_MEMORY_SIZE=128
export ASK_LAMBDA_TIMEOUT=30
export ASK_LAMBDA_RUNTIME=nodejs18.x

ask deploy --target all

echo ""
echo "✅ Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Configure your Python service URL in lambda/env.json"
echo "2. Redeploy if needed: ask deploy --target lambda"
echo "3. Test your skill: ask dialog --locale es-ES"
echo ""
echo "🔧 To deploy the Python service:"
echo "1. Use a free service like Railway, Render, or Heroku"
echo "2. Deploy the ytmusic-service directory"
echo "3. Update YTMUSIC_API_ENDPOINT with your service URL"
echo ""
echo "📱 To test on your Alexa devices:"
echo "1. Go to alexa.amazon.com"
echo "2. Find your skill in 'Your Skills'"
echo "3. Enable it for testing"
echo "4. Say: 'Alexa, abrí YouTube Music'"