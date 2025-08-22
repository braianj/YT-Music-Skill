from flask import Flask, request, jsonify
from flask_cors import CORS
from ytmusicapi import YTMusic
import os
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar YTMusic
yt = None

def initialize_ytmusic():
    global yt
    try:
        oauth_path = os.path.join(os.path.dirname(__file__), 'oauth.json')
        if os.path.exists(oauth_path):
            yt = YTMusic(oauth_path)
            logger.info("YTMusic initialized with oauth.json")
        else:
            yt = YTMusic()
            logger.info("YTMusic initialized without authentication")
    except Exception as e:
        logger.error(f"Error initializing YTMusic: {e}")
        yt = None

# Inicializar al arrancar
initialize_ytmusic()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'ytmusic_initialized': yt is not None
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
        
        # Buscar en YouTube Music
        search_results = yt.search(query, filter='songs', limit=10)
        
        # Formatear resultados para Alexa
        formatted_results = []
        for result in search_results:
            if result.get('videoId'):
                formatted_result = {
                    'video_id': result['videoId'],
                    'title': result.get('title', 'Unknown Title'),
                    'artist': ', '.join([artist['name'] for artist in result.get('artists', [])]) if result.get('artists') else 'Unknown Artist',
                    'duration': result.get('duration', 'Unknown'),
                    'thumbnail': result.get('thumbnails', [{}])[-1].get('url', ''),
                    'stream_url': f"https://www.youtube.com/watch?v={result['videoId']}"
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

@app.route('/get_song', methods=['POST'])
def get_song_details():
    try:
        data = request.get_json()
        video_id = data.get('video_id', '')
        
        if not video_id:
            return jsonify({'error': 'video_id parameter is required'}), 400
            
        if not yt:
            return jsonify({'error': 'YouTube Music API not initialized'}), 500
        
        # Obtener detalles de la canción
        song_info = yt.get_song(video_id)
        
        if not song_info:
            return jsonify({'error': 'Song not found'}), 404
        
        return jsonify({
            'video_id': video_id,
            'title': song_info.get('videoDetails', {}).get('title', 'Unknown'),
            'artist': song_info.get('videoDetails', {}).get('author', 'Unknown'),
            'duration': song_info.get('videoDetails', {}).get('lengthSeconds', '0'),
            'stream_url': f"https://www.youtube.com/watch?v={video_id}"
        })
        
    except Exception as e:
        logger.error(f"Error getting song details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/playlists', methods=['GET'])
def get_playlists():
    try:
        if not yt:
            return jsonify({'error': 'YouTube Music API not initialized'}), 500
        
        # Obtener playlists del usuario (requiere autenticación)
        playlists = yt.get_library_playlists(limit=25)
        
        formatted_playlists = []
        for playlist in playlists:
            formatted_playlist = {
                'playlist_id': playlist.get('playlistId', ''),
                'title': playlist.get('title', 'Unknown Playlist'),
                'description': playlist.get('description', ''),
                'count': playlist.get('count', 0),
                'thumbnail': playlist.get('thumbnails', [{}])[-1].get('url', '') if playlist.get('thumbnails') else ''
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
        
        # Obtener canciones de la playlist
        playlist = yt.get_playlist(playlist_id, limit=100)
        
        if not playlist:
            return jsonify({'error': 'Playlist not found'}), 404
        
        songs = []
        for track in playlist.get('tracks', []):
            if track.get('videoId'):
                song = {
                    'video_id': track['videoId'],
                    'title': track.get('title', 'Unknown Title'),
                    'artist': ', '.join([artist['name'] for artist in track.get('artists', [])]) if track.get('artists') else 'Unknown Artist',
                    'duration': track.get('duration', 'Unknown'),
                    'thumbnail': track.get('thumbnails', [{}])[-1].get('url', '') if track.get('thumbnails') else '',
                    'stream_url': f"https://www.youtube.com/watch?v={track['videoId']}"
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