# Rasa Agent Project

This repository contains a Rasa conversational AI agent.

## Running with GitHub Codespaces

This project is configured to work with GitHub Codespaces, providing a fully configured development environment in the cloud.

### Using Codespaces

1. Click the "Code" button on the repository page
2. Select the "Codespaces" tab
3. Click "Create codespace on main"
4. Wait for the environment to build (this may take a few minutes)
5. Once loaded, you can:
   - Train the model: `rasa train`
   - Run Rasa Inspect: `rasa inspect`
   
   This will automatically start both the Rasa server and the actions server, and open the UI in your browser.

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

### CORS Configuration

The Codespaces environment is configured to handle CORS issues when accessing the Rasa servers from your local browser. The forwarded ports will automatically open in your browser when the servers start.

## Environment Details

- Python: 3.10.0
- Rasa Pro
- Package manager: uv

## Local Development

If you prefer local development, ensure you have Python 3.10 installed and create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install 'uv[pyproject]'
uv pip install rasa-pro
```
