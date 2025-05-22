#!/bin/bash
# This script is used to start Rasa with proper CORS settings in a Codespace environment

echo "Setting up Rasa environment..."

# Get the current directory name
CURRENT_DIR=$(basename "$PWD")

# Check if we're in the correct directory for Rasa commands
if [ "$CURRENT_DIR" != "agent_cue" ]; then
  if [ -d "../agent_cue" ]; then
    echo "Changing to agent_cue directory..."
    cd ../agent_cue
  elif [ -d "./agent_cue" ]; then
    echo "Changing to agent_cue directory..."
    cd ./agent_cue
  else
    echo "Error: Not in agent_cue directory and couldn't find it. Rasa commands require being in the agent_cue directory."
    exit 1
  fi
fi

# Check if Rasa is installed
if ! command -v rasa &> /dev/null; then
  echo "Rasa not found. Installing Rasa Pro..."
  pip install 'uv[pyproject]'
  uv pip install pydantic>=2.0.0 --system
  uv pip install rasa-pro --system
fi

# Train the model if it doesn't exist
if [ ! -d "./models" ] || [ -z "$(ls -A ./models)" ]; then
  echo "No models found. Training a new model..."
  rasa train
fi

# Start the backend server in a separate terminal
if [ -d "./backend" ]; then
  echo "Starting backend server in a new terminal..."
  # Save the current directory
  MAIN_DIR="$PWD"
  # Start backend server in background
  cd backend && python server.py &
  BACKEND_PID=$!
  # Return to the main directory
  cd "$MAIN_DIR"
  echo "Backend server started with PID: $BACKEND_PID"
else
  echo "Warning: Backend directory not found. Skipping backend server startup."
fi

# Start Rasa Inspect
echo "Starting Rasa Inspect..."
rasa inspect --cors "*" --debug

# If we get here, Rasa has been stopped, so kill the backend server
if [ -n "$BACKEND_PID" ]; then
  echo "Stopping backend server..."
  kill $BACKEND_PID
fi 