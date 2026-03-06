"""Tests for the YouTube Music API service."""
import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, stream_cache


@pytest.fixture
def client():
    """Create a test client."""
    app.config['testing'] = True
    # Disable API key check for tests
    os.environ['API_KEY'] = ''
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear stream cache between tests."""
    stream_cache.clear()
    yield
    stream_cache.clear()


class TestHealthCheck:
    def test_health_returns_200(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'ytmusic_initialized' in data
        assert 'cache_size' in data


class TestSearch:
    @patch('app.yt')
    def test_search_requires_query(self, mock_yt, client):
        response = client.post('/search',
                               data=json.dumps({'query': ''}),
                               content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    @patch('app.yt')
    def test_search_returns_results(self, mock_yt, client):
        mock_yt.search.return_value = [
            {
                'videoId': 'abc123',
                'title': 'Wonderwall',
                'artists': [{'name': 'Oasis'}],
                'duration': '4:18',
                'thumbnails': [{'url': 'https://example.com/thumb.jpg'}],
                'album': {'name': 'Morning Glory'},
            }
        ]

        response = client.post('/search',
                               data=json.dumps({'query': 'Oasis Wonderwall'}),
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 1
        assert data['results'][0]['video_id'] == 'abc123'
        assert data['results'][0]['title'] == 'Wonderwall'
        assert data['results'][0]['artist'] == 'Oasis'
        assert 'stream_url' not in data['results'][0]  # No fake URLs

    @patch('app.yt')
    def test_search_handles_empty_results(self, mock_yt, client):
        mock_yt.search.return_value = []

        response = client.post('/search',
                               data=json.dumps({'query': 'nonexistent song xyz'}),
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0

    @patch('app.yt', None)
    def test_search_without_ytmusic_init(self, client):
        response = client.post('/search',
                               data=json.dumps({'query': 'test'}),
                               content_type='application/json')
        assert response.status_code == 500


class TestStreamExtraction:
    @patch('app.yt_dlp.YoutubeDL')
    def test_stream_requires_video_id(self, mock_ydl, client):
        response = client.post('/stream',
                               data=json.dumps({'video_id': ''}),
                               content_type='application/json')
        assert response.status_code == 400

    @patch('app.yt_dlp.YoutubeDL')
    def test_stream_extracts_audio_url(self, mock_ydl_class, client):
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {
            'url': 'https://audio-stream.example.com/audio.m4a',
            'title': 'Wonderwall',
            'artist': 'Oasis',
            'duration': 258,
            'ext': 'm4a',
        }

        response = client.post('/stream',
                               data=json.dumps({'video_id': 'abc123'}),
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['stream_url'] == 'https://audio-stream.example.com/audio.m4a'
        assert data['video_id'] == 'abc123'
        assert data['title'] == 'Wonderwall'

    @patch('app.yt_dlp.YoutubeDL')
    def test_stream_caches_results(self, mock_ydl_class, client):
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {
            'url': 'https://audio-stream.example.com/audio.m4a',
            'title': 'Test Song',
            'duration': 200,
            'ext': 'm4a',
        }

        # First request - should call yt-dlp
        client.post('/stream',
                     data=json.dumps({'video_id': 'cached123'}),
                     content_type='application/json')
        assert mock_ydl.extract_info.call_count == 1

        # Second request - should use cache
        response = client.post('/stream',
                               data=json.dumps({'video_id': 'cached123'}),
                               content_type='application/json')
        assert response.status_code == 200
        assert mock_ydl.extract_info.call_count == 1  # Not called again

    @patch('app.yt_dlp.YoutubeDL')
    def test_stream_fallback_to_formats(self, mock_ydl_class, client):
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {
            'url': '',  # No direct URL
            'title': 'Test Song',
            'duration': 200,
            'ext': 'm4a',
            'formats': [
                {'acodec': 'none', 'vcodec': 'avc1', 'url': 'https://video.url'},
                {'acodec': 'mp4a', 'vcodec': 'none', 'url': 'https://audio-only.url'},
            ]
        }

        response = client.post('/stream',
                               data=json.dumps({'video_id': 'fallback123'}),
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['stream_url'] == 'https://audio-only.url'


class TestApiKeyAuth:
    def test_api_key_required_when_configured(self, client):
        os.environ['API_KEY'] = 'test-secret-key'
        # Need to reload the module to pick up the new env var
        import importlib
        import app as app_module
        importlib.reload(app_module)

        response = client.post('/search',
                               data=json.dumps({'query': 'test'}),
                               content_type='application/json')
        assert response.status_code == 401

        # Clean up
        os.environ['API_KEY'] = ''
        importlib.reload(app_module)

    def test_health_skips_auth(self, client):
        os.environ['API_KEY'] = 'test-secret-key'
        import importlib
        import app as app_module
        importlib.reload(app_module)

        response = client.get('/health')
        assert response.status_code == 200

        os.environ['API_KEY'] = ''
        importlib.reload(app_module)


class TestPlaylists:
    @patch('app.yt')
    def test_get_playlists(self, mock_yt, client):
        mock_yt.get_library_playlists.return_value = [
            {
                'playlistId': 'PLabc123',
                'title': 'My Favorites',
                'description': 'My favorite songs',
                'count': 42,
                'thumbnails': [{'url': 'https://example.com/thumb.jpg'}]
            }
        ]

        response = client.get('/playlists')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 1
        assert data['playlists'][0]['title'] == 'My Favorites'

    @patch('app.yt')
    def test_get_playlist_songs(self, mock_yt, client):
        mock_yt.get_playlist.return_value = {
            'title': 'My Favorites',
            'description': '',
            'tracks': [
                {
                    'videoId': 'song1',
                    'title': 'Song One',
                    'artists': [{'name': 'Artist 1'}],
                    'duration': '3:30',
                    'thumbnails': [{'url': 'https://example.com/thumb1.jpg'}],
                }
            ]
        }

        response = client.get('/playlist/PLabc123')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 1
        assert data['songs'][0]['title'] == 'Song One'


class TestGetSongDetails:
    @patch('app.yt')
    def test_get_song_details(self, mock_yt, client):
        mock_yt.get_song.return_value = {
            'videoDetails': {
                'title': 'Wonderwall',
                'author': 'Oasis',
                'lengthSeconds': '258',
            }
        }

        response = client.post('/get_song',
                               data=json.dumps({'video_id': 'abc123'}),
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['title'] == 'Wonderwall'
        assert data['artist'] == 'Oasis'

    @patch('app.yt')
    def test_get_song_requires_video_id(self, mock_yt, client):
        response = client.post('/get_song',
                               data=json.dumps({'video_id': ''}),
                               content_type='application/json')
        assert response.status_code == 400
