const Alexa = require('ask-sdk-core');
const axios = require('axios');

// YouTube Music API service configuration
const YTMUSIC_API_ENDPOINT = process.env.YTMUSIC_API_ENDPOINT || 'http://localhost:8080';

// Helper function to make requests to our Python service
async function callYTMusicAPI(endpoint, params = {}) {
    try {
        const response = await axios.post(`${YTMUSIC_API_ENDPOINT}${endpoint}`, params);
        return response.data;
    } catch (error) {
        console.error('Error calling YTMusic API:', error);
        return null;
    }
}

// Intent Handler for playing music
const PlayMusicIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'PlayMusicIntent';
    },
    async handle(handlerInput) {
        const query = Alexa.getSlotValue(handlerInput.requestEnvelope, 'query');
        
        if (!query) {
            const speakOutput = handlerInput.requestEnvelope.request.locale.startsWith('es') 
                ? '¿Qué música te gustaría escuchar?' 
                : 'What music would you like to listen to?';
            
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .reprompt(speakOutput)
                .getResponse();
        }

        // Search music on YouTube Music
        const searchResult = await callYTMusicAPI('/search', { query });
        
        if (!searchResult || !searchResult.results || searchResult.results.length === 0) {
            const speakOutput = handlerInput.requestEnvelope.request.locale.startsWith('es')
                ? `No pude encontrar música para ${query}. Intenta con otra búsqueda.`
                : `I couldn't find music for ${query}. Try a different search.`;
            
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        const firstResult = searchResult.results[0];
        const speakOutput = handlerInput.requestEnvelope.request.locale.startsWith('es')
            ? `Reproduciendo ${firstResult.title} de ${firstResult.artist}`
            : `Playing ${firstResult.title} by ${firstResult.artist}`;

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .addAudioPlayerPlayDirective('REPLACE_ALL', firstResult.stream_url, firstResult.video_id, 0)
            .getResponse();
    }
};

// Intent Handler for music search
const SearchMusicIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'SearchMusicIntent';
    },
    async handle(handlerInput) {
        const artist = Alexa.getSlotValue(handlerInput.requestEnvelope, 'artist');
        const song = Alexa.getSlotValue(handlerInput.requestEnvelope, 'song');
        
        let query = '';
        if (artist) query += artist + ' ';
        if (song) query += song;
        
        const searchResult = await callYTMusicAPI('/search', { query: query.trim() });
        
        if (!searchResult || !searchResult.results || searchResult.results.length === 0) {
            const speakOutput = handlerInput.requestEnvelope.request.locale.startsWith('es')
                ? 'No encontré resultados para esa búsqueda.'
                : 'I found no results for that search.';
            
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        // If it's an artist search, play the first song directly
        const firstResult = searchResult.results[0];
        const speakOutput = handlerInput.requestEnvelope.request.locale.startsWith('es')
            ? `Reproduciendo ${firstResult.title} de ${firstResult.artist}`
            : `Playing ${firstResult.title} by ${firstResult.artist}`;

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .addAudioPlayerPlayDirective('REPLACE_ALL', firstResult.stream_url, firstResult.video_id, 0)
            .getResponse();
    }
};

// Intent Handler for playlists
const PlayPlaylistIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'PlayPlaylistIntent';
    },
    async handle(handlerInput) {
        const playlistName = Alexa.getSlotValue(handlerInput.requestEnvelope, 'playlistName');
        
        if (!playlistName) {
            const speakOutput = handlerInput.requestEnvelope.request.locale.startsWith('es')
                ? '¿Qué playlist te gustaría reproducir?'
                : 'Which playlist would you like to play?';
            
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .reprompt(speakOutput)
                .getResponse();
        }

        // Search user playlists
        const playlistsResult = await callYTMusicAPI('/playlists');
        
        if (!playlistsResult || !playlistsResult.playlists || playlistsResult.playlists.length === 0) {
            const speakOutput = handlerInput.requestEnvelope.request.locale.startsWith('es')
                ? 'No encontré playlists en tu cuenta. Asegurate de tener playlists creadas en YouTube Music.'
                : 'I couldn\'t find any playlists in your account. Make sure you have playlists created in YouTube Music.';
            
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        // Find playlist by name
        const playlist = playlistsResult.playlists.find(p => 
            p.title.toLowerCase().includes(playlistName.toLowerCase())
        );

        if (!playlist) {
            const speakOutput = handlerInput.requestEnvelope.request.locale.startsWith('es')
                ? `No encontré una playlist llamada ${playlistName}. Estas son tus playlists disponibles: ${playlistsResult.playlists.slice(0, 3).map(p => p.title).join(', ')}`
                : `I couldn't find a playlist called ${playlistName}. Here are your available playlists: ${playlistsResult.playlists.slice(0, 3).map(p => p.title).join(', ')}`;
            
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        // Get playlist songs
        const playlistSongs = await callYTMusicAPI(`/playlist/${playlist.playlist_id}`);
        
        if (!playlistSongs || !playlistSongs.songs || playlistSongs.songs.length === 0) {
            const speakOutput = handlerInput.requestEnvelope.request.locale.startsWith('es')
                ? `La playlist ${playlist.title} está vacía.`
                : `The playlist ${playlist.title} is empty.`;
            
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        // Play first song from playlist
        const firstSong = playlistSongs.songs[0];
        const speakOutput = handlerInput.requestEnvelope.request.locale.startsWith('es')
            ? `Reproduciendo la playlist ${playlist.title}. Primera canción: ${firstSong.title} de ${firstSong.artist}`
            : `Playing playlist ${playlist.title}. First song: ${firstSong.title} by ${firstSong.artist}`;

        // Save playlist songs in session for navigation
        const sessionAttributes = handlerInput.attributesManager.getSessionAttributes();
        sessionAttributes.currentPlaylist = playlistSongs.songs;
        sessionAttributes.currentIndex = 0;
        handlerInput.attributesManager.setSessionAttributes(sessionAttributes);

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .addAudioPlayerPlayDirective('REPLACE_ALL', firstSong.stream_url, firstSong.video_id, 0)
            .getResponse();
    }
};

// Intent Handlers for playback controls
const PauseIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.PauseIntent';
    },
    handle(handlerInput) {
        return handlerInput.responseBuilder
            .addAudioPlayerStopDirective()
            .getResponse();
    }
};

const ResumeIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.ResumeIntent';
    },
    handle(handlerInput) {
        return handlerInput.responseBuilder
            .addAudioPlayerPlayDirective('REPLACE_ALL', '', '', 0)
            .getResponse();
    }
};

// Launch Request Handler
const LaunchRequestHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'LaunchRequest';
    },
    handle(handlerInput) {
        const locale = handlerInput.requestEnvelope.request.locale;
        const speakOutput = locale.startsWith('es')
            ? 'Bienvenido a YouTube Music. Puedes pedirme que reproduzca cualquier canción, por ejemplo: reproduce Wonderwall de Oasis.'
            : 'Welcome to YouTube Music. You can ask me to play any song, for example: play Wonderwall by Oasis.';

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};

// Help Intent Handler
const HelpIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.HelpIntent';
    },
    handle(handlerInput) {
        const locale = handlerInput.requestEnvelope.request.locale;
        const speakOutput = locale.startsWith('es')
            ? 'Puedes pedirme que reproduzca música diciendo: reproduce seguido del nombre de la canción o artista. También puedes usar comandos como pausa, continúa, siguiente o anterior.'
            : 'You can ask me to play music by saying: play followed by the song name or artist. You can also use commands like pause, resume, next, or previous.';

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};

// Cancel and Stop Intent Handler
const CancelAndStopIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && (Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.CancelIntent'
                || Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.StopIntent');
    },
    handle(handlerInput) {
        const locale = handlerInput.requestEnvelope.request.locale;
        const speakOutput = locale.startsWith('es') ? '¡Adiós!' : 'Goodbye!';

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .addAudioPlayerStopDirective()
            .getResponse();
    }
};

// Fallback Intent Handler
const FallbackIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.FallbackIntent';
    },
    handle(handlerInput) {
        const locale = handlerInput.requestEnvelope.request.locale;
        const speakOutput = locale.startsWith('es')
            ? 'Lo siento, no entendí eso. Puedes pedirme que reproduzca música diciendo: reproduce seguido del nombre de la canción.'
            : 'Sorry, I don\'t know about that. You can ask me to play music by saying: play followed by the song name.';

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};

// Session Ended Request Handler
const SessionEndedRequestHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'SessionEndedRequest';
    },
    handle(handlerInput) {
        console.log(`~~~~ Session ended: ${JSON.stringify(handlerInput.requestEnvelope)}`);
        return handlerInput.responseBuilder.getResponse();
    }
};

// Error Handler
const ErrorHandler = {
    canHandle() {
        return true;
    },
    handle(handlerInput, error) {
        const locale = handlerInput.requestEnvelope.request.locale;
        const speakOutput = locale.startsWith('es')
            ? 'Lo siento, hubo un problema. Por favor intenta de nuevo.'
            : 'Sorry, I had trouble doing what you asked. Please try again.';

        console.log(`~~~~ Error handled: ${JSON.stringify(error)}`);

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};

// Skill Builder
exports.handler = Alexa.SkillBuilders.custom()
    .addRequestHandlers(
        LaunchRequestHandler,
        PlayMusicIntentHandler,
        SearchMusicIntentHandler,
        PlayPlaylistIntentHandler,
        PauseIntentHandler,
        ResumeIntentHandler,
        HelpIntentHandler,
        CancelAndStopIntentHandler,
        FallbackIntentHandler,
        SessionEndedRequestHandler
    )
    .addErrorHandlers(ErrorHandler)
    .withCustomUserAgent('youtube-music-alexa-skill/v1.0')
    .lambda();