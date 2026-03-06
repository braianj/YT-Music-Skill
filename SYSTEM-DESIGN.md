# YouTube Music Alexa Skill - System Design & Completion Plan

## Current State Analysis

### What You Have
- **Alexa Skill package** (skill.json, interaction models in es-ES and en-US) - READY
- **Lambda handler** (Node.js, index.js) - Has a critical bug but structure is good
- **Python YTMusic service** (Flask + ytmusicapi) - Needs one critical fix
- **DigitalOcean Droplet** - Available for hosting the Python service

### What's Missing / Broken

#### CRITICAL BUG: Audio Streaming URLs Don't Work
The biggest issue in the current code is that `stream_url` is set to:
```
https://www.youtube.com/watch?v={videoId}
```
**Alexa's AudioPlayer CANNOT play YouTube page URLs.** It requires direct audio stream URLs (MP3, M3U8, AAC, etc.). The skill will search for music correctly but will fail the moment it tries to play anything.

**Solution:** Add `yt-dlp` to the Python service to extract the actual audio stream URL from YouTube. These are temporary URLs that expire after a few hours, so they must be extracted on-demand.

#### Missing Pieces
1. No `yt-dlp` integration for extracting playable audio URLs
2. Python service not deployed anywhere
3. Lambda not deployed to AWS
4. Skill not registered in Alexa Developer Console
5. No HTTPS on the Python service (required for Lambda to call it securely)
6. `lambda/env.json` has placeholder URL

---

## Proposed Architecture (Cheapest Possible)

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────────┐
│   Alexa Device  │────>│   AWS Lambda (Free)   │────>│  DigitalOcean Droplet   │
│   (Echo, etc.)  │     │   Node.js handler     │     │  (Your existing server) │
│                 │     │   $0/month             │     │                         │
└─────────────────┘     └──────────────────────┘     │  Flask + ytmusicapi     │
                                                      │  + yt-dlp               │
                                                      │  + Nginx (HTTPS)        │
                                                      │  $0 extra               │
                                                      └─────────────────────────┘
```

### Cost Breakdown

| Component | Service | Cost |
|-----------|---------|------|
| Alexa Skill hosting | AWS Lambda Free Tier | **$0** (1M requests/month free) |
| Python YTMusic API | DigitalOcean Droplet (existing) | **$0** (already paying for it) |
| HTTPS certificate | Let's Encrypt via Certbot | **$0** |
| Domain (optional) | Use Droplet IP with Nginx | **$0** |
| Amazon Developer Account | Free | **$0** |
| **TOTAL** | | **$0 extra** |

---

## Step-by-Step Completion Plan

### Phase 1: Fix the Python Service (on your Droplet)

#### 1.1 Add yt-dlp for Audio Extraction

Update `requirements.txt`:
```
ytmusicapi==1.7.0
flask==3.0.0
flask-cors==4.0.0
python-dotenv==1.0.0
requests==2.31.0
yt-dlp>=2024.1.0
```

Add a new endpoint to `app.py` that extracts the actual audio stream:

```python
import yt_dlp

@app.route('/stream', methods=['POST'])
def get_stream_url():
    """Extract the actual playable audio URL from a YouTube video ID."""
    data = request.get_json()
    video_id = data.get('video_id', '')

    if not video_id:
        return jsonify({'error': 'video_id is required'}), 400

    try:
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(
                f'https://music.youtube.com/watch?v={video_id}',
                download=False
            )
            audio_url = info.get('url', '')

            if not audio_url:
                # Fallback: look in formats
                for fmt in info.get('formats', []):
                    if fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                        audio_url = fmt['url']
                        break

            return jsonify({
                'video_id': video_id,
                'stream_url': audio_url,
                'title': info.get('title', ''),
                'duration': info.get('duration', 0),
                'expires_in': '~6 hours'
            })

    except Exception as e:
        logger.error(f"Error extracting stream: {e}")
        return jsonify({'error': str(e)}), 500
```

Also update the `/search` endpoint to NOT include fake stream_url. Instead, return just the metadata:

```python
formatted_result = {
    'video_id': result['videoId'],
    'title': result.get('title', 'Unknown Title'),
    'artist': '...',
    'duration': result.get('duration', 'Unknown'),
    'thumbnail': '...',
    # NO stream_url here - Lambda will call /stream separately
}
```

#### 1.2 Deploy on DigitalOcean Droplet

SSH into your Droplet and:

```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx certbot python3-certbot-nginx ffmpeg -y

# Create app directory
mkdir -p /opt/ytmusic-service
cd /opt/ytmusic-service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Copy your files (or git clone)
# Then install dependencies
pip install -r requirements.txt

# Install yt-dlp system-wide too (for updates)
pip install yt-dlp
```

#### 1.3 Set Up as a Systemd Service

Create `/etc/systemd/system/ytmusic.service`:
```ini
[Unit]
Description=YouTube Music API Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/ytmusic-service
Environment=PORT=8080
ExecStart=/opt/ytmusic-service/venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ytmusic
sudo systemctl start ytmusic
```

#### 1.4 Configure Nginx with HTTPS (Free with Let's Encrypt)

If you have a domain pointing to your Droplet:
```nginx
# /etc/nginx/sites-available/ytmusic
server {
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 60s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/ytmusic /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com
```

If you DON'T have a domain, you can use a free subdomain from services like:
- **DuckDNS** (duckdns.org) - completely free
- **No-IP** - free tier available
- Or use Cloudflare Tunnel (free, no domain needed)

### Phase 2: Fix the Lambda Handler

Update `lambda/index.js` to call `/stream` to get the actual audio URL before playing:

```javascript
// In PlayMusicIntentHandler, after getting search results:
const firstResult = searchResult.results[0];

// Get the actual stream URL
const streamData = await callYTMusicAPI('/stream', {
    video_id: firstResult.video_id
});

if (!streamData || !streamData.stream_url) {
    // Handle error - couldn't extract stream
    return handlerInput.responseBuilder
        .speak('No pude obtener el audio. Intenta de nuevo.')
        .getResponse();
}

return handlerInput.responseBuilder
    .speak(speakOutput)
    .addAudioPlayerPlayDirective(
        'REPLACE_ALL',
        streamData.stream_url,  // <-- actual audio URL
        firstResult.video_id,
        0
    )
    .getResponse();
```

### Phase 3: Deploy to AWS & Alexa

#### 3.1 Create Amazon Developer Account (Free)
1. Go to https://developer.amazon.com
2. Sign up (free)
3. Go to Alexa Developer Console

#### 3.2 Configure and Deploy

```bash
# Configure ASK CLI
npm install -g ask-cli
ask configure

# Update lambda/env.json with your Droplet URL
{
    "YTMUSIC_API_ENDPOINT": "https://your-domain.com",
    "NODE_ENV": "production"
}

# Deploy everything
ask deploy --target all
```

#### 3.3 Enable for Personal Use
1. Go to Alexa Developer Console
2. Find your skill → Test tab
3. Set testing to "Development"
4. Now it works on all YOUR Alexa devices

---

## Important Considerations

### Alexa AudioPlayer + YouTube: Known Challenges

1. **Stream URL Expiration**: YouTube audio URLs expire after ~6 hours. This is fine for on-demand playback but means you can't pre-cache URLs.

2. **YouTube TOS**: Using yt-dlp to extract audio streams is in a gray area regarding YouTube's Terms of Service. This is for personal use only - don't publish the skill publicly.

3. **AudioPlayer Compatibility**: Some YouTube audio formats may not be compatible with Alexa's AudioPlayer. The AudioPlayer supports:
   - MP3
   - AAC/MP4 (m4a)
   - HLS (m3u8)

   yt-dlp should be configured to prefer `m4a` format which Alexa handles well.

4. **Latency**: Extracting the stream URL with yt-dlp takes 2-5 seconds. This is within Alexa's timeout but close to the limit. Consider having Alexa say "Buscando..." while the extraction happens.

### Security

- Add an API key between Lambda and your Droplet so random people can't use your service
- Example: add a header check in Flask:

```python
API_KEY = os.environ.get('API_KEY', 'your-secret-key')

@app.before_request
def check_api_key():
    if request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
```

### Keeping yt-dlp Updated

YouTube changes their systems frequently. Set up a cron job to keep yt-dlp updated:

```bash
# Add to crontab: update yt-dlp weekly
0 3 * * 0 /opt/ytmusic-service/venv/bin/pip install --upgrade yt-dlp
```

---

## Alternative (Even Simpler): Cloudflare Tunnel

If you don't want to deal with Nginx/domains/SSL, you can use **Cloudflare Tunnel** (free):

```bash
# Install cloudflared on your Droplet
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
sudo mv cloudflared /usr/local/bin/
chmod +x /usr/local/bin/cloudflared

# Create a tunnel (one-time setup)
cloudflared tunnel login
cloudflared tunnel create ytmusic
cloudflared tunnel route dns ytmusic ytmusic.your-domain.com

# Run the tunnel
cloudflared tunnel run ytmusic
```

This gives you a free HTTPS URL without configuring Nginx or SSL certificates.

---

## Summary: What You Need to Do

1. **Fix `app.py`**: Add yt-dlp and the `/stream` endpoint
2. **Deploy Python service on your Droplet**: systemd + nginx + Let's Encrypt (or Cloudflare Tunnel)
3. **Fix `lambda/index.js`**: Call `/stream` to get real audio URLs
4. **Update `lambda/env.json`**: Point to your Droplet's URL
5. **Create Amazon Developer account** and `ask deploy`
6. **Test**: "Alexa, abrí YouTube Music"

Total additional cost: **$0** (using your existing Droplet + AWS free tier)
