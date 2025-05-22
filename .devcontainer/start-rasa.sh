#!/bin/bash
# This script is used to start Rasa with proper CORS settings in a Codespace environment

echo "Setting up Rasa environment..."

# Train the model if it doesn't exist
if [ ! -d "./models" ] || [ -z "$(ls -A ./models)" ]; then
  echo "No models found. Training a new model..."
  rasa train
fi

# Start Rasa Inspect
echo "Starting Rasa Inspect..."
rasa inspect --cors "*" --debug 