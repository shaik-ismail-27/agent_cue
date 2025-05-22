#!/bin/bash
# This script is used to start Rasa with proper CORS settings in a Codespace environment

echo "Setting up Rasa environment..."

# Check if Rasa is installed
if ! command -v rasa &> /dev/null; then
  echo "Rasa not found. Installing Rasa Pro..."
  pip install 'uv[pyproject]'
  uv pip install rasa-pro --system
fi

# Train the model if it doesn't exist
if [ ! -d "./models" ] || [ -z "$(ls -A ./models)" ]; then
  echo "No models found. Training a new model..."
  rasa train
fi

# Start Rasa Inspect
echo "Starting Rasa Inspect..."
rasa inspect --cors "*" --debug 