#!/bin/bash

# Define the base directory for the project.
PROJECT_DIR="/"

# Navigate to the correct directory
echo "Navigating to the project directory: $PROJECT_DIR"
cd "$PROJECT_DIR" || { echo "Error: Could not find or enter project directory."; exit 1; }

# Check if the virtual environment directory exists.
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating a new one..."
    python3 -m venv venv || { echo "Error: Failed to create virtual environment."; exit 1; }
fi

# Define the full paths to the executables within the virtual environment.
PYTHON_EXEC="$PROJECT_DIR/venv/bin/python3"

# Start the Python Flask application and ngrok tunnel in the background.
# We will not use 'exec' so that the script can handle any pre-flight checks.
/snap/bin/ngrok http --domain=https://<random_string>.ngrok-free.app 5000 &
echo "Starting the Flask application..."
"$PYTHON_EXEC" app.py
