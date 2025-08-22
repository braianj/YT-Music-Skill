from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add the parent directory to Python path to import ytmusicapi
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from ytmusicapi import YTMusic
except ImportError:
    # Fallback if ytmusicapi is not available
    YTMusic = None

class handler(BaseHTTPRequestHandler):
    def __init__(self):
        # Initialize YTMusic
        self.yt = None
        if YTMusic:
            try:
                # Try to load with oauth if available
                oauth_path = os.path.join(os.path.dirname(__file__), '..', 'oauth.json')
                if os.path.exists(oauth_path):
                    self.yt = YTMusic(oauth_path)
                else:
                    self.yt = YTMusic()
            except Exception as e:
                print(f"Error initializing YTMusic: {e}")
                self.yt = None

    def do_POST(self):
        if self.path == '/search':
            return self.handle_search()
        elif self.path == '/playlists':
            return self.handle_playlists()
        elif self.path.startswith('/playlist/'):
            playlist_id = self.path.split('/')[-1]
            return self.handle_playlist_songs(playlist_id)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'ytmusic_initialized': self.yt is not None
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def handle_search(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            query = data.get('query', '')
            if not query:
                self.send_error_response('Query parameter is required', 400)
                return
                
            if not self.yt:
                self.send_error_response('YouTube Music API not initialized', 500)
                return
            
            # Search in YouTube Music
            search_results = self.yt.search(query, filter='songs', limit=10)
            
            # Format results for Alexa
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
            
            response = {
                'query': query,
                'results': formatted_results,
                'count': len(formatted_results)
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_playlists(self):
        try:
            if not self.yt:
                self.send_error_response('YouTube Music API not initialized', 500)
                return
            
            # Get user playlists (requires authentication)
            playlists = self.yt.get_library_playlists(limit=25)
            
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
            
            response = {
                'playlists': formatted_playlists,
                'count': len(formatted_playlists)
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_playlist_songs(self, playlist_id):
        try:
            if not self.yt:
                self.send_error_response('YouTube Music API not initialized', 500)
                return
            
            # Get playlist songs
            playlist = self.yt.get_playlist(playlist_id, limit=100)
            
            if not playlist:
                self.send_error_response('Playlist not found', 404)
                return
            
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
            
            response = {
                'playlist_id': playlist_id,
                'title': playlist.get('title', 'Unknown Playlist'),
                'description': playlist.get('description', ''),
                'songs': songs,
                'count': len(songs)
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            self.send_error_response(str(e), 500)

    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_error_response(self, message, status_code):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        error_response = {'error': message}
        self.wfile.write(json.dumps(error_response).encode())

# Vercel expects this format
def handler_func(request):
    h = handler()
    h.setup(request)
    return h