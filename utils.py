def write_to_file(file, content, mode = "w"):
    with open(file, mode) as f:
        f.write(content)
