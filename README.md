# 🎨 AI-Anime-Maker - Turn Your Photos into Anime with a Dash of AI Magic! 🌟
Transform your photos into stunning anime art using the power of Stable Diffusion. Welcome to AI-Anime-Maker - where every picture gets a whimsical anime makeover!

Status: V1 - Stable and rocking! 🎉

1. [Goal](#goal)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Model Support](#model-support)
5. [Expanding Your Artistic Horizons](#expanding-your-artistic-horizons)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)
8. [Development](#development)
9. [License](#license)
10. [Contributing](#contributing)

## 🎯 Goal
Our mission (and the mission of our future tools) is to provide simple, dedicated solutions for specific purposes. Unlike the complex and convoluted atomic0000, our tools are designed to be user-friendly for everyone, not just tech wizards!

![Example Image](example.jpg)

Just imagine! A world where converting photos to anime is as easy as pie. 🥧

To make the generation results even better, we implemented a local image-to-text conversion, which describes the input of your source image automaticaly. 

## 🎨 Model Support
AI-Anime-Maker supports a variety of models, from Hugging Face models to safetensor files. You can download these models from multiple websites like https://civit.ai for free. This flexibility allows you to experiment with different models to find the perfect one for your needs.

## 🖌️ Expanding Your Artistic Horizons
If you want to modify pictures to create different styles of paintings from artists like Picasso or others, you can easily do so by adapting the "Style" section in the configuration file. The sky's the limit! 🌌

## 🛠️ Installation
Tested on Linux, but it should work like a charm on Windows and Mac too (fingers crossed! 🤞). If you encounter any hiccups on Windows or Mac, please let me know, or better yet, create a pull request with the fix. You're awesome! 🚀

### Prerequisites
* Python 3.12 (tested with it)
* Python venv module (should be there with python)
* Python pip (should be tehre as well)
* a GPU with 4-8GB VRAM depending on Model and Image Size
(CPU works also but is very slow)


### Now
1. Download the repository.

```sh
git clone https://github.com/yourusername/ai-anime-maker.git
cd ai-anime-maker
```

2. Run the magical command: 
```sh 
./run.sh
```
3. Have fun

Note: The first run might take a while as it downloads multiple gigabytes of AI models and required libraries. Patience, young grasshopper! 🐢

## ⚙️ Configuration
Customize your anime-creating experience using the app.config file. Here's a sneak peek at the basic structure:

```ini
[General]
app_title=Funny Image-converter
user_message=Attention: Limited Render Resources. App might be slow!

# Defines the port where the app starts. If not defined, a random port will be chosen.
#port=7860

# Define if the application should create an internet-reachable link via Gradio shared tunnel function.
is_shared=false

# true = Output of the generation process should be saved to a file.
save_output=true

# The folder where the output should be saved if activated.
output_folder=./output/

# true = Enables cache for input images (not implemented so far).
#cache_enabled=false
# The folder where the cached files should be saved if cache is activated.
#cache_folder=./cache/

[GenAI]
# A local savetensors file or a Huggingface Model (will be downloaded).
default_model=./models/toonify.safetensors

# The URL to download the model if the file specified in "model" does not exist.
#safetensor_url=https://civit.ai/...

# The number of steps used to generate the image. Lower values for systems without GPU.
default_steps=60

# Value between 0 and 1. 0 = no changes to the input image, 1 = maximum changes.
# Good values are 0.4 to 0.6.
default_strength=0.4

# The maximum width or height of the output image. Adjust based on model and available GPU RAM.
max_size=1024

[UI]
# true = Enables the slider to modify strengths in the UI.
show_strengths=false

# true = Enables the slider to modify steps in the UI.
show_steps=false

[Styles]
# The number of styles listed below.
style_count=2

# The negative prompt applied to all styles.
general_negative_prompt=realistic photo, wrong fingers, ugly, sad

style_1_name=Test 1
style_1_prompt=disney-style painting
style_1_strength=0.6
style_1_negative_prompt=anime

style_2_name=Test 2
style_2_prompt=a anime style painting
# Optional settings.
#style_2_strength=0.3
#style_2_negative_prompt=oil painting
```

## 🛠️ Development
For development purposes, you can create a dev.config (copy of app.config) which allows you to use local folders without affecting the release/standard configuration. Happy coding! 💻

---
Get ready to unleash your inner artist and turn your photos into anime masterpieces! 🌈✨


## 📜 License
This project is licensed under the GPL3 License - see the [LICENSE.md] file for details.

## 🤝 Contributing
We welcome contributions! Please read our Contributing Guidelines for details on the process for submitting pull requests.

## 🌟 Outlook (Planned Features)
* Preview on generation Process
* Better Image description generation
* Better Memory Handling for higher resolutions
* SDXL and FLUX Support
* More Styles or Groups of Styles

### More Ideas
* Gif/Video output