import json
import requests
from bs4 import BeautifulSoup

def get_apple_music_tracks(playlist_url):
    print(f"Extracting songs from Apple Music: {playlist_url}...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(playlist_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    script_data = soup.find("script", id="serialized-server-data")
    
    # Return empty list if script data isn't found to prevent crashes
    if not script_data:
        print("Error: Could not find track data on the page.")
        return []

    json_data = json.loads(script_data.string)
    sections = json_data["data"][0]["data"]["sections"]

    extracted_tracks = []
    for section in sections:
        if section.get("itemKind") == "trackLockup":
            for item in section.get("items", []):
                extracted_tracks.append({
                    "title": item.get("title"),
                    "artist": item.get("artistName")
                })

    print(f"Extracted {len(extracted_tracks)} tracks.")
    return extracted_tracks