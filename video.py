import glob
from utils import write_to_file, chunk
from pydub import AudioSegment
from PIL import Image, ImageDraw, ImageFont
from os import path
from pathlib import Path
import subprocess

CROSSFADE = 1000
W = 1080
H = 1920
WHITE = (255, 255, 255)

def generate_audio_stream(folder, enforce_length = None):
    fade = CROSSFADE / 1000
    
    files = glob.glob(path.join(folder, "*.mp3"))
    clip = AudioSegment.from_mp3(files[0])

    if enforce_length is not None:
        clip = trim_audio(clip, enforce_length)
    
    duration = (clip.duration_seconds - (fade / 2)) / 3
    config = f"""ffconcat version 1.0
file start.jpg
duration {duration}
file 1.jpg
duration {duration * 2}
"""

    for file in files[1:-1]:
        segment = AudioSegment.from_mp3(file)

        if enforce_length is not None:
            segment = trim_audio(segment, enforce_length)
        
        file_name = f"{Path(file).stem}.jpg"
        config = config + f"file {file_name}\nduration {segment.duration_seconds - fade}\n"
        clip = clip.append(segment, crossfade=CROSSFADE)

    if(len(files) > 1):
        last = files[-1]
        segment = AudioSegment.from_mp3(last)

        if enforce_length is not None:
            segment = trim_audio(segment, enforce_length)
        
        duration = segment.duration_seconds / 2
        config = config + f"""file {Path(last).stem}.jpg
duration {duration}
file end.jpg
duration {duration}
file end.jpg"""
        clip = clip.append(segment, crossfade=CROSSFADE)

    write_to_file(path.join(folder, "in.ffconcat"), config)
    output = path.join(folder, "audio.mp3")
    clip.export(output, format="mp3")

def trim_audio(clip, max_length):
    curr_length = clip.duration_seconds * 1000
    if(curr_length <= max_length):
        return clip

    excess_content = curr_length - max_length
    start_pos = excess_content / 2
    end_pos = start_pos + max_length

    return clip[start_pos:end_pos]

def generate_image(background, album_path, title, artist):
    font = ImageFont.truetype("OpenSans-Italic.ttf", 55)
    drawer = ImageDraw.Draw(background)
    
    with Image.open(album_path) as cover_image:
        target_size = int(W * 0.85)
        cover_image = cover_image.resize((target_size, target_size))            
        w,h = cover_image.size
        x = int((W - w) / 2)
        y = int((H - h) / 3)
        background.paste(cover_image, (x, y, x + w, y + h))
        #text = f"{title} - {artist}"

        lines_to_write = [c for c in chunk(title, 35)]
        lines_to_write += [c for c in chunk(artist, 35)]
        text_start = y + h + 30

        for i in range(len(lines_to_write)):        
            draw_centered_text(drawer, lines_to_write[i], None, text_start + (80 * i), font)

    return background

def generate_background(colour):
    #title_font = ImageFont.truetype("font.ttf", 60)
    background = Image.new("RGB", (W, H), colour)
    #drawer = ImageDraw.Draw(background)
    
    #draw_centered_text(drawer, "Rank these 5 songs", None, 100, title_font)
    #draw_centered_text(drawer, "without changing order", None, 200, title_font)

    #for i in range(1, 6):
    #    drawer.text((100, 1000 + (i * 100)), str(i), font=title_font, fill=WHITE)

    return background

def generate_cards(folder, colour, date):
    font = ImageFont.truetype("font.ttf", 80)
    emphasis_font = ImageFont.truetype("font.ttf", 100)
    start_card = Image.new("RGB", (W, H), colour)
    drawer = ImageDraw.Draw(start_card)
    start_start = H / 3
    draw_centered_text(drawer, "Rank these 5 songs", None, start_start, font)
    draw_centered_text(drawer, "WITHOUT", None, start_start + 120, emphasis_font)
    draw_centered_text(drawer, "changing your order!", None, start_start + 260, font)

    draw_centered_text(drawer, f"{date:%Y} chart edition!", None, H * 0.666, font)

    start_card.save(path.join(folder, "start.jpg"))
    
    end_card = Image.new("RGB", (W, H), colour)
    drawer = ImageDraw.Draw(end_card)
    draw_centered_text(drawer, "Let us know", None, (H / 2) - 50, emphasis_font)
    draw_centered_text(drawer, "your order!", None, (H / 2) + 50, emphasis_font)
    end_card.save(path.join(folder, "end.jpg"))

def draw_centered_text(drawer, text, x = None, y = None, font = None):
    _, _, w, h = drawer.textbbox((0, 0), text, font=font)
    if x is None:
        x = (W-w)/2

    if y is None:
        y = (H-h)/2

    drawer.text((x, y), text, font=font, fill=WHITE)

def combine_audio_and_images(folder):
    tmp_file = path.join(folder, "out.mp4")
    process = subprocess.call('ffmpeg -i in.ffconcat -i audio.mp3 -c:a copy -shortest -c:v libx264 -vf "fps=25,format=yuv420p" out.mp4', cwd=folder)
    return tmp_file

def generate_video(folder, max_track_ms = None):
    generate_audio_stream(folder, max_track_ms)
    return combine_audio_and_images(folder)
