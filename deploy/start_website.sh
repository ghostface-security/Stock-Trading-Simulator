#!/bin/bash

# Define the base directory for the project.
PROJECT_DIR="/home/pi/deploy"

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
NGROK_EXEC="/usr/local/bin/ngrok"

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || { echo "Error: Could not activate virtual environment. Make sure it exists."; exit 1; }

# Start ngrok to forward traffic to port 5000 in the background.
# We start ngrok first so that the 'exec' command for Flask can take over
# as the main process for systemd, while ngrok continues to run.
echo "Starting ngrok to forward traffic..."
"$NGROK_EXEC" http --domain=your-ngrok-link.ngrok-free.app --host-header=rewrite 5000 > /home/pi/website/ngrok_log.txt 2>&1 &

# Store the PID of the ngrok process so we can wait for it if needed,
# though systemd will primarily manage the Flask app.
NGROK_PID=$!

# Start the Python Flask application.
# Using 'exec' ensures that the Python process directly replaces the shell script's process.
# This makes systemd directly supervise the Flask application, which is generally
# a more robust way to manage long-running services.
echo "Starting the Flask application..."
exec "$PYTHON_EXEC" app.py

# Note: Any commands after 'exec' will NOT be executed by this script,
# as 'exec' replaces the current shell process. The ngrok process,
# having been backgrounded, will continue to run independently.
