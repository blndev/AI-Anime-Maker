#!/bin/bash

# Ensure the directory is a Git repository
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "Not a Git repository!"
    exit 1
fi

# Fetch the latest tags from the remote repository
git fetch --tags

# Get the latest version (latest tag)
latest_tag=$(git describe --tags `git rev-list --tags --max-count=1`)

if [ -z "$latest_tag" ]; then
    echo "No tags found!"
    exit 1
fi

echo "Latest version: $latest_tag"

# Switch to the latest tag
git checkout "$latest_tag"

# Optional: Ensure the latest updates from the remote repository
git pull origin "$latest_tag"

echo "Updated to version $latest_tag successfully."

# Check if ".venv" folder exists, if not create a virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Activate the virtual environment
source .venv/bin/activate

# # Check if "models/toony.safetensors" exists, if not download it
# if [ ! -f "models/toonify.safetensors ]; then
#     echo "Downloading toony.safetensors..."
#     mkdir -p models
#     wget -O models/toonify.safetensors "https://civitai.com/api/download/models/244831?type=Model&format=SafeTensor&size=pruned&fp=fp16"
# else
#     echo "Model file already exists."
# fi

# Upgrade Python requirements
echo "Upgrading Python requirements..."
pip install --quiet --upgrade pip
pip install --quiet --require-virtualenv --requirement requirements.txt

# Execute "photo-to-drawing.py" in the virtual environment
echo "Starting app..."
python photo-to-drawing.py

# Deactivate the virtual environment
deactivate