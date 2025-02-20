#!/bin/bash

# Check if it's a Git repository
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "Not a Git repository. Auto-update not possible."
else
    # Fetch the latest tags from the remote repository
    git fetch --tags

    # Get the latest version tag (must start with V)
    latest_tag=$(git tag -l "V*" | sort -V | tail -n1)

    if [ -z "$latest_tag" ]; then
        echo "No version tags (starting with V) found on server, could not check for updates."
    else
        # Get tag creation date
        tag_date=$(git log -1 --format=%ai "$latest_tag")
        echo "Latest version: $latest_tag"
        echo "Created on: $tag_date"

        # Ask for confirmation
        read -p "Do you want to proceed with this version? (y/n) " answer
        if [[ $answer == "y" || $answer == "Y" ]]; then
            # Switch to the latest tag
            git checkout "$latest_tag"

            # Optional: Ensure the latest updates from the remote repository
            git pull origin "$latest_tag"

            echo "Updated to version $latest_tag successfully."
        else
            echo "Continuing with current version..."
        fi
    fi
fi

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

# Function to start the main app
start_main_app() {
    echo "Starting App..."
    python main.py
}

# Function to start the analytics dashboard
start_analytics() {
    echo "Starting Analytics Dashboard..."
    python analytics_dashboard.py
}

# Function to start both components
start_both() {
    echo "Starting both AI Anime Maker and Analytics Dashboard..."
    python main.py & 
    python analytics_dashboard.py &
    wait
}

# Show menu and get user choice
echo "Please select what to start:"
echo "1) AI App"
echo "2) Analytics Dashboard"
echo "3) Both"
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        start_main_app
        ;;
    2)
        start_analytics
        ;;
    3)
        start_both
        ;;
    *)
        echo "Invalid choice. Starting AI Anime Maker by default..."
        start_main_app
        ;;
esac

# Deactivate the virtual environment when done
