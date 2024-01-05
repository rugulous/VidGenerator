from secrets import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from base64 import b64encode
from urllib.parse import quote_plus
import requests
from unidecode import unidecode

token = None

def basic_auth(username, password):
    token = b64encode(f"{username}:{password}".encode('utf-8')).decode("ascii")
    return f'Basic {token}'

def get_access_token():
    response = requests.post("https://accounts.spotify.com/api/token", headers = {"Authorization": basic_auth(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET), "Content-Type": "application/x-www-form-urlencoded"}, data = {"grant_type": "client_credentials"})
    data = response.json()
    return data["access_token"]

def get_track_links(title, artist, isrc = None):
    global token
    if token is None:
        token = get_access_token()
    
    if isrc is not None:
        query = f"isrc:{isrc} artist:{artist}"
    else:
        query = f"track:{title} artist:{artist}"

    query = quote_plus(query)
    url = f"https://api.spotify.com/v1/search?q={query}&type=track&market=GB&include_external=audio"
    
    response = requests.get(url, headers = {"Authorization": f"Bearer {token}"})
    data = response.json()
    track = find_suitable_track(data["tracks"]["items"], artist)
    
    if track is None:
        if isrc is not None:
            return get_track_links(title, artist)
        
        return None
   
    return (track['preview_url'], track['album']['images'][0]['url'])

def find_suitable_track(track_list, artist):
    sanitized_artist = unidecode(artist).lower().replace("&", "and")
    for t in track_list:
        if t["preview_url"] is not None:
            for a in t["artists"]:
                check_artist = unidecode(a["name"]).lower().replace("&", "and")
                if check_artist == sanitized_artist or f"the {check_artist}" == sanitized_artist or check_artist == f"the {sanitized_artist}":
                    return t
                else:
                    print(f"{a['name']} != {artist}")

    return None
