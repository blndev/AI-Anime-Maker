import os
import requests
from datetime import datetime

def download_file(url, local_path):
    # Check if the file already exists
    if not os.path.exists(local_path):
        print(f"Downloading {local_path}... this can take some minutes")
        response = requests.get(url)
        response.raise_for_status()  # Check for download errors

        # Create directory if it does not exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Write the file to the specified path
        with open(local_path, 'wb') as file:
            file.write(response.content)
        print(f"Downloaded {local_path} successfully.")
    else:
        print(f"File {local_path} already exists.")


def save_image_with_timestamp(image, folder_path, ignore_errors=False):
    try:
        # Create the folder if it does not exist
        os.makedirs(folder_path, exist_ok=True)

        # Generate a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create the filename with the timestamp
        filename = f"{timestamp}.png"  # Change the extension as needed

        # Full path to save the image
        file_path = os.path.join(folder_path, filename)

        # Save the image
        image.save(file_path)
    except Exception as e:
        print (f"save image failed: {e}")
        if not ignore_errors: raise e
