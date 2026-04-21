# Custom Web Chat Interface for Cue

This directory contains custom web-based chat interfaces for the Cue clinic booking agent.

## Option 1: Simple HTML/JS Chat Interface

### Setup Instructions

1. **Start Rasa Server**
   ```bash
   # In the agent_cue directory
   rasa run --enable-api --cors "*"
   ```

2. **Start Backend Server**
   ```bash
   # In a new terminal
   cd backend
   python server.py
   ```

3. **Open the Chat Interface**
   - Open `simple_chat.html` in your browser
   - Or serve it with a simple HTTP server:
   ```bash
   cd frontend
   python -m http.server 8000
   # Then visit http://localhost:8000/simple_chat.html
   ```

### Features
- Clean, responsive design
- Real-time messaging
- Typing indicators
- Error handling
- CORS support for local development

## Option 2: React Chat Interface (Advanced)

For a more sophisticated interface, you can create a React app:

```bash
npx create-react-app cue-chat-frontend
cd cue-chat-frontend
npm install axios socket.io-client
```

### Key Components
- `ChatContainer.js` - Main chat component
- `MessageList.js` - Message display
- `MessageInput.js` - Input handling
- `useRasa.js` - Custom hook for Rasa API

## Option 3: Socket.IO Integration

For real-time bidirectional communication:

1. Update `credentials.yml` to enable Socket.IO (already configured)
2. Start Rasa with Socket.IO:
   ```bash
   rasa run --enable-api --socketio --cors "*"
   ```
3. Use Socket.IO client in frontend for real-time updates

## API Endpoints

### REST API
- **POST** `/webhooks/rest/webhook` - Send messages
- **GET** `/conversations/{sender_id}/tracker` - Get conversation state
- **POST** `/conversations/{sender_id}/execute` - Trigger actions

### Socket.IO Events
- `user_uttered` - Send user message
- `bot_uttered` - Receive bot response
- `session_confirmed` - Session management

## Environment Variables

Make sure your `.env` file includes:
```bash
RASA_PRO_LICENSE=your_rasa_pro_license_key
OPENAI_API_KEY=your_openai_api_key
```

## Deployment Considerations

### For Production:
1. Use HTTPS for all communications
2. Implement proper authentication
3. Add rate limiting
4. Set up proper CORS policies
5. Use environment-specific configurations
6. Add logging and monitoring

### Security Notes:
- Never expose API keys in frontend code
- Validate all user inputs
- Implement proper session management
- Use secure WebSocket connections (WSS) in production
