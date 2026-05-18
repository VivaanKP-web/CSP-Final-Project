from pathlib import Path

# Absolute path to the directory this file lives in.
# All image lookups are relative to an "images/" subfolder here.
DIR_PATH = Path(__file__).resolve().parent

def get_image_path(image_name):
    """Return the full path to an image in the images/ folder."""
    return Path.joinpath(DIR_PATH, "images", image_name)