# AI-Anime-Maker
Creates a Anime out of a Photo by using Stable Diffusion


# Installation
The app ist tested on Linux, but should run also on windows or mac as it uses standard components. 
If there are any issues on Windows or Mac please let me know or better create a pull request wit the fix.

1. download the repository
2. execute "run.sh"

Note: on the first run the app needs a while because it will download multiple gigabytes of Ai Models and required libraries!

## Configuration

You can configure the application by using teh app.config - file-

Basic structure:
```ini
[General]
app_title=Funny Image-converter
user_message = Attention: Limited Render ressources. App might be slow!

# defines the port where the app is starting, if not defined, a random port will be choosen
#port = 7860

#define if the application should create a internet reachable link via gradio shared tunnel function
is_shared = false

# true = output of the generation process should be saved to file"
save_output=True

# The folder where the output should be saved if activated
output_folder=./output/

# true = enables cache for input images (not implemented so far)
#cache_enabled=false
# The folder where the cached files should be saved if cache is activated
#cache_folder="./cache/"

[GenAI]
# a local savetensors file or a Huggingface Model (will be downloaded)
default_model = ./models/toonify.safetensors

# the url to download the model if the file specified in "model" is not existing
#safetensor_url = "https://civit.ai/..."

# the amount of steps used to generate the image
# the value should be lower for systems without GPU
default_steps = 60

# value between 0 and 1
# 0 = no changes to the input image
# 1 = maximum changes (like no input file)
# good values are 0.4 to 0.6
default_strength = 0.4

# the maximum width or height of the output image
# change the value depending on teh model and available RAM on the GPU
max_size = 1024

[UI]
# true = enables the slider to modify strengths in the UI
show_strengths = false

# true = enables the slider to modify steps in the UI
show_steps = false

[Styles]
# the amout of styles listed below
style_count = 2

# the negative prompt which should be applied to all styles
general_negative_prompt = realistic photo, wrong fingers, ugly, sad

style_1_name = Test 1
style_1_prompt = disney-style painting
style_1_strength = 0.6
style_1_negative_prompt = "anime"

style_2_name = Test 2
style_2_prompt = a anime style painting
# optional settings
#style_2_strength = 0.3
#style_2_negative_prompt = "oil painting
```
# Development
for development purposes you can create a dev.config (copy of app.config) which allows you to use local folders without affecting release/standard configuration