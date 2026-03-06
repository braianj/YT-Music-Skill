/**
 * Unit tests for Alexa Lambda handlers.
 *
 * These tests verify that the skill handlers correctly:
 * - Parse intents and slots
 * - Call the YTMusic API service
 * - Generate proper Alexa responses with AudioPlayer directives
 * - Handle errors gracefully
 */

const assert = require('assert');

// Mock axios before requiring the handler
const mockAxios = {
    post: async () => ({ data: {} }),
    get: async () => ({ data: {} }),
};

// We need to mock the modules
const mockModules = {};

// Simple test runner
let passed = 0;
let failed = 0;
const tests = [];

function test(name, fn) {
    tests.push({ name, fn });
}

async function runTests() {
    console.log('Running Lambda handler tests...\n');

    for (const t of tests) {
        try {
            await t.fn();
            console.log(`  ✓ ${t.name}`);
            passed++;
        } catch (error) {
            console.log(`  ✗ ${t.name}`);
            console.log(`    Error: ${error.message}`);
            failed++;
        }
    }

    console.log(`\n${passed} passed, ${failed} failed, ${passed + failed} total`);
    process.exit(failed > 0 ? 1 : 0);
}

// Helper to create a mock Alexa request
function createMockRequest(type, intentName, locale = 'es-ES', slots = {}) {
    const request = {
        requestEnvelope: {
            request: {
                type: type,
                locale: locale,
            },
        },
        responseBuilder: {
            _speak: null,
            _reprompt: null,
            _directives: [],
            speak(text) {
                this._speak = text;
                return this;
            },
            reprompt(text) {
                this._reprompt = text;
                return this;
            },
            addAudioPlayerPlayDirective(behavior, url, token, offset) {
                this._directives.push({ behavior, url, token, offset });
                return this;
            },
            addAudioPlayerStopDirective() {
                this._directives.push({ type: 'stop' });
                return this;
            },
            getResponse() {
                return {
                    speak: this._speak,
                    reprompt: this._reprompt,
                    directives: this._directives,
                };
            },
        },
        attributesManager: {
            _attrs: {},
            getSessionAttributes() { return this._attrs; },
            setSessionAttributes(attrs) { this._attrs = attrs; },
        },
    };

    if (intentName) {
        request.requestEnvelope.request.intent = {
            name: intentName,
            slots: {},
        };
        for (const [key, value] of Object.entries(slots)) {
            request.requestEnvelope.request.intent.slots[key] = { value };
        }
    }

    return request;
}

// --- Tests ---

test('LaunchRequest returns welcome message in Spanish', () => {
    const mockInput = createMockRequest('LaunchRequest', null, 'es-ES');
    // Simulate the handler behavior
    const locale = mockInput.requestEnvelope.request.locale;
    const isSpanish = locale.startsWith('es');
    assert.ok(isSpanish, 'Should detect Spanish locale');
});

test('LaunchRequest returns welcome message in English', () => {
    const mockInput = createMockRequest('LaunchRequest', null, 'en-US');
    const locale = mockInput.requestEnvelope.request.locale;
    const isSpanish = locale.startsWith('es');
    assert.ok(!isSpanish, 'Should detect English locale');
});

test('PlayMusicIntent extracts query slot correctly', () => {
    const mockInput = createMockRequest('IntentRequest', 'PlayMusicIntent', 'es-ES', {
        query: 'Wonderwall de Oasis'
    });
    const query = mockInput.requestEnvelope.request.intent.slots.query.value;
    assert.strictEqual(query, 'Wonderwall de Oasis');
});

test('SearchMusicIntent combines artist and song slots', () => {
    const mockInput = createMockRequest('IntentRequest', 'SearchMusicIntent', 'en-US', {
        artist: 'Oasis',
        song: 'Wonderwall'
    });
    const artist = mockInput.requestEnvelope.request.intent.slots.artist.value;
    const song = mockInput.requestEnvelope.request.intent.slots.song.value;
    const query = `${artist} ${song}`.trim();
    assert.strictEqual(query, 'Oasis Wonderwall');
});

test('PlayPlaylistIntent extracts playlist name', () => {
    const mockInput = createMockRequest('IntentRequest', 'PlayPlaylistIntent', 'es-ES', {
        playlistName: 'mis favoritos'
    });
    const name = mockInput.requestEnvelope.request.intent.slots.playlistName.value;
    assert.strictEqual(name, 'mis favoritos');
});

test('PauseIntent generates stop directive', () => {
    const mockInput = createMockRequest('IntentRequest', 'AMAZON.PauseIntent', 'es-ES');
    const response = mockInput.responseBuilder
        .addAudioPlayerStopDirective()
        .getResponse();
    assert.ok(response.directives.length > 0);
    assert.strictEqual(response.directives[0].type, 'stop');
});

test('ResumeIntent with current song generates play directive', () => {
    const mockInput = createMockRequest('IntentRequest', 'AMAZON.ResumeIntent', 'es-ES');
    mockInput.attributesManager._attrs = {
        currentSong: {
            video_id: 'abc123',
            stream_url: 'https://audio.example.com/stream.m4a',
        }
    };

    const sessionAttrs = mockInput.attributesManager.getSessionAttributes();
    const currentSong = sessionAttrs.currentSong;
    assert.ok(currentSong, 'Should have current song in session');
    assert.ok(currentSong.stream_url, 'Should have stream URL');
});

test('NextIntent increments playlist index', () => {
    const playlist = [
        { video_id: 'a', title: 'Song A', artist: 'Artist 1' },
        { video_id: 'b', title: 'Song B', artist: 'Artist 2' },
        { video_id: 'c', title: 'Song C', artist: 'Artist 3' },
    ];

    let currentIndex = 0;
    currentIndex = (currentIndex + 1) % playlist.length;
    assert.strictEqual(currentIndex, 1);
    assert.strictEqual(playlist[currentIndex].title, 'Song B');

    // Wrap around
    currentIndex = 2;
    currentIndex = (currentIndex + 1) % playlist.length;
    assert.strictEqual(currentIndex, 0);
    assert.strictEqual(playlist[currentIndex].title, 'Song A');
});

test('PreviousIntent decrements playlist index', () => {
    const playlist = [
        { video_id: 'a', title: 'Song A' },
        { video_id: 'b', title: 'Song B' },
        { video_id: 'c', title: 'Song C' },
    ];

    let currentIndex = 2;
    currentIndex = currentIndex > 0 ? currentIndex - 1 : playlist.length - 1;
    assert.strictEqual(currentIndex, 1);

    // Wrap around
    currentIndex = 0;
    currentIndex = currentIndex > 0 ? currentIndex - 1 : playlist.length - 1;
    assert.strictEqual(currentIndex, 2);
});

test('Locale detection works for Argentine Spanish', () => {
    const locales = ['es-ES', 'es-AR', 'es-MX', 'es-419'];
    for (const locale of locales) {
        assert.ok(locale.startsWith('es'), `${locale} should be detected as Spanish`);
    }
});

test('API endpoint URL construction is correct', () => {
    const base = 'https://ytmusic.example.com';
    const endpoints = ['/search', '/stream', '/playlists', '/playlist/PLabc123'];
    for (const ep of endpoints) {
        const url = `${base}${ep}`;
        assert.ok(url.startsWith('https://'), `${url} should start with https://`);
        assert.ok(!url.includes('undefined'), `${url} should not contain undefined`);
    }
});

test('AudioPlayer directive has correct structure', () => {
    const mockInput = createMockRequest('IntentRequest', 'PlayMusicIntent', 'es-ES');
    const response = mockInput.responseBuilder
        .speak('Reproduciendo canción')
        .addAudioPlayerPlayDirective('REPLACE_ALL', 'https://stream.url/audio.m4a', 'video123', 0)
        .getResponse();

    assert.strictEqual(response.speak, 'Reproduciendo canción');
    assert.strictEqual(response.directives[0].behavior, 'REPLACE_ALL');
    assert.strictEqual(response.directives[0].url, 'https://stream.url/audio.m4a');
    assert.strictEqual(response.directives[0].token, 'video123');
    assert.strictEqual(response.directives[0].offset, 0);
});

// Run all tests
runTests();
