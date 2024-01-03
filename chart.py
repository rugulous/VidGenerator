from dateutil import parser
from datetime import timedelta, datetime
import requests
from tempfile import TemporaryDirectory
from os import path, startfile
import random
import shutil
from spotify import get_track_links
from uktop40 import get_chart_data, get_isrc
from utils import write_to_file
from video import generate_background, generate_cards, generate_image, generate_audio_stream, generate_video

colours = [
    (9, 49, 69), #darkest indigo
    (18, 135, 168), #darker alice
    (188, 161, 54), #darkest daisy
    (192, 47, 29), #ruby
    (194, 87, 26), #darkest coral
    (100, 59, 159) #royal purple
]

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

def save_track(directory, position, links, background, title, artist):
    image_path = path.join(directory, f"{position}.jpg")

    write_to_file(path.join(directory, f"{position}.mp3"), requests.get(links[0]).content, "wb")
    write_to_file(image_path, requests.get(links[1]).content, "wb")
    
    image = generate_image(background.copy(), image_path, title, artist)
    image.save(image_path)

def random_date(limit):
    max_timestamp = int(datetime.timestamp(limit))
    chosen_timestamp = random.randrange(max_timestamp)
    date = datetime.fromtimestamp(chosen_timestamp)
    return date

def generate_caption(chosen):
    caption = f"""Comment your ranking! Which song is number one?

#music #uk #chart #uktop40 #charts #{date:%Y} #rank #blindrank #react #blindreact #ranking"""

    for choice in chosen:
        parts = choice[1].replace(' ', '').lower().split("&")
        for part in parts:
            caption = caption + f" #{part}"

    return caption

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

    target_file = path.abspath(f"content/rank-{date:%Y%m%d}")
    
    raw_vid = generate_video(tmp_dir, 15000)
    caption = generate_caption(chosen)
    
    shutil.copy(raw_vid, target_file + ".mp4")
    write_to_file(target_file + ".txt", caption)
    
    startfile(target_file + ".mp4")
