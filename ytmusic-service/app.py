from flask import Flask, request, jsonify
from flask_cors import CORS
from ytmusicapi import YTMusic
import yt_dlp
import os
import time
import threading
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

# Initialize YTMusic
yt = None

# Simple in-memory cache for stream URLs (they expire after ~6 hours)
stream_cache = {}
CACHE_TTL = 3600 * 4  # 4 hours (conservative, URLs last ~6h)


def initialize_ytmusic():
    global yt
    try:
        oauth_path = os.path.join(os.path.dirname(__file__), 'oauth.json')
        if os.path.exists(oauth_path):
            yt = YTMusic(oauth_path)
            logger.info("YTMusic initialized with oauth.json")
        else:
            yt = YTMusic()
            logger.info("YTMusic initialized without authentication (limited functionality)")
    except Exception as e:
        logger.error(f"Error initializing YTMusic: {e}")
        yt = None


# Initialize on startup
initialize_ytmusic()


def cleanup_cache():
    """Remove expired entries from stream cache."""
    now = time.time()
    expired = [k for k, v in stream_cache.items() if now - v['timestamp'] > CACHE_TTL]
    for k in expired:
        del stream_cache[k]


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
        'ytmusic_initialized': yt is not None,
        'cache_size': len(stream_cache)
    })


@app.route('/search', methods=['POST'])
def search_music():
    try:
        data = request.get_json()
        query = data.get('query', '')

        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400

        if not yt:
            return jsonify({'error': 'YouTube Music API not initialized'}), 500

        # Search on YouTube Music
        search_results = yt.search(query, filter='songs', limit=10)

        # Format results for Alexa (without stream_url - use /stream endpoint)
        formatted_results = []
        for result in search_results:
            if result.get('videoId'):
                artists = result.get('artists', [])
                artist_name = ', '.join([a['name'] for a in artists]) if artists else 'Unknown Artist'
                thumbnails = result.get('thumbnails', [{}])

                formatted_result = {
                    'video_id': result['videoId'],
                    'title': result.get('title', 'Unknown Title'),
                    'artist': artist_name,
                    'album': result.get('album', {}).get('name', '') if result.get('album') else '',
                    'duration': result.get('duration', 'Unknown'),
                    'thumbnail': thumbnails[-1].get('url', '') if thumbnails else '',
                }
                formatted_results.append(formatted_result)

        return jsonify({
            'query': query,
            'results': formatted_results,
            'count': len(formatted_results)
        })

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
    try:
        data = request.get_json()
        video_id = data.get('video_id', '')

        if not video_id:
            return jsonify({'error': 'video_id parameter is required'}), 400

        if not yt:
            return jsonify({'error': 'YouTube Music API not initialized'}), 500

        song_info = yt.get_song(video_id)

        if not song_info:
            return jsonify({'error': 'Song not found'}), 404

        video_details = song_info.get('videoDetails', {})
        return jsonify({
            'video_id': video_id,
            'title': video_details.get('title', 'Unknown'),
            'artist': video_details.get('author', 'Unknown'),
            'duration': video_details.get('lengthSeconds', '0'),
        })

    except Exception as e:
        logger.error(f"Error getting song details: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/playlists', methods=['GET', 'POST'])
def get_playlists():
    try:
        if not yt:
            return jsonify({'error': 'YouTube Music API not initialized'}), 500

        # Get user playlists (requires oauth authentication)
        playlists = yt.get_library_playlists(limit=25)

        formatted_playlists = []
        for playlist in playlists:
            thumbnails = playlist.get('thumbnails', [{}])
            formatted_playlist = {
                'playlist_id': playlist.get('playlistId', ''),
                'title': playlist.get('title', 'Unknown Playlist'),
                'description': playlist.get('description', ''),
                'count': playlist.get('count', 0),
                'thumbnail': thumbnails[-1].get('url', '') if thumbnails else ''
            }
            formatted_playlists.append(formatted_playlist)

        return jsonify({
            'playlists': formatted_playlists,
            'count': len(formatted_playlists)
        })

    except Exception as e:
        logger.error(f"Error getting playlists: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/playlist/<playlist_id>', methods=['GET'])
def get_playlist_songs(playlist_id):
    try:
        if not yt:
            return jsonify({'error': 'YouTube Music API not initialized'}), 500

        playlist = yt.get_playlist(playlist_id, limit=100)

        if not playlist:
            return jsonify({'error': 'Playlist not found'}), 404

        songs = []
        for track in playlist.get('tracks', []):
            if track.get('videoId'):
                artists = track.get('artists', [])
                thumbnails = track.get('thumbnails', [{}])
                song = {
                    'video_id': track['videoId'],
                    'title': track.get('title', 'Unknown Title'),
                    'artist': ', '.join([a['name'] for a in artists]) if artists else 'Unknown Artist',
                    'duration': track.get('duration', 'Unknown'),
                    'thumbnail': thumbnails[-1].get('url', '') if thumbnails else '',
                }
                songs.append(song)

        return jsonify({
            'playlist_id': playlist_id,
            'title': playlist.get('title', 'Unknown Playlist'),
            'description': playlist.get('description', ''),
            'songs': songs,
            'count': len(songs)
        })

    except Exception as e:
        logger.error(f"Error getting playlist songs: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
