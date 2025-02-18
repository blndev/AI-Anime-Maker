import os
import requests                 # for downloads of files
from datetime import datetime   # for timestamp
import numpy as np              # for image manipulation e.g. sepia
from PIL import Image           # for image handling
from hashlib import sha1        # generate image hash
import logging
from src import config          # for debug check

# Set up module logger
logger = logging.getLogger(__name__)

def get_all_local_models(model_folder: str, extension: str = ".safetensors"):
    """read all local models to the system"""
    safetensors_files = []
    try:
        for root, _, files in os.walk(model_folder, followlinks=True):
            for file in files:
                if file.endswith(extension):
                    relative_path = "./" + os.path.relpath(os.path.join(root, file))
                    safetensors_files.append(relative_path)
        logger.debug("Found safetensors files: %s", safetensors_files)
    except Exception as e:
        logger.error("Error listing safetensors files: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
    return safetensors_files


def download_file_if_not_existing(url, local_path):
    # Check if the file already exists
    if not os.path.exists(local_path):
        logger.info("Downloading %s... this can take some minutes", local_path)
        response = requests.get(url)
        response.raise_for_status()  # Check for download errors

        # Create directory if it does not exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Write the file to the specified path
        with open(local_path, 'wb') as file:
            file.write(response.content)
        logger.info("Downloaded %s successfully", local_path)
    else:
        logger.info("File %s already exists", local_path)


def save_image_as_file(image: Image.Image, dir: str):
    """
    saves a image as JPEG to the given directory and uses the SHA1 as filename
    return value is the full filename
    """
    try:
        if not os.path.exists(dir):
            os.makedirs(dir)
        # if we use imageEditor from Gradio:
        # try:
        #     image = image['background'] # if we use editor field
        # except:
        #     print("seems no background in image dict")
        #     print (image)
        # Convert the image to bytes and compute the SHA-1 hash
        image_bytes = image.tobytes()
        hash = sha1(image_bytes).hexdigest()
        filetype = "jpg"
        filename_hash = hash + "."+filetype
        file_path = os.path.join(dir, filename_hash)

        if not os.path.exists(file_path):
            image.save(file_path, format="JPEG")

        logger.debug("Image saved to %s", file_path)
        return file_path
    except Exception as e:
        logger.error("Error while saving image to cache: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        return None


def save_image_with_timestamp(image, folder_path, ignore_errors=False, reference=""):
    """
    saves a image in a given folder and returns the used path
    refernce: could be the SHA1 from source image to make a combined filename
    """
    try:
        # Create the folder if it does not exist
        os.makedirs(folder_path, exist_ok=True)

        # Generate a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        separator = "" if reference == "" else "-"
        # Create the filename with the timestamp
        filename = f"{reference}{separator}{timestamp}.png"  # Change the extension as needed

        # Full path to save the image
        file_path = os.path.join(folder_path, filename)

        # Save the image
        image.save(file_path)
        return file_path
    except Exception as e:
        logger.error("Save image failed: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        if not ignore_errors:
            raise e


def image_convert_to_sepia(input: Image):
    """converts a image to a sepia ton image"""

    img = np.array(input)
    sepia_filter = np.array([
        [0.393, 0.769, 0.189],
        [0.349, 0.686, 0.168],
        [0.272, 0.534, 0.131]
    ])
    sepia_img = img @ sepia_filter.T
    sepia_img = np.clip(sepia_img, 0, 255)
    sepia_img = sepia_img.astype(np.uint8)
    return Image.fromarray(sepia_img)
