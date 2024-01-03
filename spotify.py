from secrets import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from base64 import b64encode
from urllib.parse import quote_plus
import requests

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
    if data['tracks']['total'] == 0 or data['tracks']['items'][0]['preview_url'] is None:
        if isrc is not None:
            return get_track_links(title, artist)
        
        return None

    track = data['tracks']['items'][0]    
    return (track['preview_url'], track['album']['images'][0]['url'])
