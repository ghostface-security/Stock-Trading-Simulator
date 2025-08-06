#!/bin/bash

# Define the base directory for the project.
PROJECT_DIR="/home/pi/Stock-Trading-Simulator"

# Navigate to the correct directory
echo "Navigating to the project directory: $PROJECT_DIR"
cd "$PROJECT_DIR" || { echo "Error: Could not find or enter project directory."; exit 1; }

# Check if the virtual environment directory exists. If not, create it.
# This part is kept for robustness, but 'pip install' is removed from runtime.
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

# IMPORTANT: Removed 'pip install -r requirements.txt' from here.
# This command should be run manually once during setup or deployment,
# not every time the service starts, as it can cause delays or issues.

# Start ngrok to forward traffic to port 5000 in the background.
# We start ngrok first so that the 'exec' command for Flask can take over
# as the main process for systemd, while ngrok continues to run.
echo "Starting ngrok to forward traffic..."
"$NGROK_EXEC" http --domain=merry-well-ladybird.ngrok-free.app --host-header=rewrite 5000 > /home/pi/Stock-Trading-Simulator/ngrok_log.txt 2>&1 &

# Store the PID of the ngrok process so we can wait for it if needed,
# though systemd will primarily manage the Flask app.
NGROK_PID=$!

# Start the Python Flask application.
# Using 'exec' ensures that the Python process directly replaces the shell script's process.
# This makes systemd directly supervise the Flask application, which is generally
# a more robust way to manage long-running services.
echo "Starting the Flask application (this will become the main process for systemd)..."
exec "$PYTHON_EXEC" app.py

# Note: Any commands after 'exec' will NOT be executed by this script,
# as 'exec' replaces the current shell process. The ngrok process,
# having been backgrounded, will continue to run independently.
