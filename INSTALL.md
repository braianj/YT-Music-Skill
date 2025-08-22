# Guía de Instalación - YouTube Music Alexa Skill

Esta guía te ayudará a instalar y configurar la skill de YouTube Music paso a paso.

## 📋 Prerrequisitos

### 1. Cuentas Necesarias
- **Amazon Developer Account**: [developer.amazon.com](https://developer.amazon.com)
- **AWS Account**: [aws.amazon.com](https://aws.amazon.com) (nivel gratuito)
- **YouTube Music Premium**: Para mejores funcionalidades

### 2. Software Requerido
```bash
# Node.js (versión 18 o superior)
node --version  # Debe mostrar v18.x.x o superior

# npm (viene con Node.js)
npm --version

# Python 3.10+
python3 --version  # Debe mostrar 3.10.x o superior

# pip (viene con Python)
pip3 --version

# Git
git --version
```

### 3. Instalar Herramientas de Alexa
```bash
# ASK CLI (Alexa Skills Kit Command Line Interface)
npm install -g ask-cli

# AWS CLI
# macOS: brew install awscli
# Windows: https://aws.amazon.com/cli/
# Linux: sudo apt install awscli

# Verificar instalación
ask --version
aws --version
```

## 🚀 Instalación

### Paso 1: Clonar y Configurar el Proyecto
```bash
# Clonar el repositorio
git clone <your-repository-url>
cd youtube-music-skill

# Instalar dependencias de Node.js
npm install

# Instalar dependencias de Python
cd ytmusic-service
pip3 install -r requirements.txt
cd ..
```

### Paso 2: Configurar AWS
```bash
# Configurar credenciales de AWS
aws configure

# Se te pedirá:
# AWS Access Key ID: [Tu access key]
# AWS Secret Access Key: [Tu secret key]
# Default region name: us-east-1  (recomendado para Alexa)
# Default output format: json
```

### Paso 3: Configurar ASK CLI
```bash
# Inicializar ASK CLI
ask configure

# Seleccionar:
# - Profile: default
# - AWS Profile: default
# - Vendor ID: (se detectará automáticamente)
```

### Paso 4: Configurar YouTube Music Authentication
```bash
# Ejecutar script de configuración
python3 setup.py

# Seguir las instrucciones para:
# 1. Obtener el cookie de YouTube Music
# 2. Configurar oauth.json
# 3. Probar la conexión
```

### Paso 5: Desplegar la Skill
```bash
# Desplegar usando el script automático
./deploy.sh

# O manualmente:
ask deploy --target all
```

## 🔧 Configuración del Servicio Python

### Opción 1: Heroku (Gratuito)
```bash
# Instalar Heroku CLI
# Crear nueva app
heroku create your-ytmusic-app

# Configurar variables de entorno
heroku config:set PORT=8080

# Desplegar
cd ytmusic-service
git init
git add .
git commit -m "Initial commit"
heroku git:remote -a your-ytmusic-app
git push heroku main
```

### Opción 2: Railway (Gratuito)
1. Ve a [railway.app](https://railway.app)
2. Conecta tu cuenta de GitHub
3. Deploya el directorio `ytmusic-service`
4. Copia la URL generada

### Opción 3: Render (Gratuito)
1. Ve a [render.com](https://render.com)
2. Conecta tu repositorio
3. Configura como Web Service
4. Root Directory: `ytmusic-service`
5. Start Command: `python app.py`

### Actualizar URL del Servicio
Una vez desplegado el servicio Python, actualiza la URL:

```bash
# Editar archivo de configuración
nano lambda/env.json

# Cambiar:
{
  "YTMUSIC_API_ENDPOINT": "https://your-service-url.herokuapp.com",
  "NODE_ENV": "production"
}

# Redesplegar Lambda
ask deploy --target lambda
```

## 🧪 Pruebas

### 1. Probar el Servicio Python
```bash
# Verificar que el servicio funciona
curl -X POST https://your-service-url/search \\
  -H "Content-Type: application/json" \\
  -d '{"query":"Oasis Wonderwall"}'
```

### 2. Probar la Skill Localmente
```bash
# Usar el simulador de ASK
ask dialog --locale es-ES

# Comandos de prueba:
# > open youtube music
# > reproducí wonderwall de oasis
# > pausá
# > continuá
```

### 3. Probar en Dispositivos Alexa
1. Ve a [alexa.amazon.com](https://alexa.amazon.com)
2. Ve a "Skills" → "Your Skills" → "Dev"
3. Encuentra tu skill y habilítala
4. Di: "Alexa, abrí YouTube Music"

## 📱 Comandos de Prueba

### Español (Argentina)
```
"Alexa, abrí YouTube Music"
"Alexa, reproducí Wonderwall de Oasis"
"Alexa, poné The Beatles"
"Alexa, reproducí mi playlist favoritos"
"Alexa, pausá"
"Alexa, continuá"
"Alexa, siguiente"
```

### English (US)
```
"Alexa, open YouTube Music"
"Alexa, play Wonderwall by Oasis"  
"Alexa, play The Beatles"
"Alexa, play my playlist favorites"
"Alexa, pause"
"Alexa, resume"
"Alexa, next"
```

## 🔧 Troubleshooting

### Error: "ASK CLI not found"
```bash
npm install -g ask-cli
```

### Error: "AWS credentials not configured"
```bash
aws configure
# Verificar: aws sts get-caller-identity
```

### Error: "YouTube Music API not initialized"
- Verificar que el servicio Python esté funcionando
- Comprobar la URL en `lambda/env.json`
- Revisar logs del servicio

### Error: "Skill not found on device"
- Ir a alexa.amazon.com → Skills → Your Skills → Dev
- Habilitar la skill manualmente
- Esperar hasta 60 segundos para sincronización

### Error: "No playlists found"
- Verificar que `oauth.json` esté configurado
- Comprobar que tienes playlists en YouTube Music
- Re-ejecutar `python3 setup.py`

## 📊 Monitoreo

### Ver logs de Lambda
```bash
# Ver logs recientes
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/ask"

# Ver logs específicos
aws logs tail /aws/lambda/ask-your-skill-name-default --follow
```

### Ver logs del servicio Python
Depende del servicio usado:
- **Heroku**: `heroku logs --tail -a your-app-name`
- **Railway**: Panel de control → Logs
- **Render**: Panel de control → Logs

## 🆘 Soporte

Si tienes problemas:

1. **Revisar logs**: Lambda y servicio Python
2. **Verificar configuración**: URLs, credenciales, oauth.json
3. **Probar componentes**: Servicio Python independientemente
4. **Consultar documentación**: [Amazon Developer Docs](https://developer.amazon.com/alexa)

## 🔄 Actualización

Para actualizar la skill:

```bash
# Actualizar código
git pull origin main

# Reinstalar dependencias si es necesario
npm install
pip3 install -r ytmusic-service/requirements.txt

# Redesplegar
ask deploy --target all
```

¡Ya tienes tu skill de YouTube Music funcionando! 🎵