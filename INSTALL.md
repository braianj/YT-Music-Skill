# Installation Guide - YouTube Music Alexa Skill

This guide will help you install and configure the YouTube Music skill step by step.

## 📋 Prerequisites

### 1. Required Accounts
- **Amazon Developer Account**: [developer.amazon.com](https://developer.amazon.com)
- **AWS Account**: [aws.amazon.com](https://aws.amazon.com) (free tier)
- **YouTube Music Premium**: For better functionality

### 2. Required Software
```bash
# Node.js (version 18 or higher)
node --version  # Should show v18.x.x or higher

# npm (comes with Node.js)
npm --version

# Python 3.10+
python3 --version  # Should show 3.10.x or higher

# pip (comes with Python)
pip3 --version

# Git
git --version
```

### 3. Install Alexa Tools
```bash
# ASK CLI (Alexa Skills Kit Command Line Interface)
npm install -g ask-cli

# AWS CLI
# macOS: brew install awscli
# Windows: https://aws.amazon.com/cli/
# Linux: sudo apt install awscli

# Verify installation
ask --version
aws --version
```

## 🚀 Installation

### Step 1: Clone and Configure the Project
```bash
# Clone the repository
git clone <your-repository-url>
cd youtube-music-skill

# Install Node.js dependencies
npm install

# Install Python dependencies
cd ytmusic-service
pip3 install -r requirements.txt
cd ..
```

### Step 2: Configure AWS
```bash
# Configure AWS credentials
aws configure

# You'll be prompted for:
# AWS Access Key ID: [Your access key]
# AWS Secret Access Key: [Your secret key]
# Default region name: us-east-1  (recommended for Alexa)
# Default output format: json
```

### Step 3: Configure ASK CLI
```bash
# Initialize ASK CLI
ask configure

# Select:
# - Profile: default
# - AWS Profile: default
# - Vendor ID: (will be detected automatically)
```

### Step 4: Configure YouTube Music Authentication
```bash
# Run configuration script
python3 setup.py

# Follow instructions to:
# 1. Get YouTube Music cookie
# 2. Configure oauth.json
# 3. Test connection
```

### Step 5: Deploy the Skill
```bash
# Deploy using the automatic script
./deploy.sh

# Or manually:
ask deploy --target all
```

## 🔧 Python Service Configuration

### Option 1: Heroku (Free)
```bash
# Install Heroku CLI
# Create new app
heroku create your-ytmusic-app

# Configure environment variables
heroku config:set PORT=8080

# Deploy
cd ytmusic-service
git init
git add .
git commit -m "Initial commit"
heroku git:remote -a your-ytmusic-app
git push heroku main
```

### Option 2: Railway (Free)
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub account
3. Deploy the `ytmusic-service` directory
4. Copy the generated URL

### Option 3: Render (Free)
1. Go to [render.com](https://render.com)
2. Connect your repository
3. Configure as Web Service
4. Root Directory: `ytmusic-service`
5. Start Command: `python app.py`

### Update Service URL
Once the Python service is deployed, update the URL:

```bash
# Edit configuration file
nano lambda/env.json

# Change:
{
  "YTMUSIC_API_ENDPOINT": "https://your-service-url.herokuapp.com",
  "NODE_ENV": "production"
}

# Redeploy Lambda
ask deploy --target lambda
```

## 🧪 Testing

### 1. Test the Python Service
```bash
# Verify that the service works
curl -X POST https://your-service-url/search \\
  -H "Content-Type: application/json" \\
  -d '{"query":"Oasis Wonderwall"}'
```

### 2. Test the Skill Locally
```bash
# Use the ASK simulator
ask dialog --locale es-ES

# Test commands:
# > open youtube music
# > reproducí wonderwall de oasis
# > pausá
# > continuá
```

### 3. Test on Alexa Devices
1. Go to [alexa.amazon.com](https://alexa.amazon.com)
2. Go to "Skills" → "Your Skills" → "Dev"
3. Find your skill and enable it
4. Say: "Alexa, abrí YouTube Music"

## 📱 Test Commands

### Spanish (Argentina)
```
"Alexa, abrí YouTube Music"
"Alexa, reproducí Wonderwall de Oasis"
"Alexa, poné The Beatles"
"Alexa, reproducí mi playlist favoritos"
"Alexa, pausá"
"Alexa, continuá"
"Alexa, siguiente"
```

### English (US)
```
"Alexa, open YouTube Music"
"Alexa, play Wonderwall by Oasis"  
"Alexa, play The Beatles"
"Alexa, play my playlist favorites"
"Alexa, pause"
"Alexa, resume"
"Alexa, next"
```

## 🔧 Troubleshooting

### Error: "ASK CLI not found"
```bash
npm install -g ask-cli
```

### Error: "AWS credentials not configured"
```bash
aws configure
# Verify: aws sts get-caller-identity
```

### Error: "YouTube Music API not initialized"
- Verify that the Python service is running
- Check the URL in `lambda/env.json`
- Review service logs

### Error: "Skill not found on device"
- Go to alexa.amazon.com → Skills → Your Skills → Dev
- Enable the skill manually
- Wait up to 60 seconds for synchronization

### Error: "No playlists found"
- Verify that `oauth.json` is configured
- Check that you have playlists in YouTube Music
- Re-run `python3 setup.py`

## 📊 Monitoring

### View Lambda logs
```bash
# View recent logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/ask"

# View specific logs
aws logs tail /aws/lambda/ask-your-skill-name-default --follow
```

### View Python service logs
Depends on the service used:
- **Heroku**: `heroku logs --tail -a your-app-name`
- **Railway**: Control panel → Logs
- **Render**: Control panel → Logs

## 🆘 Support

If you have problems:

1. **Review logs**: Lambda and Python service
2. **Verify configuration**: URLs, credentials, oauth.json
3. **Test components**: Python service independently
4. **Consult documentation**: [Amazon Developer Docs](https://developer.amazon.com/alexa)

## 🔄 Updates

To update the skill:

```bash
# Update code
git pull origin main

# Reinstall dependencies if necessary
npm install
pip3 install -r ytmusic-service/requirements.txt

# Redeploy
ask deploy --target all
```

You now have your YouTube Music skill working! 🎵