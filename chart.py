from dateutil import parser
from datetime import timedelta, datetime
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import json
from tempfile import TemporaryDirectory
from time import sleep
from os import path, startfile
import subprocess
import glob
from pydub import AudioSegment
import random
from urllib.parse import quote_plus
from pathlib import Path
import shutil

spoofy_token = "BQAD97kyT9nxWq5V612_lhdhvwhXTVwthek_B4G_mwBVwkVJ4Boz8oc5P19SeLS-k3acoa0DvHpbQNGUyjrvKlW363_tdSQo-KH0LMPOooW-bJRbFDE"
colours = [
    (9, 49, 69), #darkest indigo
    (18, 135, 168), #darker alice
    (188, 161, 54), #darkest daisy
    (192, 47, 29), #ruby
    (194, 87, 26), #darkest coral
    (100, 59, 159) #royal purple
]
W = 1080
H = 1920
WHITE = (255, 255, 255)
CROSSFADE = 1000

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
            try:
                _ = int(haystack[i]) #e.g. Taylor Swift's 22
                if haystack[i + 2] != artist:
                    continue
            except:
                pass #non-numeric title
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

    query = quote_plus(query)
    url = f"https://api.spotify.com/v1/search?q={query}&type=track&market=GB&include_external=audio"
    
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

def save_track(directory, position, links, background, title, artist):
    image_path = path.join(directory, f"{position}.jpg")
    
    download_file(path.join(directory, f"{position}.mp3"), links[0])
    download_file(image_path, links[1])
    
    image = generate_image(background.copy(), image_path, title, artist)
    image.save(image_path)

def generate_image(background, album_path, title, artist):
    font = ImageFont.truetype("OpenSans-Italic.ttf", 40)
    drawer = ImageDraw.Draw(background)
    
    with Image.open(album_path) as cover_image:
        cover_image = cover_image.resize((600, 600))            
        w,h = cover_image.size
        background.paste(cover_image, (240, 300, 240 + w, 300 + h))
        text = f"{title} - {artist}"

        if len(text) <= 45:
            draw_centered_text(drawer, text, None, 930, font)
        else:
            draw_centered_text(drawer, title, None, 930, font)
            draw_centered_text(drawer, artist, None, 980, font)

    return background

def download_file(local_path, link):
    f = open(local_path, "wb")
    f.write(requests.get(link).content)
    f.close()

def generate_audio_stream(folder):
    fade = CROSSFADE / 1000
    config = "ffconcat version 1.0\n"
    
    files = glob.glob(path.join(folder, "*.mp3"))
    clip = AudioSegment.from_mp3(files[0])
    duration = (clip.duration_seconds - (fade / 2)) / 3

    config = config + f"""file start.jpg
duration {duration}
file 1.jpg
duration {duration * 2}
"""

    for file in files[1:-1]:
        segment = AudioSegment.from_mp3(file)
        file_name = f"{Path(file).stem}.jpg"
        config = config + f"file {file_name}\nduration {segment.duration_seconds - fade}\n"
        clip = clip.append(segment, crossfade=CROSSFADE)

    if(len(files) > 1):
        last = files[-1]
        segment = AudioSegment.from_mp3(last)
        duration = segment.duration_seconds / 2
        config = config + f"""file {Path(last).stem}.jpg
duration {duration}
file end.jpg
duration {duration}
file end.jpg"""
        clip = clip.append(segment, crossfade=CROSSFADE)

    write_to_file(path.join(folder, "in.ffconcat"), config)
    clip.export(path.join(folder, "audio.mp3"), format="mp3")

def generate_background(colour):
    title_font = ImageFont.truetype("font.ttf", 60)
    background = Image.new("RGB", (W, H), colour)
    drawer = ImageDraw.Draw(background)
    
    draw_centered_text(drawer, "Rank these 5 songs", None, 100, title_font)
    draw_centered_text(drawer, "without changing order", None, 200, title_font)

    for i in range(1, 6):
        drawer.text((100, 1000 + (i * 100)), str(i), font=title_font, fill=WHITE)

    return background

def draw_centered_text(drawer, text, x = None, y = None, font = None):
    _, _, w, h = drawer.textbbox((0, 0), text, font=font)
    if x is None:
        x = (W-w)/2

    if y is None:
        y = (H-h)/2

    drawer.text((x, y), text, font=font, fill=WHITE)

def generate_video(folder, date, chosen):
    tmp_file = path.join(folder, "out.mp4")
    target_file = f"content/rank-{date:%Y%m%d}"
    process = subprocess.call('ffmpeg -i in.ffconcat -i audio.mp3 -c:a copy -shortest -c:v libx264 -vf "fps=25,format=yuv420p" out.mp4', cwd=folder)
    shutil.copy(tmp_file, target_file + ".mp4")

    caption = f"""Comment your ranking! Which song is number one?

#music #uk #chart #uktop40 #charts #{date:%Y} #rank #blindrank #react #blindreact #ranking"""

    for choice in chosen:
        caption = caption + f" #{choice[1].replace(' ', '').lower()}"

    print(caption)
    write_to_file(target_file + ".txt", caption)
    startfile(path.abspath(target_file + ".mp4"))

def generate_cards(folder, colour):
    font = ImageFont.truetype("font.ttf", 80)
    emphasis_font = ImageFont.truetype("font.ttf", 100)
    start_card = Image.new("RGB", (W, H), colour)
    drawer = ImageDraw.Draw(start_card)
    draw_centered_text(drawer, "Rank these 5 songs", None, H / 3, font)
    draw_centered_text(drawer, "WITHOUT", None, H / 2, emphasis_font)
    draw_centered_text(drawer, "changing your order!", None, H * 0.66666, font)
    start_card.save(path.join(folder, "start.jpg"))
    
    end_card = Image.new("RGB", (W, H), colour)
    drawer = ImageDraw.Draw(end_card)
    draw_centered_text(drawer, "Let us know", None, (H / 2) - 50, emphasis_font)
    draw_centered_text(drawer, "your order!", None, (H / 2) + 50, emphasis_font)
    end_card.save(path.join(folder, "end.jpg"))

def random_date(limit):
    max_timestamp = int(datetime.timestamp(limit))
    chosen_timestamp = random.randrange(max_timestamp)
    date = datetime.fromtimestamp(chosen_timestamp)
    return date

def write_to_file(file, content):
    with open(file, "w") as f:
        f.write(content)

date = random_date(datetime.now()) #datetime(2023,4,9) #get_date("Please enter the date you wish to check the charts for", True)
print(f"Searching for charts for week beginning {date}...")
chart_items = get_chart_data(date)
random.shuffle(chart_items)

chosen = []
colour = random.choice(colours)
background = generate_background(colour)

with TemporaryDirectory() as tmp_dir:
    print(f"Downloading to {tmp_dir}")
    generate_cards(tmp_dir, colour)
    
    for item in chart_items:
        isrc = get_isrc(item[2], item[3])
        links = get_track_links(item[0], item[1], isrc)
        if links is None:
            print(f"Skipping {item[0]}")
            continue

        chosen.append((item[0], item[1]))
        print(f"{len(chosen)}. {item[0]} - {item[1]}")
        save_track(tmp_dir, len(chosen), links, background, item[0], item[1])

        if len(chosen) >= 5:
            break

    generate_audio_stream(tmp_dir)
    generate_video(tmp_dir, date, chosen)
