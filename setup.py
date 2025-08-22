#!/usr/bin/env python3
"""
Script de configuración para YouTube Music Alexa Skill
Genera el archivo oauth.json necesario para autenticar con YouTube Music
"""

import json
import os
from ytmusicapi import YTMusic

def setup_youtube_music_auth():
    """Configura la autenticación con YouTube Music"""
    print("🎵 Configuración de YouTube Music Alexa Skill")
    print("=" * 50)
    
    ytmusic_dir = os.path.join(os.path.dirname(__file__), 'ytmusic-service')
    oauth_path = os.path.join(ytmusic_dir, 'oauth.json')
    
    if os.path.exists(oauth_path):
        print(f"⚠️  El archivo oauth.json ya existe en: {oauth_path}")
        response = input("¿Deseas recrearlo? (y/N): ").strip().lower()
        if response not in ['y', 'yes', 'sí', 'si']:
            print("❌ Configuración cancelada")
            return False
    
    print("\n📋 Instrucciones:")
    print("1. Abre YouTube Music en tu navegador")
    print("2. Inicia sesión con tu cuenta")
    print("3. Abre las herramientas de desarrollador (F12)")
    print("4. Ve a la pestaña 'Network' o 'Red'")
    print("5. Busca una petición a 'music.youtube.com'")
    print("6. Copia el valor del header 'Cookie'")
    print()
    
    try:
        # Crear directorio si no existe
        os.makedirs(ytmusic_dir, exist_ok=True)
        
        # Configurar YTMusic
        print("🔧 Iniciando configuración...")
        YTMusic.setup(filepath=oauth_path)
        
        # Verificar que funciona
        yt = YTMusic(oauth_path)
        test_search = yt.search("test", limit=1)
        
        if test_search:
            print("✅ Configuración exitosa!")
            print(f"📁 Archivo guardado en: {oauth_path}")
            print("\n🎉 Ya puedes usar la skill de YouTube Music")
            return True
        else:
            print("❌ Error: No se pudo verificar la configuración")
            return False
            
    except Exception as e:
        print(f"❌ Error durante la configuración: {e}")
        print("\n💡 Consejos:")
        print("- Asegúrate de tener una cuenta de YouTube Music activa")
        print("- Verifica que el cookie esté completo")
        print("- Intenta con una sesión nueva del navegador")
        return False

def test_configuration():
    """Prueba la configuración actual"""
    print("\n🧪 Probando configuración...")
    
    ytmusic_dir = os.path.join(os.path.dirname(__file__), 'ytmusic-service')
    oauth_path = os.path.join(ytmusic_dir, 'oauth.json')
    
    try:
        if os.path.exists(oauth_path):
            yt = YTMusic(oauth_path)
            print("✅ Archivo oauth.json encontrado y cargado")
        else:
            yt = YTMusic()
            print("⚠️  Usando modo sin autenticación (funcionalidad limitada)")
        
        # Probar búsqueda
        test_results = yt.search("Oasis Wonderwall", limit=3)
        if test_results:
            print(f"✅ Búsqueda funcionando - {len(test_results)} resultados encontrados")
            print(f"   Ejemplo: {test_results[0]['title']} - {test_results[0]['artists'][0]['name']}")
        else:
            print("❌ Error: Búsqueda no funcionó")
            
        # Probar playlists (solo con auth)
        if os.path.exists(oauth_path):
            try:
                playlists = yt.get_library_playlists(limit=1)
                if playlists:
                    print(f"✅ Acceso a playlists funcionando - {len(playlists)} playlists encontradas")
                else:
                    print("⚠️  No se encontraron playlists (puede ser normal)")
            except:
                print("⚠️  Acceso a playlists limitado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en la prueba: {e}")
        return False

def show_usage_info():
    """Muestra información de uso"""
    print("\n📚 Información de uso:")
    print("=" * 30)
    print("🎯 Comandos de ejemplo:")
    print("  • 'Alexa, abre YouTube Music'")
    print("  • 'Alexa, poné Wonderwall de Oasis'")
    print("  • 'Alexa, reproducí The Beatles'")
    print("  • 'Alexa, poné mi playlist favoritos'")
    print()
    print("🚀 Para desplegar la skill:")
    print("  1. npm install")
    print("  2. ask deploy")
    print()
    print("🔧 Para ejecutar el servicio localmente:")
    print("  1. cd ytmusic-service")
    print("  2. python app.py")
    print()
    print("⚠️  Recuerda:")
    print("  • Esta skill es para uso personal")
    print("  • Respeta los términos de YouTube Music")
    print("  • Requiere conexión a internet")

def main():
    """Función principal"""
    print("🎵 YouTube Music Alexa Skill - Configuración")
    print("=" * 50)
    
    while True:
        print("\n¿Qué deseas hacer?")
        print("1. Configurar autenticación de YouTube Music")
        print("2. Probar configuración actual") 
        print("3. Mostrar información de uso")
        print("4. Salir")
        
        choice = input("\nElige una opción (1-4): ").strip()
        
        if choice == '1':
            setup_youtube_music_auth()
        elif choice == '2':
            test_configuration()
        elif choice == '3':
            show_usage_info()
        elif choice == '4':
            print("👋 ¡Hasta luego!")
            break
        else:
            print("❌ Opción inválida. Elige 1-4.")

if __name__ == "__main__":
    main()