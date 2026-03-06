"""Tests for the YouTube Music API service (yt-dlp based)."""
import json
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app, stream_cache, search_cache


@pytest.fixture
def client():
    """Create a test client."""
    app.config['testing'] = True
    os.environ['API_KEY'] = ''
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear caches between tests."""
    stream_cache.clear()
    search_cache.clear()
    yield
    stream_cache.clear()
    search_cache.clear()


class TestHealthCheck:
    def test_health_returns_200(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'cache_size' in data


class TestSearch:
    def test_search_requires_query(self, client):
        response = client.post('/search',
                               data=json.dumps({'query': ''}),
                               content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    @patch('app.yt_dlp.YoutubeDL')
    def test_search_returns_results(self, mock_ydl_class, client):
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {
            'entries': [
                {
                    'id': 'abc123',
                    'title': 'Wonderwall',
                    'uploader': 'Oasis',
                    'duration': 258,
                    'thumbnails': [{'url': 'https://example.com/thumb.jpg'}],
                }
            ]
        }

        response = client.post('/search',
                               data=json.dumps({'query': 'Oasis Wonderwall'}),
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 1
        assert data['results'][0]['video_id'] == 'abc123'
        assert data['results'][0]['title'] == 'Wonderwall'
        assert data['results'][0]['artist'] == 'Oasis'

    @patch('app.yt_dlp.YoutubeDL')
    def test_search_handles_empty_results(self, mock_ydl_class, client):
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {'entries': []}

        response = client.post('/search',
                               data=json.dumps({'query': 'nonexistent song xyz'}),
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 0

    @patch('app.yt_dlp.YoutubeDL')
    def test_search_cleans_topic_artist(self, mock_ydl_class, client):
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {
            'entries': [
                {
                    'id': 'xyz789',
                    'title': 'Bohemian Rhapsody',
                    'uploader': 'Queen - Topic',
                    'duration': 360,
                }
            ]
        }

        response = client.post('/search',
                               data=json.dumps({'query': 'Bohemian Rhapsody'}),
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['results'][0]['artist'] == 'Queen'


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

        client.post('/stream',
                     data=json.dumps({'video_id': 'cached123'}),
                     content_type='application/json')
        assert mock_ydl.extract_info.call_count == 1

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
            'url': '',
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


class TestGetSongDetails:
    @patch('app.yt_dlp.YoutubeDL')
    def test_get_song_details(self, mock_ydl_class, client):
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
        mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
        mock_ydl.extract_info.return_value = {
            'title': 'Wonderwall',
            'artist': 'Oasis',
            'duration': 258,
            'album': '(What\'s the Story) Morning Glory?',
            'thumbnail': 'https://example.com/thumb.jpg',
        }

        response = client.post('/get_song',
                               data=json.dumps({'video_id': 'abc123'}),
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['title'] == 'Wonderwall'
        assert data['artist'] == 'Oasis'

    def test_get_song_requires_video_id(self, client):
        response = client.post('/get_song',
                               data=json.dumps({'video_id': ''}),
                               content_type='application/json')
        assert response.status_code == 400


class TestApiKeyAuth:
    def test_api_key_required_when_configured(self, client):
        os.environ['API_KEY'] = 'test-secret-key'
        import importlib
        import app as app_module
        importlib.reload(app_module)

        response = client.post('/search',
                               data=json.dumps({'query': 'test'}),
                               content_type='application/json')
        assert response.status_code == 401

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
