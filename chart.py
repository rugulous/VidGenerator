from dateutil import parser
from datetime import timedelta, datetime
import requests
from bs4 import BeautifulSoup
from PIL import Image
import json
from tempfile import TemporaryDirectory
from time import sleep
from os import path
import subprocess
import glob
from pydub import AudioSegment
import random

spoofy_token = "BQAEpecaJ_HBE2Px_BMAzpRttea7tUO4v5G1qQ7bJw8gtHbFclhdRWpjyrOm7sgFohMLayiXqivaUeENNPC0yu6ro8NhxuFLfmpqg0LqD4b9Ly83yEo"

def get_date(prompt, date_only = False):
    while True:
        try:
            date = input(f"{prompt}:   ")
            date = parser.parse(date)
            break
        except:
            print("I'm sorry, I couldn't understand that. Please make sure your date is in a valid format (e.g. YYYY-MM-DD)")

    if date_only:
        return date.date()

    return date

def get_chart_data(date):
    url = f"https://www.officialcharts.com/charts/singles-chart/{date:%Y%m%d}/7501/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    chart_json = soup.find(id="__NUXT_DATA__")
    chart_json = json.loads(chart_json.text)
    chart_elements = soup.find_all("div", class_="chart-item")
    chart_id = None
    items = []
    
    for item in chart_elements:
        if "chart-ad" in item["class"]:
            continue

        if chart_id is None:
            chart_id = item['data-item'].split('-')[1]

        parsed_chart = parse_chart_item(item)
        chart_item_id = find_chart_id(chart_json, *parsed_chart)
        items.append((*parsed_chart, chart_id, chart_item_id))

    return items

def find_chart_id(haystack, title, artist):
    for i in range(720, len(haystack)):
        if haystack[i] == title: #and haystack[i + 2] == artist:
            return int(haystack[i - 1])

    return None
            

def parse_chart_item(item):
    description = item.find_all("div", class_="description")[0]
    links = description.find_all("a")
    title = links[0].select("span")[1].text
    artist = links[1].text

    return (title, artist)

def get_track_links(title, artist, isrc = None):
    if isrc is not None:
        query = f"isrc:{isrc} artist:{artist}"
    else:
        query = f"track:{title} artist:{artist}"

    url = f"https://api.spotify.com/v1/search?q={query}&type=track&market=GB&include_external=audio"
    print(url)
    
    response = requests.get(url, headers = {"Authorization": f"Bearer {spoofy_token}"})
    data = response.json()
    if data['tracks']['total'] == 0 or data['tracks']['items'][0]['preview_url'] is None:
        if isrc is not None:
            return get_track_links(title, artist)
        
        return None

    track = data['tracks']['items'][0]    
    return (track['preview_url'], track['album']['images'][0]['url'])

def get_isrc(chart_id, item_id):
    data = requests.get(f"https://backstage.officialcharts.com/ajax/charted-item/chart/{chart_id}/{item_id}").json()
    return data['catNo']

def save_track(directory, position, links):
    download_file(path.join(directory, f"{position}.mp3"), links[0])
    download_file(path.join(directory, f"{position}.jpg"), links[1])

def download_file(local_path, link):
    f = open(local_path, "wb")
    f.write(requests.get(link).content)
    f.close()

def generate_audio_stream(folder):
    files = glob.glob(path.join(folder, "*.mp3"))
    clip = AudioSegment.from_mp3(files[0])
    for file in files[1:]:
        clip = clip + AudioSegment.from_mp3(file)
        
    
    clip.export(path.join(folder, "audio.mp3"), format="mp3")

date = datetime(2023,12,25) #get_date("Please enter the date you wish to check the charts for", True)
print(f"Searching for charts for week beginning {date}...")
chart_items = get_chart_data(date)
random.shuffle(chart_items)

successful = 0

with TemporaryDirectory() as tmp_dir:
    print(f"Downloading to {tmp_dir}")
    subprocess.Popen(f'explorer /select,"{tmp_dir}"')
    for item in chart_items[:10]:
        isrc = get_isrc(item[2], item[3])
        links = get_track_links(item[0], item[1], isrc)
        if links is None:
            continue

        save_track(tmp_dir, successful, links)
        successful = successful + 1

        if successful >= 5:
            break

    generate_audio_stream(tmp_dir)
    sleep(300)

print(successful)
