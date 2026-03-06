"""Integration tests that run against a live YTMusic API.

These tests require:
- Network access
- A valid oauth.json file (for playlist tests)

Run with: pytest tests/test_integration.py -v -m integration
Skip with: pytest -m "not integration"
"""
import json
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app


@pytest.fixture
def client():
    app.config['testing'] = True
    os.environ['API_KEY'] = ''
    with app.test_client() as client:
        yield client


@pytest.mark.integration
class TestLiveSearch:
    def test_search_returns_real_results(self, client):
        """Test that search actually returns results from YouTube Music."""
        response = client.post('/search',
                               data=json.dumps({'query': 'Oasis Wonderwall'}),
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] > 0
        assert any('wonderwall' in r['title'].lower() for r in data['results'])

    def test_search_artist(self, client):
        """Test searching by artist name."""
        response = client.post('/search',
                               data=json.dumps({'query': 'The Beatles'}),
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] > 0


@pytest.mark.integration
class TestLiveStream:
    def test_stream_extraction_works(self, client):
        """Test that yt-dlp can extract a real audio stream URL.

        This is the most critical test - if this fails, Alexa playback won't work.
        """
        # First search for a song to get a valid video_id
        search_response = client.post('/search',
                                      data=json.dumps({'query': 'Never Gonna Give You Up'}),
                                      content_type='application/json')
        search_data = json.loads(search_response.data)

        assert search_data['count'] > 0, "Search should return results"

        video_id = search_data['results'][0]['video_id']

        # Now extract the stream URL
        stream_response = client.post('/stream',
                                      data=json.dumps({'video_id': video_id}),
                                      content_type='application/json')
        assert stream_response.status_code == 200

        stream_data = json.loads(stream_response.data)
        assert stream_data['stream_url'], "Stream URL should not be empty"
        assert stream_data['stream_url'].startswith('https://'), "Stream URL should be HTTPS"
        assert stream_data['video_id'] == video_id


@pytest.mark.integration
class TestLivePlaylists:
    """These tests require oauth.json to be configured."""

    def test_get_playlists_with_auth(self, client):
        """Test getting user playlists (requires YouTube Premium auth)."""
        response = client.get('/playlists')
        # This may fail with 500 if no oauth.json is configured
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'playlists' in data
            assert isinstance(data['playlists'], list)
        else:
            pytest.skip("OAuth not configured - skipping playlist test")
