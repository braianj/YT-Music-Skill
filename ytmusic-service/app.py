from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os
import time
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Key authentication
API_KEY = os.environ.get('API_KEY', '')

# Simple in-memory cache for stream URLs (they expire after ~6 hours)
stream_cache = {}
CACHE_TTL = 3600 * 4  # 4 hours (conservative, URLs last ~6h)

# Search results cache (shorter TTL since search results don't expire)
search_cache = {}
SEARCH_CACHE_TTL = 600  # 10 minutes


def cleanup_cache():
    """Remove expired entries from stream cache."""
    now = time.time()
    expired = [k for k, v in stream_cache.items() if now - v['timestamp'] > CACHE_TTL]
    for k in expired:
        del stream_cache[k]
    expired = [k for k, v in search_cache.items() if now - v['timestamp'] > SEARCH_CACHE_TTL]
    for k in expired:
        del search_cache[k]


@app.before_request
def check_api_key():
    """Validate API key if one is configured."""
    if not API_KEY:
        return  # No API key configured, skip validation

    # Skip auth for health check
    if request.path == '/health':
        return

    provided_key = request.headers.get('X-API-Key', '')
    if provided_key != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'cache_size': len(stream_cache),
        'search_cache_size': len(search_cache)
    })


@app.route('/search', methods=['POST'])
def search_music():
    """Search for songs using yt-dlp's YouTube search.

    Uses yt-dlp ytsearch instead of ytmusicapi because Google blocks
    ytmusicapi's internal API from datacenter IPs (returns 400).
    """
    try:
        data = request.get_json()
        query = data.get('query', '')
        limit = data.get('limit', 10)

        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400

        # Clamp limit
        limit = min(max(1, limit), 20)

        # Check search cache
        cache_key = f"{query}:{limit}"
        if cache_key in search_cache:
            cached = search_cache[cache_key]
            if time.time() - cached['timestamp'] < SEARCH_CACHE_TTL:
                logger.info(f"Search cache hit for '{query}'")
                return jsonify(cached['data'])

        # Use yt-dlp to search YouTube Music
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch',
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f'ytsearch{limit}:{query}'
            info = ydl.extract_info(search_query, download=False)

            formatted_results = []
            for entry in info.get('entries', []):
                if entry and entry.get('id'):
                    # Parse title to extract artist if possible
                    title = entry.get('title', 'Unknown Title')
                    artist = entry.get('uploader', entry.get('channel', 'Unknown Artist'))
                    # Clean up artist name (remove " - Topic" suffix from YT Music channels)
                    if artist and artist.endswith(' - Topic'):
                        artist = artist[:-8]

                    duration_secs = entry.get('duration')
                    if duration_secs:
                        mins = int(duration_secs) // 60
                        secs = int(duration_secs) % 60
                        duration_str = f"{mins}:{secs:02d}"
                    else:
                        duration_str = 'Unknown'

                    formatted_result = {
                        'video_id': entry['id'],
                        'title': title,
                        'artist': artist,
                        'duration': duration_str,
                        'duration_seconds': int(duration_secs) if duration_secs else 0,
                        'thumbnail': entry.get('thumbnails', [{}])[0].get('url', '') if entry.get('thumbnails') else '',
                    }
                    formatted_results.append(formatted_result)

            response_data = {
                'query': query,
                'results': formatted_results,
                'count': len(formatted_results)
            }

            # Cache search results
            search_cache[cache_key] = {
                'data': response_data,
                'timestamp': time.time()
            }

            # Cleanup old cache entries periodically
            if len(search_cache) > 100:
                cleanup_cache()

            return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error in search: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/stream', methods=['POST'])
def get_stream_url():
    """Extract the actual playable audio URL from a YouTube video ID.

    This is the critical endpoint that makes Alexa playback work.
    Alexa's AudioPlayer requires direct audio URLs (MP3, AAC/M4A, HLS).
    YouTube page URLs don't work - we need yt-dlp to extract the real stream.
    """
    try:
        data = request.get_json()
        video_id = data.get('video_id', '')

        if not video_id:
            return jsonify({'error': 'video_id is required'}), 400

        # Check cache first
        if video_id in stream_cache:
            cached = stream_cache[video_id]
            if time.time() - cached['timestamp'] < CACHE_TTL:
                logger.info(f"Cache hit for {video_id}")
                return jsonify(cached['data'])

        # Extract audio stream URL using yt-dlp
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'no_check_certificates': True,
            'geo_bypass': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            url = f'https://music.youtube.com/watch?v={video_id}'
            info = ydl.extract_info(url, download=False)

            audio_url = info.get('url', '')

            # If no direct URL, look through formats for audio-only
            if not audio_url:
                for fmt in info.get('formats', []):
                    if (fmt.get('acodec', 'none') != 'none' and
                            fmt.get('vcodec', 'none') == 'none'):
                        audio_url = fmt['url']
                        break

            if not audio_url:
                return jsonify({'error': 'Could not extract audio stream'}), 500

            response_data = {
                'video_id': video_id,
                'stream_url': audio_url,
                'title': info.get('title', ''),
                'artist': info.get('artist', info.get('uploader', '')),
                'duration': info.get('duration', 0),
                'format': info.get('ext', 'unknown'),
            }

            # Cache the result
            stream_cache[video_id] = {
                'data': response_data,
                'timestamp': time.time()
            }

            # Cleanup old cache entries periodically
            if len(stream_cache) > 50:
                cleanup_cache()

            return jsonify(response_data)

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp download error for {video_id}: {e}")
        return jsonify({'error': 'Video not available or region-restricted'}), 404
    except Exception as e:
        logger.error(f"Error extracting stream for {video_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/get_song', methods=['POST'])
def get_song_details():
    """Get song details using yt-dlp (replaces ytmusicapi.get_song which is blocked)."""
    try:
        data = request.get_json()
        video_id = data.get('video_id', '')

        if not video_id:
            return jsonify({'error': 'video_id parameter is required'}), 400

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            url = f'https://music.youtube.com/watch?v={video_id}'
            info = ydl.extract_info(url, download=False)

            artist = info.get('artist', info.get('uploader', info.get('channel', 'Unknown')))
            if artist and artist.endswith(' - Topic'):
                artist = artist[:-8]

            return jsonify({
                'video_id': video_id,
                'title': info.get('title', 'Unknown'),
                'artist': artist,
                'duration': info.get('duration', 0),
                'album': info.get('album', ''),
                'thumbnail': info.get('thumbnail', ''),
            })

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp error getting song details for {video_id}: {e}")
        return jsonify({'error': 'Song not found or unavailable'}), 404
    except Exception as e:
        logger.error(f"Error getting song details: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
