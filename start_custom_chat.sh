#!/bin/bash

# Script to start Cue with custom web chat interface

echo "🏥 Starting Cue Clinic Booking System with Custom Web Chat..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create it with your API keys."
    echo "📝 Copy .env.example to .env and add your keys:"
    echo "   RASA_PRO_LICENSE=your_rasa_pro_license_key"
    echo "   OPENAI_API_KEY=your_openai_api_key"
    exit 1
fi

# Source environment variables
source .env

# Check if model exists, train if not
if [ ! -d "models" ] || [ -z "$(ls -A models)" ]; then
    echo "🤖 No model found. Training new model..."
    rasa train
fi

# Start backend server in background
echo "🔧 Starting backend server..."
cd backend
python server.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start Rasa server with REST API
echo "🚀 Starting Rasa server with REST API..."
rasa run --enable-api --cors "*" --port 5005 &
RASA_PID=$!

# Wait for Rasa to start
sleep 5

# Open the chat interface
echo "Opening professional chat interface..."
if command -v open > /dev/null; then
    # macOS
    open frontend/pro_chat_fixed.html
elif command -v xdg-open > /dev/null; then
    # Linux
    xdg-open frontend/pro_chat_fixed.html
elif command -v start > /dev/null; then
    # Windows
    start frontend/pro_chat_fixed.html
else
    echo "Please open frontend/pro_chat_fixed.html in your browser manually"
fi

echo "System started successfully!"
echo "Chat interface: frontend/pro_chat_fixed.html"
echo "🤖 Rasa API: http://localhost:5005"
echo "🔧 Backend API: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping services..."
    kill $RASA_PID 2>/dev/null
    kill $BACKEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set up trap to cleanup on Ctrl+C
trap cleanup INT

# Wait for user to stop
wait
