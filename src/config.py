
from configparser import ConfigParser

# used from other areas like AI Module and is set by main module
# helps to reduce easting storage for torch etc on build systems
SKIP_AI = True
DEBUG = False

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
    global current_config
    try:
        # Read the INI file
        print ("read configuration")
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
        return current_config
    except Exception as e:
        print (e)
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

def is_cache_enabled():
    """true = enables cache for input images"""
    return get_boolean_config_value("General","cache_enabled", False)

def get_cache_folder():
    """The folder where the cached files should be stored"""
    return get_config_value("General","cache_folder", "./cache/")

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
# section UI
#-----------------------------------------------------------------
def UI_show_stength_slider():
    """true = enables the slider in the UI"""
    return get_boolean_config_value("UI","show_strength", False)

def UI_show_steps_slider():
    """true = enables the slider in the UI"""
    return get_boolean_config_value("UI","show_steps", False)

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
