def write_to_file(file, content, mode = "w"):
    with open(file, mode) as f:
        f.write(content)

def get_main_artist(artist):
    if "FT" in artist:
        artist = artist.split("FT")[0].strip()

    if "/" in artist:
        artist = artist.split("/")[0].strip()

    if "&" in artist:
        artist = artist.split("&")[0].strip()

    return artist

def chunk(text, size):
    for start in range(0, len(text), size):
        yield text[start:start+size]
