# YouTube Music Alexa Skill

Una skill de Alexa que permite reproducir música de YouTube Music en dispositivos Echo.

## Características

- 🎵 Reproduce música de YouTube Music por voz
- 🌍 Soporte para español (Argentina) e inglés (Estados Unidos)  
- 🔍 Búsqueda por canción, artista o álbum
- ⏯️ Controles de reproducción (pausa, continuar, siguiente, anterior)
- 📱 Funciona con cualquier dispositivo Alexa

## Comandos de Voz

### Español
- "Alexa, abre YouTube Music"
- "Alexa, reproduce Wonderwall de Oasis"
- "Alexa, busca música de The Beatles"
- "Alexa, pausa" / "Alexa, continúa"

### English
- "Alexa, open YouTube Music"
- "Alexa, play Wonderwall by Oasis" 
- "Alexa, search for The Beatles music"
- "Alexa, pause" / "Alexa, resume"

## Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Alexa Device  │────│   AWS Lambda     │────│  YTMusic API    │
│                 │    │   (Node.js)      │    │  (Python)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

- **Alexa Device**: Captura comandos de voz
- **AWS Lambda**: Procesa intents y maneja la lógica de la skill
- **YTMusic Service**: API en Python que interactúa con YouTube Music

## Instalación

### Prerrequisitos

1. **Cuenta de Amazon Developer**: [developer.amazon.com](https://developer.amazon.com)
2. **AWS CLI configurado**: [Guía AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
3. **ASK CLI**: `npm install -g ask-cli`
4. **Node.js**: v18 o superior
5. **Python**: 3.10 o superior

### Configuración

1. **Clonar el repositorio**:
   ```bash
   git clone <repository-url>
   cd youtube-music-skill
   ```

2. **Instalar dependencias de Node.js**:
   ```bash
   npm install
   ```

3. **Configurar el servicio de Python**:
   ```bash
   cd ytmusic-service
   pip install -r requirements.txt
   ```

4. **Configurar autenticación de YouTube Music** (opcional):
   ```bash
   # En el directorio ytmusic-service/
   python -c "from ytmusicapi import YTMusic; YTMusic.setup(filepath='oauth.json')"
   ```
   > **Nota**: Sin oauth.json funcionará con búsquedas públicas solamente

5. **Desplegar la skill**:
   ```bash
   ask deploy
   ```

### Configuración para Argentina y Estados Unidos

La skill está configurada para funcionar en ambos países:

- **Distribución**: Estados Unidos y Argentina
- **Idiomas**: Inglés (en-US) y Español (es-ES)
- **Modo**: Privado (para uso personal)

## Desarrollo Local

### Ejecutar el servicio de Python localmente:
```bash
cd ytmusic-service
python app.py
```

### Probar la API:
```bash
curl -X POST http://localhost:8080/search \\
  -H "Content-Type: application/json" \\
  -d '{"query":"Oasis Wonderwall"}'
```

### Ejecutar tests de la skill:
```bash
ask dialog --locale es-ES
```

## Variables de Entorno

Crear un archivo `.env` en `ytmusic-service/`:

```env
PORT=8080
YTMUSIC_API_ENDPOINT=http://localhost:8080
```

## Estructura del Proyecto

```
youtube-music-skill/
├── lambda/
│   └── index.js                 # Lógica principal de Alexa
├── skill-package/
│   ├── skill.json              # Configuración de la skill
│   └── interactionModels/
│       └── custom/
│           ├── en-US.json      # Modelo en inglés
│           └── es-ES.json      # Modelo en español
├── ytmusic-service/
│   ├── app.py                  # API de YouTube Music
│   ├── requirements.txt        # Dependencias Python
│   └── oauth.json             # Autenticación (opcional)
├── package.json               # Dependencias Node.js
└── README.md
```

## Limitaciones

⚠️ **Importante**: Esta skill usa APIs no oficiales de YouTube Music:

- No está afiliada con Google/YouTube
- Puede dejar de funcionar si YouTube cambia su API
- Para uso personal/educativo solamente
- Respeta los términos de servicio de YouTube Music

## Troubleshooting

### Error: "YouTube Music API not initialized"
- Verifica que el servicio de Python esté ejecutándose
- Comprueba la configuración de `YTMUSIC_API_ENDPOINT`

### Error: "No se pudo encontrar música"
- Verifica la conexión a internet
- Prueba con búsquedas más específicas
- Comprueba los logs del servicio Python

### La skill no responde en español
- Configura tu dispositivo Alexa en español
- Verifica que el modelo `es-ES.json` esté desplegado

## Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añade nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

MIT License - Ver [LICENSE](LICENSE) para más detalles.

## Disclaimer

Esta aplicación no está afiliada, asociada, autorizada, respaldada por, o de alguna manera oficialmente conectada con Google, YouTube, YouTube Music, o cualquiera de sus subsidiarias o afiliadas.