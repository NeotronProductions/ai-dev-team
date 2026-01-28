# Timeout Troubleshooting Guide

## Error: telemetry.crewai.com Connection Timeout

If you see:
```
HTTPSConnectionPool(host='telemetry.crewai.com', port=4319): Max retries exceeded ...
Connection to telemetry.crewai.com timed out. (connect timeout=30)
```

CrewAI sends telemetry by default; when that endpoint is unreachable (firewall, network, or offline), it can cause a 30-second timeout.

**Fix:** The project scripts now disable OpenTelemetry by default. You can also set in `.env`:
```bash
OTEL_SDK_DISABLED=true
```
Or use CrewAI’s own flag: `CREWAI_DISABLE_TELEMETRY=true`.

---

## Error: Ollama Timeout After 600 Seconds

If you see this error:
```
LLM Call Failed
Error: litellm.APIConnectionError: OllamaException - litellm.Timeout: Connection timed out after 600.0 seconds.
```

This means Ollama took too long to respond (10 minutes default timeout).

## Why This Happens

1. **Complex Tasks**: Large user stories with many sub-tasks
2. **Slow Model**: Smaller models (like qwen2.5-coder:3b) are slower
3. **System Load**: Ollama server may be overloaded
4. **Network Issues**: Connection problems between CrewAI and Ollama

## Solutions

### Solution 1: Increase Timeout (Recommended for Complex Tasks)

Set a longer timeout in your `.env` file:

```bash
# Add to ~/ai-dev-team/.env
OLLAMA_TIMEOUT=1800  # 30 minutes (in seconds)
```

Or export before running:
```bash
export OLLAMA_TIMEOUT=1800
python3 scripts/automated_crew.py owner/repo 1 550
```

**Timeout values:**
- `600` = 10 minutes (default)
- `1200` = 20 minutes (new default in script)
- `1800` = 30 minutes (for very complex tasks)
- `3600` = 60 minutes (maximum recommended)

### Solution 2: Use OpenAI Instead (Faster)

If Ollama is too slow, use OpenAI as the primary LLM:

```bash
# Ensure OpenAI key is set
export OPENAI_API_KEY=sk-your-key-here

# The script will automatically fallback to OpenAI if Ollama fails
python3 scripts/automated_crew.py owner/repo 1 550
```

Or force OpenAI by stopping Ollama:
```bash
# Stop Ollama temporarily
pkill ollama

# Run crew (will use OpenAI)
python3 scripts/automated_crew.py owner/repo 1 550
```

### Solution 3: Use a Faster Ollama Model

Switch to a faster model:

```bash
# In ~/ai-dev-team/.env
OLLAMA_MODEL=llama3.2:3b  # Faster than qwen2.5-coder:3b
```

Or use a larger, more capable model (slower but better quality):
```bash
OLLAMA_MODEL=qwen2.5-coder:7b  # Better quality, may be slower
```

### Solution 4: Check Ollama Status

Verify Ollama is running and responsive:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test a simple query
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:3b",
  "prompt": "Hello",
  "stream": false
}'
```

If Ollama is slow or unresponsive:
```bash
# Restart Ollama service
systemctl restart ollama  # If running as service
# Or
ollama serve  # If running manually
```

### Solution 5: Process Sub-Tasks Separately

For complex user stories with many sub-tasks, process them individually:

```bash
# Process parent first
python3 scripts/automated_crew.py owner/repo 1 550

# Then process sub-tasks one by one (smaller, faster tasks)
python3 scripts/automated_crew.py owner/repo 1 551
python3 scripts/automated_crew.py owner/repo 1 552
python3 scripts/automated_crew.py owner/repo 1 553
python3 scripts/automated_crew.py owner/repo 1 554
python3 scripts/automated_crew.py owner/repo 1 555
```

## Configuration Options

### Environment Variables

Add to `~/ai-dev-team/.env`:

```env
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:3b
OLLAMA_TIMEOUT=1200  # Timeout in seconds (20 minutes)

# OpenAI (fallback)
OPENAI_API_KEY=sk-your-key-here
```

### Recommended Settings by Task Complexity

**Simple Tasks (1-2 sub-tasks):**
```env
OLLAMA_TIMEOUT=600  # 10 minutes
```

**Medium Tasks (3-5 sub-tasks):**
```env
OLLAMA_TIMEOUT=1200  # 20 minutes
```

**Complex Tasks (6+ sub-tasks or large user stories):**
```env
OLLAMA_TIMEOUT=1800  # 30 minutes
# Or use OpenAI for faster processing
```

## Automatic Fallback

The script is configured to automatically fallback to OpenAI if Ollama fails:

1. **Ollama timeout** → Falls back to OpenAI
2. **Ollama connection error** → Falls back to OpenAI
3. **Ollama not available** → Uses OpenAI

You'll see messages like:
```
⚠ Failed to configure Ollama: [error]
🔄 Falling back to OpenAI...
✓ Using OpenAI (gpt-4o-mini) - fallback from Ollama
```

## Monitoring Progress

Watch for timeout warnings:

```bash
# Run with verbose output
python3 scripts/automated_crew.py owner/repo 1 550

# Watch for:
# - "LLM Call Failed" messages
# - Timeout errors
# - Fallback messages
```

## Best Practices

### For Large User Stories (like US-001)

1. **Use OpenAI** for faster processing:
   ```bash
   export OPENAI_API_KEY=sk-your-key-here
   python3 scripts/automated_crew.py owner/repo 1 550
   ```

2. **Or increase timeout** if you prefer Ollama:
   ```bash
   export OLLAMA_TIMEOUT=1800
   python3 scripts/automated_crew.py owner/repo 1 550
   ```

3. **Or process sequentially** (sub-tasks separately):
   ```bash
   export SUB_ISSUE_STRATEGY=sequential
   python3 scripts/automated_crew.py owner/repo 1 550
   ```

### For Testing/Development

Use Ollama with shorter timeouts to catch issues quickly:
```bash
export OLLAMA_TIMEOUT=300  # 5 minutes
python3 scripts/automated_crew.py owner/repo 1 550
```

## Troubleshooting Steps

1. **Check timeout setting:**
   ```bash
   grep OLLAMA_TIMEOUT ~/ai-dev-team/.env
   ```

2. **Test Ollama response time:**
   ```bash
   time curl -X POST http://localhost:11434/api/generate \
     -d '{"model": "qwen2.5-coder:3b", "prompt": "Hello", "stream": false}'
   ```

3. **Check system resources:**
   ```bash
   # CPU and memory usage
   top
   # Or
   htop
   ```

4. **Check Ollama logs:**
   ```bash
   # If running as service
   journalctl -u ollama -n 50
   ```

## Quick Fix for US-001

For processing US-001 (which has 5 sub-tasks), recommended approach:

```bash
# Option 1: Use OpenAI (fastest)
export OPENAI_API_KEY=sk-your-key-here
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 550

# Option 2: Increase Ollama timeout
export OLLAMA_TIMEOUT=1800
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 550

# Option 3: Process sub-tasks separately
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 551
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 552
# ... etc
```

## Related Documentation

- [TERMINAL_COMMANDS.md](TERMINAL_COMMANDS.md) - How to run the crew
- [USER_STORY_PROCESSING.md](USER_STORY_PROCESSING.md) - Processing user stories
- [OUTPUT_TROUBLESHOOTING.md](OUTPUT_TROUBLESHOOTING.md) - Output issues

---

**Last Updated:** January 2025
