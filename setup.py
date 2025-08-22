#!/usr/bin/env python3
"""
Configuration script for YouTube Music Alexa Skill
Generates the oauth.json file needed to authenticate with YouTube Music
"""

import json
import os
from ytmusicapi import YTMusic

def setup_youtube_music_auth():
    """Configure YouTube Music authentication"""
    print("🎵 YouTube Music Alexa Skill Configuration")
    print("=" * 50)
    
    ytmusic_dir = os.path.join(os.path.dirname(__file__), 'ytmusic-service')
    oauth_path = os.path.join(ytmusic_dir, 'oauth.json')
    
    if os.path.exists(oauth_path):
        print(f"⚠️  The oauth.json file already exists at: {oauth_path}")
        response = input("Do you want to recreate it? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("❌ Configuration canceled")
            return False
    
    print("\n📋 Instructions:")
    print("1. Open YouTube Music in your browser")
    print("2. Log in with your account")
    print("3. Open developer tools (F12)")
    print("4. Go to the 'Network' tab")
    print("5. Look for a request to 'music.youtube.com'")
    print("6. Copy the 'Cookie' header value")
    print()
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(ytmusic_dir, exist_ok=True)
        
        # Configure YTMusic
        print("🔧 Starting configuration...")
        YTMusic.setup(filepath=oauth_path)
        
        # Verify it works
        yt = YTMusic(oauth_path)
        test_search = yt.search("test", limit=1)
        
        if test_search:
            print("✅ Configuration successful!")
            print(f"📁 File saved at: {oauth_path}")
            print("\n🎉 You can now use the YouTube Music skill")
            return True
        else:
            print("❌ Error: Could not verify configuration")
            return False
            
    except Exception as e:
        print(f"❌ Error during configuration: {e}")
        print("\n💡 Tips:")
        print("- Make sure you have an active YouTube Music account")
        print("- Verify that the cookie is complete")
        print("- Try with a new browser session")
        return False

def test_configuration():
    """Test current configuration"""
    print("\n🧪 Testing configuration...")
    
    ytmusic_dir = os.path.join(os.path.dirname(__file__), 'ytmusic-service')
    oauth_path = os.path.join(ytmusic_dir, 'oauth.json')
    
    try:
        if os.path.exists(oauth_path):
            yt = YTMusic(oauth_path)
            print("✅ oauth.json file found and loaded")
        else:
            yt = YTMusic()
            print("⚠️  Using mode without authentication (limited functionality)")
        
        # Test search
        test_results = yt.search("Oasis Wonderwall", limit=3)
        if test_results:
            print(f"✅ Search working - {len(test_results)} results found")
            print(f"   Example: {test_results[0]['title']} - {test_results[0]['artists'][0]['name']}")
        else:
            print("❌ Error: Search didn't work")
            
        # Test playlists (auth only)
        if os.path.exists(oauth_path):
            try:
                playlists = yt.get_library_playlists(limit=1)
                if playlists:
                    print(f"✅ Playlist access working - {len(playlists)} playlists found")
                else:
                    print("⚠️  No playlists found (this may be normal)")
            except:
                print("⚠️  Limited playlist access")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in test: {e}")
        return False

def show_usage_info():
    """Show usage information"""
    print("\n📚 Usage information:")
    print("=" * 30)
    print("🎯 Example commands:")
    print("  • 'Alexa, abre YouTube Music'")
    print("  • 'Alexa, poné Wonderwall de Oasis'")
    print("  • 'Alexa, reproducí The Beatles'")
    print("  • 'Alexa, poné mi playlist favoritos'")
    print()
    print("🚀 To deploy the skill:")
    print("  1. npm install")
    print("  2. ask deploy")
    print()
    print("🔧 To run the service locally:")
    print("  1. cd ytmusic-service")
    print("  2. python app.py")
    print()
    print("⚠️  Remember:")
    print("  • This skill is for personal use")
    print("  • Respect YouTube Music's terms of service")
    print("  • Requires internet connection")

def main():
    """Main function"""
    print("🎵 YouTube Music Alexa Skill - Configuration")
    print("=" * 50)
    
    while True:
        print("\nWhat would you like to do?")
        print("1. Configure YouTube Music authentication")
        print("2. Test current configuration") 
        print("3. Show usage information")
        print("4. Exit")
        
        choice = input("\nChoose an option (1-4): ").strip()
        
        if choice == '1':
            setup_youtube_music_auth()
        elif choice == '2':
            test_configuration()
        elif choice == '3':
            show_usage_info()
        elif choice == '4':
            print("👋 See you later!")
            break
        else:
            print("❌ Invalid option. Choose 1-4.")

if __name__ == "__main__":
    main()