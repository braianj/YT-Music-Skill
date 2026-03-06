const Alexa = require('ask-sdk-core');
const axios = require('axios');

// YouTube Music API service configuration
const YTMUSIC_API_ENDPOINT = process.env.YTMUSIC_API_ENDPOINT || 'http://localhost:8080';
const API_KEY = process.env.API_KEY || '';

// Helper function to make requests to our Python service
async function callYTMusicAPI(endpoint, params = {}, method = 'POST') {
    try {
        const config = {
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: 15000, // 15 second timeout
        };

        if (API_KEY) {
            config.headers['X-API-Key'] = API_KEY;
        }

        let response;
        if (method === 'GET') {
            response = await axios.get(`${YTMUSIC_API_ENDPOINT}${endpoint}`, config);
        } else {
            response = await axios.post(`${YTMUSIC_API_ENDPOINT}${endpoint}`, params, config);
        }
        return response.data;
    } catch (error) {
        console.error('Error calling YTMusic API:', error.message);
        return null;
    }
}

// Helper to get locale-specific messages
function getLocaleMessage(handlerInput, esMessage, enMessage) {
    const locale = handlerInput.requestEnvelope.request.locale || 'en-US';
    return locale.startsWith('es') ? esMessage : enMessage;
}

// Helper to search and play music
async function searchAndPlay(handlerInput, query) {
    if (!query) {
        const speakOutput = getLocaleMessage(
            handlerInput,
            '¿Qué música te gustaría escuchar?',
            'What music would you like to listen to?'
        );
        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }

    // Search music on YouTube Music
    const searchResult = await callYTMusicAPI('/search', { query });

    if (!searchResult || !searchResult.results || searchResult.results.length === 0) {
        const speakOutput = getLocaleMessage(
            handlerInput,
            `No pude encontrar música para ${query}. Intentá con otra búsqueda.`,
            `I couldn't find music for ${query}. Try a different search.`
        );
        return handlerInput.responseBuilder
            .speak(speakOutput)
            .getResponse();
    }

    const firstResult = searchResult.results[0];

    // Get the actual audio stream URL (critical step)
    const streamData = await callYTMusicAPI('/stream', {
        video_id: firstResult.video_id
    });

    if (!streamData || !streamData.stream_url) {
        const speakOutput = getLocaleMessage(
            handlerInput,
            'No pude obtener el audio. Por favor intentá de nuevo.',
            'I couldn\'t get the audio. Please try again.'
        );
        return handlerInput.responseBuilder
            .speak(speakOutput)
            .getResponse();
    }

    const speakOutput = getLocaleMessage(
        handlerInput,
        `Reproduciendo ${firstResult.title} de ${firstResult.artist}`,
        `Playing ${firstResult.title} by ${firstResult.artist}`
    );

    // Save current song info in session for playback controls
    const sessionAttributes = handlerInput.attributesManager.getSessionAttributes();
    sessionAttributes.currentSong = {
        video_id: firstResult.video_id,
        title: firstResult.title,
        artist: firstResult.artist,
        stream_url: streamData.stream_url,
    };
    sessionAttributes.lastSearchResults = searchResult.results;
    handlerInput.attributesManager.setSessionAttributes(sessionAttributes);

    return handlerInput.responseBuilder
        .speak(speakOutput)
        .addAudioPlayerPlayDirective(
            'REPLACE_ALL',
            streamData.stream_url,
            firstResult.video_id,
            0
        )
        .getResponse();
}

// Launch Request Handler
const LaunchRequestHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'LaunchRequest';
    },
    handle(handlerInput) {
        const speakOutput = getLocaleMessage(
            handlerInput,
            'Bienvenido a YouTube Music. Podés pedirme que reproduzca cualquier canción, por ejemplo: reproducí Wonderwall de Oasis.',
            'Welcome to YouTube Music. You can ask me to play any song, for example: play Wonderwall by Oasis.'
        );

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .reprompt(speakOutput)
            .getResponse();
    }
};

// Intent Handler for playing music
const PlayMusicIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'PlayMusicIntent';
    },
    async handle(handlerInput) {
        const query = Alexa.getSlotValue(handlerInput.requestEnvelope, 'query');
        return searchAndPlay(handlerInput, query);
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

        return searchAndPlay(handlerInput, query.trim());
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
            const speakOutput = getLocaleMessage(
                handlerInput,
                '¿Qué playlist te gustaría reproducir?',
                'Which playlist would you like to play?'
            );
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .reprompt(speakOutput)
                .getResponse();
        }

        // Search user playlists
        const playlistsResult = await callYTMusicAPI('/playlists', {}, 'POST');

        if (!playlistsResult || !playlistsResult.playlists || playlistsResult.playlists.length === 0) {
            const speakOutput = getLocaleMessage(
                handlerInput,
                'No encontré playlists en tu cuenta. Asegurate de tener playlists creadas en YouTube Music.',
                'I couldn\'t find any playlists in your account. Make sure you have playlists created in YouTube Music.'
            );
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        // Find playlist by name (fuzzy match)
        const playlist = playlistsResult.playlists.find(p =>
            p.title.toLowerCase().includes(playlistName.toLowerCase())
        );

        if (!playlist) {
            const availableNames = playlistsResult.playlists.slice(0, 3).map(p => p.title).join(', ');
            const speakOutput = getLocaleMessage(
                handlerInput,
                `No encontré una playlist llamada ${playlistName}. Tus playlists disponibles son: ${availableNames}`,
                `I couldn't find a playlist called ${playlistName}. Your available playlists are: ${availableNames}`
            );
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        // Get playlist songs
        const playlistSongs = await callYTMusicAPI(`/playlist/${playlist.playlist_id}`, {}, 'GET');

        if (!playlistSongs || !playlistSongs.songs || playlistSongs.songs.length === 0) {
            const speakOutput = getLocaleMessage(
                handlerInput,
                `La playlist ${playlist.title} está vacía.`,
                `The playlist ${playlist.title} is empty.`
            );
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        // Get stream URL for first song
        const firstSong = playlistSongs.songs[0];
        const streamData = await callYTMusicAPI('/stream', {
            video_id: firstSong.video_id
        });

        if (!streamData || !streamData.stream_url) {
            const speakOutput = getLocaleMessage(
                handlerInput,
                'No pude obtener el audio de la playlist. Intentá de nuevo.',
                'I couldn\'t get the playlist audio. Please try again.'
            );
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        const speakOutput = getLocaleMessage(
            handlerInput,
            `Reproduciendo la playlist ${playlist.title}. Primera canción: ${firstSong.title} de ${firstSong.artist}`,
            `Playing playlist ${playlist.title}. First song: ${firstSong.title} by ${firstSong.artist}`
        );

        // Save playlist songs in session for next/previous navigation
        const sessionAttributes = handlerInput.attributesManager.getSessionAttributes();
        sessionAttributes.currentPlaylist = playlistSongs.songs;
        sessionAttributes.currentIndex = 0;
        sessionAttributes.currentSong = {
            video_id: firstSong.video_id,
            title: firstSong.title,
            artist: firstSong.artist,
            stream_url: streamData.stream_url,
        };
        handlerInput.attributesManager.setSessionAttributes(sessionAttributes);

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .addAudioPlayerPlayDirective(
                'REPLACE_ALL',
                streamData.stream_url,
                firstSong.video_id,
                0
            )
            .getResponse();
    }
};

// Next song handler
const NextIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.NextIntent';
    },
    async handle(handlerInput) {
        const sessionAttributes = handlerInput.attributesManager.getSessionAttributes();
        const playlist = sessionAttributes.currentPlaylist;
        let currentIndex = sessionAttributes.currentIndex || 0;

        if (!playlist || playlist.length === 0) {
            const speakOutput = getLocaleMessage(
                handlerInput,
                'No hay una playlist activa para avanzar.',
                'There\'s no active playlist to skip forward in.'
            );
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        currentIndex = (currentIndex + 1) % playlist.length;
        const nextSong = playlist[currentIndex];

        // Get stream URL for next song
        const streamData = await callYTMusicAPI('/stream', {
            video_id: nextSong.video_id
        });

        if (!streamData || !streamData.stream_url) {
            const speakOutput = getLocaleMessage(
                handlerInput,
                'No pude obtener el audio de la siguiente canción.',
                'I couldn\'t get the audio for the next song.'
            );
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        sessionAttributes.currentIndex = currentIndex;
        sessionAttributes.currentSong = {
            video_id: nextSong.video_id,
            title: nextSong.title,
            artist: nextSong.artist,
            stream_url: streamData.stream_url,
        };
        handlerInput.attributesManager.setSessionAttributes(sessionAttributes);

        const speakOutput = getLocaleMessage(
            handlerInput,
            `Siguiente: ${nextSong.title} de ${nextSong.artist}`,
            `Next: ${nextSong.title} by ${nextSong.artist}`
        );

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .addAudioPlayerPlayDirective(
                'REPLACE_ALL',
                streamData.stream_url,
                nextSong.video_id,
                0
            )
            .getResponse();
    }
};

// Previous song handler
const PreviousIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.PreviousIntent';
    },
    async handle(handlerInput) {
        const sessionAttributes = handlerInput.attributesManager.getSessionAttributes();
        const playlist = sessionAttributes.currentPlaylist;
        let currentIndex = sessionAttributes.currentIndex || 0;

        if (!playlist || playlist.length === 0) {
            const speakOutput = getLocaleMessage(
                handlerInput,
                'No hay una playlist activa para retroceder.',
                'There\'s no active playlist to go back in.'
            );
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        currentIndex = currentIndex > 0 ? currentIndex - 1 : playlist.length - 1;
        const prevSong = playlist[currentIndex];

        const streamData = await callYTMusicAPI('/stream', {
            video_id: prevSong.video_id
        });

        if (!streamData || !streamData.stream_url) {
            const speakOutput = getLocaleMessage(
                handlerInput,
                'No pude obtener el audio de la canción anterior.',
                'I couldn\'t get the audio for the previous song.'
            );
            return handlerInput.responseBuilder
                .speak(speakOutput)
                .getResponse();
        }

        sessionAttributes.currentIndex = currentIndex;
        sessionAttributes.currentSong = {
            video_id: prevSong.video_id,
            title: prevSong.title,
            artist: prevSong.artist,
            stream_url: streamData.stream_url,
        };
        handlerInput.attributesManager.setSessionAttributes(sessionAttributes);

        const speakOutput = getLocaleMessage(
            handlerInput,
            `Anterior: ${prevSong.title} de ${prevSong.artist}`,
            `Previous: ${prevSong.title} by ${prevSong.artist}`
        );

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .addAudioPlayerPlayDirective(
                'REPLACE_ALL',
                streamData.stream_url,
                prevSong.video_id,
                0
            )
            .getResponse();
    }
};

// Playback controls
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
    async handle(handlerInput) {
        const sessionAttributes = handlerInput.attributesManager.getSessionAttributes();
        const currentSong = sessionAttributes.currentSong;

        if (currentSong && currentSong.stream_url) {
            return handlerInput.responseBuilder
                .addAudioPlayerPlayDirective(
                    'REPLACE_ALL',
                    currentSong.stream_url,
                    currentSong.video_id,
                    0
                )
                .getResponse();
        }

        const speakOutput = getLocaleMessage(
            handlerInput,
            'No hay música para continuar. Pedime que reproduzca algo.',
            'There\'s no music to resume. Ask me to play something.'
        );

        return handlerInput.responseBuilder
            .speak(speakOutput)
            .getResponse();
    }
};

// AudioPlayer event handlers
const AudioPlayerEventHandler = {
    canHandle(handlerInput) {
        return handlerInput.requestEnvelope.request.type.startsWith('AudioPlayer.');
    },
    async handle(handlerInput) {
        const audioPlayerEventName = handlerInput.requestEnvelope.request.type;

        switch (audioPlayerEventName) {
            case 'AudioPlayer.PlaybackStarted':
                console.log('Playback started');
                break;
            case 'AudioPlayer.PlaybackFinished':
                console.log('Playback finished');
                // Auto-play next song if in playlist mode
                const sessionAttributes = handlerInput.attributesManager.getSessionAttributes();
                const playlist = sessionAttributes.currentPlaylist;
                if (playlist && playlist.length > 0) {
                    let currentIndex = (sessionAttributes.currentIndex || 0) + 1;
                    if (currentIndex < playlist.length) {
                        const nextSong = playlist[currentIndex];
                        const streamData = await callYTMusicAPI('/stream', {
                            video_id: nextSong.video_id
                        });
                        if (streamData && streamData.stream_url) {
                            sessionAttributes.currentIndex = currentIndex;
                            sessionAttributes.currentSong = {
                                video_id: nextSong.video_id,
                                title: nextSong.title,
                                artist: nextSong.artist,
                                stream_url: streamData.stream_url,
                            };
                            handlerInput.attributesManager.setSessionAttributes(sessionAttributes);
                            return handlerInput.responseBuilder
                                .addAudioPlayerPlayDirective(
                                    'REPLACE_ALL',
                                    streamData.stream_url,
                                    nextSong.video_id,
                                    0
                                )
                                .getResponse();
                        }
                    }
                }
                break;
            case 'AudioPlayer.PlaybackStopped':
                console.log('Playback stopped');
                break;
            case 'AudioPlayer.PlaybackFailed':
                console.log('Playback failed:', JSON.stringify(handlerInput.requestEnvelope.request.error));
                break;
            case 'AudioPlayer.PlaybackNearlyFinished':
                console.log('Playback nearly finished');
                break;
        }

        return handlerInput.responseBuilder.getResponse();
    }
};

// Help Intent Handler
const HelpIntentHandler = {
    canHandle(handlerInput) {
        return Alexa.getRequestType(handlerInput.requestEnvelope) === 'IntentRequest'
            && Alexa.getIntentName(handlerInput.requestEnvelope) === 'AMAZON.HelpIntent';
    },
    handle(handlerInput) {
        const speakOutput = getLocaleMessage(
            handlerInput,
            'Podés pedirme que reproduzca música diciendo: reproducí seguido del nombre de la canción o artista. También podés usar comandos como pausa, continuá, siguiente o anterior.',
            'You can ask me to play music by saying: play followed by the song name or artist. You can also use commands like pause, resume, next, or previous.'
        );

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
        const speakOutput = getLocaleMessage(handlerInput, '¡Chau!', 'Goodbye!');

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
        const speakOutput = getLocaleMessage(
            handlerInput,
            'No entendí eso. Podés pedirme que reproduzca música diciendo: reproducí seguido del nombre de la canción.',
            'Sorry, I don\'t know about that. You can ask me to play music by saying: play followed by the song name.'
        );

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
        console.log(`Session ended: ${JSON.stringify(handlerInput.requestEnvelope)}`);
        return handlerInput.responseBuilder.getResponse();
    }
};

// Error Handler
const ErrorHandler = {
    canHandle() {
        return true;
    },
    handle(handlerInput, error) {
        const speakOutput = getLocaleMessage(
            handlerInput,
            'Hubo un problema. Por favor intentá de nuevo.',
            'Sorry, I had trouble doing what you asked. Please try again.'
        );

        console.log(`Error handled: ${JSON.stringify(error)}`);

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
        NextIntentHandler,
        PreviousIntentHandler,
        PauseIntentHandler,
        ResumeIntentHandler,
        AudioPlayerEventHandler,
        HelpIntentHandler,
        CancelAndStopIntentHandler,
        FallbackIntentHandler,
        SessionEndedRequestHandler
    )
    .addErrorHandlers(ErrorHandler)
    .withCustomUserAgent('youtube-music-alexa-skill/v1.0')
    .lambda();
