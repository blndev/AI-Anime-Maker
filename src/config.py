
from configparser import ConfigParser
import os
import logging
from src.logging_config import setup_logging

# property used from other areas like AI Module
# can finally be configured in setting GenAI/skip (read while load fuinction)
# it's implemented as property, so that it can be change on runtime
# helps to reduce easting storage for torch etc on build systems
SKIP_AI = os.getenv("SKIP_GENAI") == "1"
SKIP_ONNX = os.getenv("SKIP_ONNX") == "1"
DEBUG = False

# Set up module logger
logger = logging.getLogger(__name__)

# Initialize logging
setup_logging()


# this variable is used from unittests to inject configuration values!
current_config = None

# Access values with default fallback
def get_config_value(section, option, default=None):
    global current_config
    if current_config == None: read_configuration()
    if current_config.has_option(section, option):
        return current_config.get(section, option)
    else:
        return default
    
# Access values with default fallback
def get_boolean_config_value(section, option, default=None):
    global current_config
    if current_config == None: read_configuration()
    if current_config.has_option(section, option):
        return current_config.getboolean(section, option)
    else:
        return default

def get_float_config_value(section, option, default=None):
    global current_config
    if current_config == None: read_configuration()
    if current_config.has_option(section, option):
        return current_config.getfloat(section, option)
    else:
        return default
    
def read_configuration():
    global current_config, SKIP_AI, DEBUG
    try:
        # Read the INI file
        logger.info("Reading configuration")
        # here is the list of possible places where config file is expected
        # if multiple files exists, the lastet will override values of the others if
        # they define same settings
        configFileLocations = [
            "app.config",
            "local.config",
            "dev.config"
        ]
        current_config = ConfigParser()
        current_config.read(configFileLocations)
        # check if there is a overwrite from config file
        SKIP_AI = get_boolean_config_value("GenAI","skip", SKIP_AI)
        # keep debug if already set
        DEBUG = DEBUG or get_boolean_config_value("General","debug", DEBUG)
        return current_config
    except Exception as e:
        logger.error("Failed to read configuration: %s", str(e))
        logger.debug("Exception details:", exc_info=True)
        return None

#-----------------------------------------------------------------
# section General
#-----------------------------------------------------------------
def get_app_title():
    """the title of the application"""
    return get_config_value("General","app_title", "Funny Image Converter")

def get_app_disclaimer():
    """if set, it will create a popup when the application starts"""
    return get_config_value("General","app_disclaimer", "")

def get_user_message():
    """a message which is displayed to the user like "limited uptime"""
    return get_config_value("General","user_message", "")

def get_server_port():
    """the port to run the application in or none (random port)"""
    return get_config_value("General","port")

def is_gradio_shared():
    """check if the Gradio application should be available via public link"""
    return get_boolean_config_value("General","is_shared", False)

def is_save_output_enabled():
    """true = output of the generation process should be saved to file"""
    return get_boolean_config_value("General","save_output", False)

def get_output_folder():
    """The folder where the output should be saved if activated"""
    return get_config_value("General","output_folder", "./output/")

def is_input_cache_enabled():
    """true = enables cache for input images"""
    return get_boolean_config_value("General","cache_enabled", False)

def is_analytics_enabled():
    """true = advanced analytics is activated"""
    return get_boolean_config_value("General","analytics_enabled", False)

def get_analytics_db_path():
    """The path and filename of teh analytics database (will be created if not existing)"""
    return get_config_value("General","analytics_db_path", "./analytics.db")

def get_analytics_city_db():
    """The path and filename of the ip 2 city database"""
    return get_config_value("General","analytics_city_db", "./GeoLite2-City.mmdb")

#-----------------------------------------------------------------
# section Feature Token
#-----------------------------------------------------------------
def is_feature_generation_with_token_enabled():
    """true = Generation only possible by token"""
    return get_boolean_config_value("Token","enabled", True)

def get_token_explanation():
    """Explanation for Token in the UI"""
    return get_config_value("Token","explanation", "")

def get_token_for_new_image():
    """amount of token for new images"""
    return int(get_config_value("Token","new_image", 3))

def get_token_time_lock_for_new_image():
    """time after the user gets new token for the same image"""
    return int(get_config_value("Token","image_blocked_in_minutes", 240))

def get_token_bonus_for_face():
    """value which is the bonus for new images with face"""
    return int(get_config_value("Token","bonus_for_face", 2))

def get_token_bonus_for_smile():
    """value which is the bonus for new images with a smile"""
    return int(get_config_value("Token","bonus_for_smile", 1))

def get_token_bonus_for_cuteness():
    """value which is the bonus for new images with cuteness"""
    return int(get_config_value("Token","bonus_for_cuteness", 3))

#-----------------------------------------------------------------
# section UI
#-----------------------------------------------------------------
def UI_show_stength_slider():
    """true = enables the slider in the UI"""
    return get_boolean_config_value("UI","show_strength", False)

def UI_show_steps_slider():
    """true = enables the slider in the UI"""
    return get_boolean_config_value("UI","show_steps", False)

def UI_get_gradio_theme():
    """name of the gradio theme to be used"""
    return get_config_value("UI","theme", "")

#-----------------------------------------------------------------
# section Styles
#-----------------------------------------------------------------
def get_style_count():
    """The numbers of available styles"""
    return int(get_config_value("Styles","style_count", 0))

def get_general_negative_prompt():
    """The prompt for the specified style"""
    return get_config_value("Styles","general_negative_prompt", "")

def get_style_name(style: int):
    """The name for the specified style"""
    return get_config_value("Styles",f"style_{style}_name", f"Style {style}")

def get_style_prompt(style: int):
    """The prompt for the specified style"""
    return get_config_value("Styles",f"style_{style}_prompt", "")

def get_style_negative_prompt(style: int):
    """The negative prompt for the specified style including the general negative prompt"""
    return get_general_negative_prompt() + ","  + get_config_value("Styles",f"style_{style}_negative_prompt", "")

def get_style_strengths(style: int):
    """The prompt for the specified style or the default value"""
    return get_float_config_value("Styles",f"style_{style}_strength", get_default_strength())

#-----------------------------------------------------------------
# section GenAI
#-----------------------------------------------------------------
def get_model():
    """The model to be used to generate images"""
    return get_config_value(f"GenAI","default_model", "./models/toonify.safetensors")

def get_model_folder():
    """The folder where additional models are stored"""
    return get_config_value(f"GenAI","model_folder", "./models/")

def get_model_url():
    """The URL of a safetensor file to be downloaded if 'model' file is not existing"""
    return get_config_value(f"GenAI","safetensor_url", "https://civitai.com/api/download/models/244831?type=Model&format=SafeTensor&size=pruned&fp=fp16")

def GenAI_get_execution_batch_size():
    """amount of parallel renderings (depends on GPU size)"""
    return int(get_config_value(f"GenAI","execution_batch_size", 1))

def get_default_strength():
    """The default strengths if nothing is specified"""
    default = 0.5
    v = get_float_config_value(f"GenAI","default_strength", 0.5)
    if v<=0 or v>=1: v=default
    return v

def get_default_steps():
    """The default steps if nothing is specified"""
    default = 50
    v = int(get_config_value(f"GenAI","default_steps", 50))
    if v<=10 or v>=100: v=default
    return v

def get_max_size():
    """the maximum width or height of the output image"""
    return int(get_config_value(f"GenAI","max_size", 1024))

# if __name__ == "__main__":
#     if read_configuration() is None: print("read configuration failed")
#     print (is_gradio_shared())
#     if is_gradio_shared(): print ("shared")

def get_modelurl_onnx_age_googlenet():
    """The url of the onnx model to determine age"""
    return "https://github.com/onnx/models/raw/refs/heads/main/validated/vision/body_analysis/age_gender/models/age_googlenet.onnx"

def get_modelfile_onnx_age_googlenet():
    """The path and filename of the onnx model to determine age"""
    mf = get_model_folder()
    return os.path.join(mf, 'onnx/age_googlenet.onnx')

def get_modelurl_onnx_gender_googlenet():
    """The url of the onnx model to determine gender"""
    return "https://github.com/onnx/models/raw/refs/heads/main/validated/vision/body_analysis/age_gender/models/gender_googlenet.onnx"

def get_modelfile_onnx_gender_googlenet():
    """The path and filename of the onnx model to determine gender"""
    mf = get_model_folder()
    return os.path.join(mf, 'onnx/gender_googlenet.onnx')
