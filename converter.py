import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import json

# Import the function from your extractor.py file
from extractor import get_apple_music_tracks

# This loads the variables from .env into your system environment
load_dotenv()

url = "https://music.apple.com/in/playlist/pl.u-11zBJyYIKg0yeYL"
extracted_tracks = get_apple_music_tracks(url)

# ==========================================
# 2. SPOTIFY AUTHENTICATION
# ==========================================
# Make sure SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, 
# and SPOTIPY_REDIRECT_URI are set in your environment.
if extracted_tracks:
    print("\nAuthenticating with Spotify...")
    scope = "playlist-modify-public playlist-modify-private"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    user_id = sp.current_user()['id']

    # ==========================================
    # 3. SEARCH SPOTIFY & GET URIs (WITH CACHE)
    # ==========================================
    print("\nSearching Spotify for matches...")

    # Initialize or load existing cache
    cache_file = "spotify_cache.json"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            track_cache = json.load(f)
    else:
        track_cache = {}

    track_uris = []

    for track in extracted_tracks:
        # Create a unique, predictable key for the cache dictionary
        cache_key = f"{track['artist']} - {track['title']}"
        
        # Check if we already searched for this track in a previous run
        if cache_key in track_cache:
            cached_uri = track_cache[cache_key]
            if cached_uri:
                track_uris.append(cached_uri)
                print(f"Cached (Found): {track['title']} by {track['artist']}")
            else:
                print(f"Cached (Not Found): {track['title']} by {track['artist']}")
            
            # Skip the Spotify API call and move directly to the next track
            continue 

        # If track is not in cache, query Spotify
        clean_title = track['title'].split(' (')[0]
        query = f"track:{clean_title} artist:{track['artist']}"
        
        result = sp.search(q=query, type='track', limit=1)
        items = result.get('tracks', {}).get('items', [])
        
        if items:
            found_uri = items[0]['uri']
            track_uris.append(found_uri)
            track_cache[cache_key] = found_uri
            print(f"Found: {track['title']} by {track['artist']}")
        else:
            # Save explicitly as None so we don't try searching for a missing song again
            track_cache[cache_key] = None
            print(f"NOT FOUND: {track['title']} by {track['artist']}")
            
        # Write to the JSON file immediately after every API call
        # This guarantees progress is saved even if the script is force-quit
        with open(cache_file, "w") as f:
            json.dump(track_cache, f, indent=4)
            
        # Respect Spotify's rolling 30-second rate limit window
        time.sleep(1.5)

    # ==========================================
    # 4. CREATE PLAYLIST AND ADD SONGS
    # ==========================================
    if track_uris:
        print("\nCreating new Spotify playlist...")
        playlist_name = "Apple Music Transfer"
        playlist_desc = "Generated automatically via Python"
        
        # Bypass the broken user_playlist_create by hitting the new API endpoint directly
        playlist = sp._post("me/playlists", payload={
            "name": playlist_name,
            "description": playlist_desc,
            "public": True
        })
        
        def chunk_list(lst, n):
            for i in range(0, len(lst), n):
                yield lst[i:i + n]

        print("Adding tracks to the playlist...")
        for chunk in chunk_list(track_uris, 100):
            # Bypass the broken playlist_add_items by hitting the new API endpoint directly
            sp._post(f"playlists/{playlist['id']}/items", payload={"uris": chunk})
            
        print(f"\nSuccess! Playlist created: {playlist['external_urls']['spotify']}")
    else:
        print("\nNo tracks were matched. Playlist was not created.")