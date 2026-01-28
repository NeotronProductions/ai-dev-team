# Ollama Setup for GitHub Integration

The `github_simple.py` script uses **qwen2.5-coder:3b** via Ollama.

## Quick Setup

1. **Install Ollama** (if not installed):
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Start Ollama**:
   ```bash
   ollama serve
   ```
   Or as a service:
   ```bash
   sudo systemctl enable ollama
   sudo systemctl start ollama
   ```

3. **Pull the model**:
   ```bash
   ollama pull qwen2.5-coder:3b
   ```

4. **Verify setup**:
   ```bash
   cd ~/ai-dev-team
   python3 check_ollama.py
   ```

## Using the Script

Once Ollama is running with qwen2.5-coder:3b:

```bash
cd ~/ai-dev-team
source .venv/bin/activate
python3 github_simple.py owner/repo 123
```

## Alternative: Use OpenAI

If you prefer OpenAI instead:

```bash
echo "OPENAI_API_KEY=sk-..." >> ~/ai-dev-team/.env
```

Then the script will automatically use OpenAI if Ollama is not available.
