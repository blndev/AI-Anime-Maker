import argparse
import logging
import src.config as config
from src.logging_config import setup_logging

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='AI Anime Maker')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    return parser.parse_args()

# Parse arguments first
args = parse_arguments()

# Set debug mode based on command line argument
if args.debug:
    config.DEBUG = True

# Initialize logging with debug setting
setup_logging()
logger = logging.getLogger("app.main")

# Read configuration
config.read_configuration()

from src.UI import create_gradio_interface
import src.analytics as analytics
import src.utils as utils
import gradio as gr

logger.debug("Starting application in debug mode" if config.DEBUG else "Starting application")


if __name__ == "__main__":
    app = None
    try:
        # if config.read_configuration() == None:
        #     print("read configuration failed")

        if config.SKIP_AI:
            logger.info("AI is deactivated")
        else:
            logger.info("Initializing AI models")
            model = config.get_model()
            if model.endswith("safetensors"):
                utils.download_file_if_not_existing(url=config.get_model_url(), local_path=model)

        try:
            utils.download_file_if_not_existing(config.get_modelurl_onnx_age_googlenet(), local_path=config.get_modelfile_onnx_age_googlenet())
            utils.download_file_if_not_existing(config.get_modelurl_onnx_gender_googlenet(), local_path=config.get_modelfile_onnx_gender_googlenet())
        except Exception as e:
            logger.error("Could not detect or download face recognition models: %s", str(e))


        if config.is_analytics_enabled():
            analytics.start()
        title = config.get_app_title()
        logger.info("Starting server with title: %s", title)
        app = create_gradio_interface()
        app.launch(
            server_name="0.0.0.0",#TODO: add ip to config
            server_port=config.get_server_port(),
            share=config.is_gradio_shared(),
            show_error=config.DEBUG,
            show_api=False,
            enable_monitoring=False,
            max_file_size=12*gr.FileSize.MB
        )
        analytics.stop()
    except Exception as e:
        logger.error("Application error: %s", str(e))
    finally:
        if app != None:
            app.close()
        logger.info("Application closed")
