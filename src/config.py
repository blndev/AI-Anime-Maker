from configparser import ConfigParser
import os
import logging
from src.logging_config import setup_logging

# property used from other areas like AI Module
# can finally be configured in setting GenAI/skip (read while loading function)
# it's implemented as property, so that it can be changed on runtime
# helps to reduce wasting storage for torch etc on build systems
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
    """Get a string value from the configuration with fallback to default"""
    global current_config
    if current_config == None: read_configuration()
    if current_config.has_option(section, option):
        return current_config.get(section, option)
    else:
        return default
    
def get_boolean_config_value(section, option, default=None):
    """Get a boolean value from the configuration with fallback to default"""
    global current_config
    if current_config == None: read_configuration()
    if current_config.has_option(section, option):
        return current_config.getboolean(section, option)
    else:
        return default

def get_float_config_value(section, option, default=None):
    """Get a float value from the configuration with fallback to default"""
    global current_config
    if current_config == None: read_configuration()
    if current_config.has_option(section, option):
        return current_config.getfloat(section, option)
    else:
        return default
    
def read_configuration():
    """Read configuration from app.config, local.config, or dev.config files"""
    global current_config, SKIP_AI, DEBUG
    try:
        # Read the INI file
        logger.info("Reading configuration")
        # here is the list of possible places where config file is expected
        # if multiple files exist, the latest will override values of the others if
        # they define same settings
        configFileLocations = [
            "app.config",
            "local.config",
            "dev.config"
        ]
        current_config = ConfigParser()
        current_config.read(configFileLocations)
        # check if there is an override from config file
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
    """Get the title displayed in the application window and browser tab"""
    return get_config_value("General","app_title", "Funny Image Generator")

def get_app_disclaimer():
    """Get the disclaimer message shown in a popup when the application starts"""
    return get_config_value("General","app_disclaimer", "")

def get_user_message():
    """Get the message displayed below the application title (e.g., maintenance notices)"""
    return get_config_value("General","user_message", "")

def get_server_port():
    """Get the server port number, or None for random port assignment"""
    return get_config_value("General","port")

def is_gradio_shared():
    """Check if the application should be accessible via a public Gradio link"""
    return get_boolean_config_value("General","is_shared", False)

def is_save_output_enabled():
    """Check if generated images should be saved to the output folder"""
    return get_boolean_config_value("General","save_output", False)

def get_output_folder():
    """Get the directory path where generated images are saved"""
    return get_config_value("General","output_folder", "./output/")

def is_input_cache_enabled():
    """Check if caching is enabled for input images to improve performance"""
    return get_boolean_config_value("General","cache_enabled", False)

def is_analytics_enabled():
    """Check if usage analytics and tracking features are enabled"""
    return get_boolean_config_value("General","analytics_enabled", False)

def get_analytics_db_path():
    """Get the path to the SQLite database used for analytics data"""
    return get_config_value("General","analytics_db_path", "./analytics/analytics.db")

def get_analytics_city_db():
    """Get the path to the GeoLite2 City database for IP geolocation"""
    return get_config_value("General","analytics_city_db", "./analytics/GeoLite2-City.mmdb")

#-----------------------------------------------------------------
# section Feature Token
#-----------------------------------------------------------------
def is_feature_generation_with_token_enabled():
    """Check if the token-based generation system is enabled"""
    return get_boolean_config_value("Token","enabled", False)

def get_token_explanation():
    """Get the explanation text shown to users about the token system"""
    return get_config_value("Token","explanation", "")

def get_token_for_new_image():
    """Get the number of tokens awarded for uploading a new image"""
    return int(get_config_value("Token","new_image", 3))

def get_token_time_lock_for_new_image():
    """Get the cooldown period (in minutes) before an image can earn tokens again"""
    return int(get_config_value("Token","image_blocked_in_minutes", 240))

def get_token_bonus_for_face():
    """Get the bonus token amount awarded for images containing faces"""
    return int(get_config_value("Token","bonus_for_face", 2))

def get_token_bonus_for_smile():
    """Get the bonus token amount awarded for images with smiling faces"""
    return int(get_config_value("Token","bonus_for_smile", 1))

def get_token_bonus_for_cuteness():
    """Get the bonus token amount awarded for images detected as cute"""
    return int(get_config_value("Token","bonus_for_cuteness", 3))

#-----------------------------------------------------------------
# section UI
#-----------------------------------------------------------------
def UI_show_strength_slider():
    """Check if the strength adjustment slider should be shown in the UI"""
    return get_boolean_config_value("UI","show_strength", False)

def UI_show_steps_slider():
    """Check if the steps adjustment slider should be shown in the UI"""
    return get_boolean_config_value("UI","show_steps", False)

def UI_get_gradio_theme():
    """Get the name of the Gradio theme to use for the UI"""
    return get_config_value("UI","theme", "")

#-----------------------------------------------------------------
# section Styles
#-----------------------------------------------------------------
def get_style_count():
    """Get the total number of defined image generation styles"""
    return int(get_config_value("Styles","style_count", 0))

def get_general_negative_prompt():
    """Get the negative prompt that is applied to all styles"""
    return get_config_value("Styles","general_negative_prompt", "")

def get_style_name(style: int):
    """Get the display name for the specified style number"""
    return get_config_value("Styles",f"style_{style}_name", f"Style {style}")

def get_style_prompt(style: int):
    """Get the positive prompt for the specified style number"""
    return get_config_value("Styles",f"style_{style}_prompt", "")

def get_style_negative_prompt(style: int):
    """Get the combined negative prompt (general + style-specific) for the specified style"""
    return get_general_negative_prompt() + ","  + get_config_value("Styles",f"style_{style}_negative_prompt", "")

def get_style_strengths(style: int):
    """Get the strength value for the specified style, or the default strength if not defined"""
    return get_float_config_value("Styles",f"style_{style}_strength", get_default_strength())

#-----------------------------------------------------------------
# section GenAI
#-----------------------------------------------------------------
def get_model():
    """Get the path to the AI model file used for image generation"""
    return get_config_value(f"GenAI","default_model", "./models/toonify.safetensors")

def get_model_folder():
    """Get the directory containing AI model files"""
    return get_config_value(f"GenAI","model_folder", "./models/")

def get_model_url():
    """Get the download URL for the default model if not found locally"""
    return get_config_value(f"GenAI","safetensor_url", "https://civitai.com/api/download/models/244831?type=Model&format=SafeTensor&size=pruned&fp=fp16")

def GenAI_get_execution_batch_size():
    """Get the number of parallel image generation processes to run"""
    return int(get_config_value(f"GenAI","execution_batch_size", 1))

def get_default_strength():
    """Get the default strength value (0-1) for image transformation"""
    default = 0.5
    v = get_float_config_value(f"GenAI","default_strength", 0.5)
    if v<=0 or v>=1: v=default
    return v

def get_default_steps():
    """Get the default number of steps for image generation (10-100)"""
    default = 50
    v = int(get_config_value(f"GenAI","default_steps", 50))
    if v<=10 or v>=100: v=default
    return v

def get_max_size():
    """Get the maximum allowed dimension for input/output images"""
    return int(get_config_value(f"GenAI","max_size", 1024))

def get_modelurl_onnx_age_googlenet():
    """Get the download URL for the age detection model"""
    return "https://github.com/onnx/models/raw/refs/heads/main/validated/vision/body_analysis/age_gender/models/age_googlenet.onnx"

def get_modelfile_onnx_age_googlenet():
    """Get the local path where the age detection model should be stored"""
    mf = get_model_folder()
    return os.path.join(mf, 'onnx/age_googlenet.onnx')

def get_modelurl_onnx_gender_googlenet():
    """Get the download URL for the gender detection model"""
    return "https://github.com/onnx/models/raw/refs/heads/main/validated/vision/body_analysis/age_gender/models/gender_googlenet.onnx"

def get_modelfile_onnx_gender_googlenet():
    """Get the local path where the gender detection model should be stored"""
    mf = get_model_folder()
    return os.path.join(mf, 'onnx/gender_googlenet.onnx')
