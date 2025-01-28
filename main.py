import gradio as gr
import torch
from hashlib import sha1

import src.config as config
config.SKIP_AI = False # it's default if starting main, False = default for tests etc.

import src.utils as utils
import src.analytics as analytics
from src.UI import create_gradio_interface

# if active much more log output and ability to switch and select the used generation model 
DEBUG = False
# if active the system is not using any AI, just simulating the funcion
FAKE_AI = True
FAKE_AI_DELAY = 5 # time how long the thread sleeps to simulate generation

device = "cuda" # will be checked and set in main functions
style_details = {}

#TODO: use parameter
config.DEBUG = DEBUG

if __name__ == "__main__":
    app = None
    try:
        if config.read_configuration() == None: print("read configuration failed")
        model = config.get_model()
        if model.endswith("safetensors"):
            utils.download_file_if_not_existing(url=config.get_model_url(), local_path=model)

        print ("initializing ai models")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print (f"running on {device}")
        if FAKE_AI:
            print ("ai deactivated")
        # else:
        #     IMAGE_TO_IMAGE_PIPELINE = load_model()
        #     IMAGE_TO_TEXT_PIPELINE = load_captioner()

        if config.is_analytics_enabled():
            analytics.start()
        title = config.get_app_title()
        print (f"starting Server ""{title}""")
        app = create_gradio_interface()
        app.launch(
            share = config.is_gradio_shared(), 
            max_file_size=8*gr.FileSize.MB
            )
        analytics.stop()
    except Exception as e:
        print (e)
    finally:
        if app != None: app.close()
        print ("app closed")
