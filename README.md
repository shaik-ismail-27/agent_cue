# Rasa Agent Project

This repository contains a Rasa conversational AI agent.

## Disclamer

Please remember that this is a demonstration no actual clinics are involved and no bookings are placed, its backend server is mocking the responce.

## Cue Agent Description

Cue is an AI agent built on Rasa architecture designed for booking appointments at clinics within its network. Cue suggests clinics based on the user's chosen service type and preferred location, and allows users to select appointment dates and times. It handles various scenarios, including new and existing users, account creation, authentication, and payment processing. Cue can also manage situations like initial unavailable appointment slots, failed payments, various failed otps and users not found during authentication. Additionally, it validates clinic selections, collects patient information, and provides payment and booking invoices in message.

## Important consideration

For Cue's limitations explore code and functionality in the repository.

## Required API Keys

Before running the agent, you need to set up the following API keys:

1. **Rasa Pro License Key**
   - Get a free developer license from [Rasa Pro Developer Edition](https://rasa.com/rasa-pro-developer-edition-license-key-request/)
   - This license allows up to 1000 conversations per month

2. **OpenAI API Key**
   - Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys) with credits.

### Environment Setup

Create a `.env` file in the root directory with the following content:

```bash
RASA_PRO_LICENSE=your_rasa_pro_license_key
OPENAI_API_KEY=your_openai_api_key
```

Then source the environment variables:

```bash
source .env
```

## Running with GitHub Codespaces

This project is configured to work with GitHub Codespaces, providing a fully configured development environment in the cloud.

### Using Codespaces

1. Click the "Code" button on the repository page
2. Select the "Codespaces" tab
3. Click "Create codespace on main"
4. Wait for the environment to build (this may take a few minutes)
5. Once loaded, you can:
   - Train the model: `rasa train`
   - Set up backend server:
     ```bash
     # Install Flask and CORS
     pip install flask flask-cors
     
     # Navigate to backend directory
     cd backend
     
     # Start the backend server
     python server.py
     ```
   - Run Rasa Inspect: `rasa inspect`
   
   This will automatically start both the Rasa server and the actions server, and open the UI in your browser.

### Important Notes

1. The models directory is not included in this repository. You will need to train your own model using `rasa train` before running the agent.

2. The startup script and Rasa commands must be run from the `agent_cue` directory. The script will automatically try to navigate to the correct directory if needed.

### Installation Note

This project uses `uv` for package installation due to its improved performance. If you need to manually install packages:

```bash
# Install uv if not already installed
pip install 'uv[pyproject]'

# Install Rasa Pro with uv
uv pip install rasa-pro --system
```

### Startup Script

For convenience, a startup script is included that will automatically train a model if needed and start Rasa Inspect with proper CORS settings:

```bash
.devcontainer/start-rasa.sh
```

The script will:
- Check and navigate to the correct directory if needed
- Install Rasa Pro if not already installed
- Train a model if none exists
- Start Rasa Inspect with proper CORS settings

### Testing Credentials

For testing the agent's functionality, use the following credentials and scenarios:

#### Time Slots
- 12:30 PM is always not available
- 12:00 PM is initially available but becomes unavailable by the time user reaches the final booking step

#### Authentication
- Phone number `+91 1234567890` is already registered for testing authentication
- OTP `789654` is always correct for account authentication
- OTP `987654` is always correct for payment verification
- For account creation verification, any OTP will work

### CORS Configuration

The Codespaces environment is configured to handle CORS issues when accessing the Rasa servers from your local browser. The forwarded ports will automatically open in your browser when the servers start.

## Environment Details

- Python: 3.10.0
- Rasa Pro
- Package manager: uv

## Local Development

If you prefer local development, follow these steps:

1. **Prerequisites**
   - Python 3.10.0 installed
   - Git installed
   - Rasa Pro License Key
   - OpenAI API Key with credits

2. **Clone the Repository**
   ```bash
   git clone https://github.com/shaik-ismail-27/agent_cue.git
   cd agent_cue
   ```

3. **Set Up Environment**
   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install uv package manager
   pip install 'uv[pyproject]'

   # Install Rasa Pro and dependencies
   uv pip install rasa-pro
   ```

4. **Configure Environment Variables**
   ```bash
   # Create .env file
   echo "RASA_PRO_LICENSE=your_rasa_pro_license_key" > .env
   echo "OPENAI_API_KEY=your_openai_api_key" >> .env

   # Source the environment variables
   source .env
   ```

5. **Train the Model**
   ```bash
   # Make sure you're in the agent_cue directory
   rasa train
   ```

6. **Set Up Backend Server**
   ```bash
   # Navigate to backend directory
   cd backend

   # Install Flask and CORS
   pip install flask flask-cors

   # Start the backend server
   python server.py
   ```

7. **Run the Agent With a default ui**
   ```bash
   # Start Rasa Inspect (includes both server and UI)
   rasa inspect --cors "*" --debug
   ```