# 🎨 AI-Anime-Maker - Turn Your Photos into Anime with a Dash of AI Magic! 🌟
Transform your photos into stunning anime art using the power of Stable Diffusion. Welcome to AI-Anime-Maker - where every picture gets a whimsical anime makeover!

Status: V1 - Stable and rocking! 🎉

- [🎨 AI-Anime-Maker - Turn Your Photos into Anime with a Dash of AI Magic! 🌟](#-ai-anime-maker---turn-your-photos-into-anime-with-a-dash-of-ai-magic-)
  - [🎯 Goal](#-goal)
  - [🎨 Model Support](#-model-support)
  - [🖌️ Expanding Your Artistic Horizons](#️-expanding-your-artistic-horizons)
  - [🛠️ Installation](#️-installation)
    - [Prerequisites](#prerequisites)
    - [Now](#now)
  - [⚙️ Configuration](#️-configuration)
  - [🌟 Feature: Analytics](#-feature-analytics)
  - [🌟 Feature: Token based generation](#-feature-token-based-generation)
  - [🛠️ Development and Deployment](#️-development-and-deployment)
  - [📜 License](#-license)
  - [🤝 Contributing](#-contributing)
  - [🌟 Outlook (Features which could be useful)](#-outlook-features-which-could-be-useful)

## 🎯 Goal
Our mission (and the mission of our future tools) is to provide simple, dedicated solutions for specific purposes. Unlike the complex and convoluted atomic0000, our tools are designed to be user-friendly for everyone, not just tech wizards!

![Example Image](examples/restaurant_anime.png)

Just imagine! A world where converting photos to anime is as easy as pie. 🥧

To make the generation results even better, we implemented a local image-to-text conversion, which describes the input of your source image automatically. 

## 🎨 Model Support
AI-Anime-Maker supports a variety of models, from Hugging Face models to safetensor files. You can download these models from multiple websites like https://civit.ai for free. This flexibility allows you to experiment with different models to find the perfect one for your needs.

## 🖌️ Expanding Your Artistic Horizons
If you want to modify pictures to create different styles of paintings from artists like Picasso or others, you can easily do so by adapting the "Style" section in the configuration file. The sky's the limit! 🌌

## 🛠️ Installation
Tested on Linux, but it should work like a charm on Windows and Mac too (fingers crossed! 🤞). If you encounter any hiccups on Windows or Mac, please let me know, or better yet, create a pull request with the fix. You're awesome! 🚀

### Prerequisites
* Python 3.12 (tested with it)
* Python venv module (should be there with python)
* Python pip (should be there as well)
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

The script will:
- Check for available version updates (tags starting with 'V', e.g., V1.0)
- Show the latest version and its creation date if available
- Ask if you want to update to the latest version
- Continue with your chosen version (latest or current)
- Present a menu to choose what to start:
  1. AI Anime Maker (the main application)
  2. Analytics Dashboard (if analytics is enabled)
  3. Both components simultaneously

Note: The first run might take a while as it downloads multiple gigabytes of AI models and required libraries. Patience, young grasshopper! 🐢

## ⚙️ Configuration
Customize your anime-creating experience using the app.config file. Here's a sneak peek at the basic structure:

```ini
[General]
# Name of the App and Browser Tab (Default: "Funny Image Creator")
app_title=AI Anime Maker

# If set, creates a popup message when the application starts. Supports HTML formatting.
# Leave empty for no disclaimer. (Default: empty)
#app_disclaimer=<h2>Important Information</h2>

# Message displayed below the app title (Default: empty)
user_message=Have fun creating funny pictures out of your photos!

# Port number for the application server. If not defined, a random port will be chosen.
# (Default: random)
#port=7860

# Enable to create an internet-accessible link via Gradio's shared tunnel function.
# Warning: This makes your instance publicly accessible. (Default: false)
is_shared=false

# Enable analytics to track style usage, user patterns, and system performance.
# Please be aware of data privacy regulations in your region. (Default: false)
analytics_enabled=false

# Path to the SQLite database for analytics. Created automatically if it doesn't exist.
# (Default: "./analytics.db")
analytics_db_path=./analytics/analytics.db

# Path to the GeoLite2 City database for geographic analytics features.
# Download from: https://dev.maxmind.com/geoip/geoip2/geolite2/
# (Default: "./GeoLite2-City.mmdb")
analytics_city_db=./analytics/GeoLite2-City.mmdb


[Token]
# Token-based generation system to prevent misuse and manage system resources

# Enable token requirement for image generation. Users need tokens to generate images,
# which they can earn by uploading new images. (Default: true)
enabled=false

# Explanation shown to users about the token system. (Default: empty)
explanation=You will receive Token by using new images. Each generation will cost you 1 Token. We implemented this to avoid misuse.

# Number of tokens awarded for uploading a new image (Default: 3)
new_image=3

# Time in minutes before the same image can earn tokens again in the same session
# (Default: 240 minutes / 4 hours)
image_blocked_in_minutes=240

# Bonus tokens for special image characteristics:
# For images containing at least one face (Default: 2)
bonus_for_face=3
# For images with smiling faces - Feature coming soon (Default: 1)
bonus_for_smile=1
# For images recognized as "cute" (Default: 3)
bonus_for_cuteness=3

[GenAI]
# AI Model Configuration

# Path to the model file - can be local safetensors file or Hugging Face model
# (Default: "./models/toonify.safetensors")
default_model=./models/toonify.safetensors

# Directory containing additional model files (Default: "./models/")
#model_folder=./models/

# URL to download the model if the specified model file doesn't exist
# (Default: CivitAI toonify model)
#safetensor_url=https://civit.ai/...

# Number of parallel rendering processes. Increase based on available GPU memory.
# (Default: 1)
execution_batch_size=1

# Number of steps for image generation. Lower values recommended for CPU-only systems.
# Valid range: 10-100 (Default: 50)
default_steps=60

# Generation strength controls how much the AI modifies the input image
# 0.0 = no changes, 1.0 = complete transformation
# Recommended range: 0.4-0.6 (Default: 0.5)
default_strength=0.5

# Maximum dimension (width or height) for output images
# Adjust based on available GPU memory (Default: 1024)
max_size=1024

[UI]
# User Interface Configuration

# Visual theme for the application
# Browse themes: https://huggingface.co/spaces/gradio/theme-gallery
# (Default: empty - uses Gradio default theme)
theme=allenai/gradio-theme

# Enable strength adjustment slider in UI (Default: false)
show_strength=false

# Enable steps adjustment slider in UI (Default: false)
show_steps=false

[Styles]
# Style Configuration

# Number of styles defined below (Default: 0)
style_count=2

# Negative prompts applied to all styles for safety and quality
# (Default: empty)
general_negative_prompt=realistic photo, wrong fingers, ugly, sad, brutal, violence

# Style definitions
# Each style can have:
# - name: Display name
# - prompt: The positive prompt for generation
# - strength: Optional override for default_strength
# - negative_prompt: Additional style-specific negative prompts

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
## 🌟 Feature: Analytics Dashboard
AI-Anime-Maker includes a powerful analytics dashboard that provides real-time insights into system usage and user behavior. When analytics is enabled, you can access the dashboard by running:

```sh
python analytics_dashboard.py
```

### Dashboard Features:

#### 📊 Usage Statistics
All statistics are based on the user-agent 
- Session timeline showing daily and hourly activity patterns
- Platform statistics (operating systems, browsers)
- Mobile vs desktop usage distribution
- Generation success rate analysis

#### 🌍 Geographic Distribution
- Interactive world map showing user locations based on their language settings
- Language distribution analysis

#### 📸 Image Upload Analysis
- Timeline of image uploads and generations
- Generation patterns and style preferences


#### 🎨 Generation Details
- Style usage distribution with percentages

### Data Privacy
- No personal identification information is stored
- Geographic data requires GeoLite2 DB (not included)
- Limited data collection when using shared mode
- For GeoLite2 DB setup, visit: https://dev.maxmind.com/geoip/geoip2/geolite2/

### Advanced Analysis
For deeper data analysis, you can use the Jupyter notebook:
```sh
jupyter lab analytics/Analyze_Usage.ipynb
```

The dashboard provides valuable insights to:
- Optimize system configuration
- Identify popular styles and features
- Track usage patterns

## 🌟 Feature: Token based generation
If you have activated token based generation, then the users can't build unlimited amount of images based on one source file. For generation they need token (one for each) and such token will be received for uploaded images.
That prevents the system for misuse. In our public beta we have seen that users try to generate inappropriate content by tweaking the prompt. It wasn't successful as our used model doesn't support that and the style description and negative prompt prevent it in addition. But finally users wasted computing times and with that slowed down the system for others. That was the main reason why we implemented token. It's turned off by default, but feel free to switch it on.

## 🛠️ Development and Deployment
For development and deployment purposes, you can create a "local.config" file (copy of app.config) which allows you to use dedicated configuration, e.g. local model folder without affecting the release/standard configuration. 
This is useful for updating the app including app.config without affecting your local settings.

To make VSCode aware of the packages and path, you need to execute the following line within your python environment

```bash
pip install -e .
```

Interesting settings for dev environments are:
* [General][debug] (true/false) - enable model selection and more output
* [GenAI][skip] (true/false) - skip the GenAI part (used for UI Development)

Command line options:
* `--debug` - Enable debug mode for detailed logging output (alternative to setting debug=true in config)
  
Happy coding! 💻

---
Get ready to unleash your inner artist and turn your photos into anime masterpieces! 🌈✨


## 📜 License
This project is licensed under the GPL3 License - see the [LICENSE.md] file for details.

## 🤝 Contributing
We welcome contributions! Please read our Contributing Guidelines for details on the process for submitting pull requests.

## 🌟 Outlook (Features which could be useful)
* Better Memory Handling for higher resolutions
* SDXL and FLUX Support