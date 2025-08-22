# YouTube Music Alexa Skill

An Alexa skill that allows playing YouTube Music on Echo devices.

## Features

- 🎵 Play YouTube Music via voice commands
- 🌍 Support for Spanish (Argentina) and English (United States)  
- 🔍 Search by song, artist, or album
- ⏯️ Playback controls (pause, resume, next, previous)
- 📱 Works with any Alexa device

## Voice Commands

### Spanish
- "Alexa, abre YouTube Music"
- "Alexa, reproduce Wonderwall de Oasis"
- "Alexa, busca música de The Beatles"
- "Alexa, pausa" / "Alexa, continúa"

### English
- "Alexa, open YouTube Music"
- "Alexa, play Wonderwall by Oasis" 
- "Alexa, search for The Beatles music"
- "Alexa, pause" / "Alexa, resume"

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Alexa Device  │────│   AWS Lambda     │────│  YTMusic API    │
│                 │    │   (Node.js)      │    │  (Python)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

- **Alexa Device**: Captures voice commands
- **AWS Lambda**: Processes intents and handles skill logic
- **YTMusic Service**: Python API that interacts with YouTube Music

## Installation

### Prerequisites

1. **Amazon Developer Account**: [developer.amazon.com](https://developer.amazon.com)
2. **Configured AWS CLI**: [AWS CLI Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3. **ASK CLI**: `npm install -g ask-cli`
4. **Node.js**: v18 or higher
5. **Python**: 3.10 or higher

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd youtube-music-skill
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Configure the Python service**:
   ```bash
   cd ytmusic-service
   pip install -r requirements.txt
   ```

4. **Configure YouTube Music authentication** (optional):
   ```bash
   # In the ytmusic-service/ directory
   python -c "from ytmusicapi import YTMusic; YTMusic.setup(filepath='oauth.json')"
   ```
   > **Note**: Without oauth.json, it will work with public searches only

5. **Deploy the skill**:
   ```bash
   ask deploy
   ```

### Configuration for Argentina and United States

The skill is configured to work in both countries:

- **Distribution**: United States and Argentina
- **Languages**: English (en-US) and Spanish (es-ES)
- **Mode**: Private (for personal use)

## Local Development

### Run the Python service locally:
```bash
cd ytmusic-service
python app.py
```

### Test the API:
```bash
curl -X POST http://localhost:8080/search \\
  -H "Content-Type: application/json" \\
  -d '{"query":"Oasis Wonderwall"}'
```

### Run skill tests:
```bash
ask dialog --locale es-ES
```

## Environment Variables

Create a `.env` file in `ytmusic-service/`:

```env
PORT=8080
YTMUSIC_API_ENDPOINT=http://localhost:8080
```

## Project Structure

```
youtube-music-skill/
├── lambda/
│   └── index.js                 # Main Alexa logic
├── skill-package/
│   ├── skill.json              # Skill configuration
│   └── interactionModels/
│       └── custom/
│           ├── en-US.json      # English model
│           └── es-ES.json      # Spanish model
├── ytmusic-service/
│   ├── app.py                  # YouTube Music API
│   ├── requirements.txt        # Python dependencies
│   └── oauth.json             # Authentication (optional)
├── package.json               # Node.js dependencies
└── README.md
```

## Limitations

⚠️ **Important**: This skill uses unofficial YouTube Music APIs:

- Not affiliated with Google/YouTube
- May stop working if YouTube changes their API
- For personal/educational use only
- Respect YouTube Music's terms of service

## Troubleshooting

### Error: "YouTube Music API not initialized"
- Verify that the Python service is running
- Check the `YTMUSIC_API_ENDPOINT` configuration

### Error: "Could not find music"
- Check internet connection
- Try more specific searches
- Check Python service logs

### Skill doesn't respond in Spanish
- Configure your Alexa device in Spanish
- Verify that the `es-ES.json` model is deployed

## Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Create a Pull Request

## License

MIT License - See [LICENSE](LICENSE) for more details.

## Disclaimer

This application is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Google, YouTube, YouTube Music, or any of their subsidiaries or affiliates.