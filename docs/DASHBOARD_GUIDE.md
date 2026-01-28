# Dashboard Usage Guide

Complete guide to using and running the CrewAI Dashboards for GitHub issue processing.

## 🚀 Quick Terminal Commands

### Start Streaming Dashboard (Recommended)
```bash
cd ~/ai-dev-team
./scripts/start_dashboard.sh
```

### Start Any Dashboard Manually
```bash
cd ~/ai-dev-team
source .venv/bin/activate

# Streaming Dashboard
streamlit run scripts/dashboard_streaming.py --server.port=8001 --server.address=0.0.0.0

# Automated Dashboard
streamlit run scripts/dashboard_automated.py --server.port=8001 --server.address=0.0.0.0

# Basic Dashboard
streamlit run scripts/dashboard.py --server.port=8001 --server.address=0.0.0.0
```

### Access Dashboard
- Open browser: `http://localhost:8001`
- Or from network: `http://YOUR_SERVER_IP:8001`

### Stop Dashboard
Press `Ctrl+C` in the terminal, or:
```bash
pkill -f "streamlit run"
```

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Available Dashboards](#available-dashboards)
- [Quick Start](#quick-start)
- [Dashboard Details](#dashboard-details)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

Before running any dashboard, ensure you have:

1. **Virtual Environment Activated**
   ```bash
   cd ~/ai-dev-team
   source .venv/bin/activate
   ```

2. **GitHub Token Configured**
   - Your `.env` file should contain:
     ```env
     GITHUB_TOKEN=your_github_token_here
     GITHUB_REPO=owner/repo  # Optional, can be set in dashboard
     ```

3. **Required Dependencies**
   - Streamlit
   - PyGithub
   - CrewAI and related packages

## Available Dashboards

The project includes three different dashboards, each optimized for different use cases:

### 1. **Streaming Dashboard** (`dashboard_streaming.py`)
   - ✅ Real-time agent progress tracking
   - ✅ Live output streaming
   - ✅ Sub-issues detection
   - **Best for:** Monitoring long-running tasks

### 2. **Automated Dashboard** (`dashboard_automated.py`)
   - ✅ Automatic issue tracking
   - ✅ Batch processing
   - ✅ Progress persistence
   - **Best for:** Processing multiple issues sequentially

### 3. **Basic Dashboard** (`dashboard.py`)
   - ✅ Simple issue viewer
   - ✅ Manual execution
   - ✅ System information
   - **Best for:** Quick manual issue processing

## Quick Start

### Option 1: Using the Start Script (Recommended)

The easiest way to start the streaming dashboard:

```bash
cd ~/ai-dev-team
./scripts/start_dashboard.sh
```

This will:
- Activate the virtual environment
- Start the streaming dashboard on port 8001
- Make it accessible at `http://localhost:8001`

### Option 2: Manual Start

Start any dashboard manually:

```bash
cd ~/ai-dev-team
source .venv/bin/activate

# Streaming Dashboard (default)
streamlit run scripts/dashboard_streaming.py --server.port=8001 --server.address=0.0.0.0

# Automated Dashboard
streamlit run scripts/dashboard_automated.py --server.port=8001 --server.address=0.0.0.0

# Basic Dashboard
streamlit run scripts/dashboard.py --server.port=8001 --server.address=0.0.0.0
```

### Option 3: Custom Port

To use a different port:

```bash
export PORT=8080
./scripts/start_dashboard.sh
```

Or manually:
```bash
streamlit run scripts/dashboard_streaming.py --server.port=8080 --server.address=0.0.0.0
```

## Dashboard Details

### 🎥 Streaming Dashboard (`dashboard_streaming.py`)

**Features:**
- Real-time output streaming as agents work
- Live agent status indicators (Product Manager, Architect, Developer, Reviewer)
- Progress bars for each agent
- Sub-issues detection and display
- Live output stream (last 200 lines)

**How to Use:**

1. **Start the Dashboard**
   ```bash
   ./scripts/start_dashboard.sh
   ```

2. **Access the Dashboard**
   - Open your browser: `http://localhost:8001`
   - Or from another device: `http://YOUR_SERVER_IP:8001`

3. **Load Issues**
   - Enter repository name: `owner/repo`
   - Click "Load Issues"
   - Wait for issues to load

4. **Process an Issue**
   - Browse the list of open issues
   - Click "🚀 Process" on any issue
   - Watch real-time progress:
     - Agent status updates
     - Live output stream
     - Progress indicators

5. **Monitor Progress**
   - See which agent is currently working
   - View live output as it's generated
   - Track completion status for each agent

**Use Cases:**
- Long-running issue processing
- Debugging agent behavior
- Monitoring crew performance
- Understanding workflow execution

---

### ⚙️ Automated Dashboard (`dashboard_automated.py`)

**Features:**
- Automatic issue tracking (remembers processed issues)
- Batch processing mode
- Skip issues functionality
- Processed/unprocessed filtering
- Progress saved to `data/processed_issues.json`

**How to Use:**

1. **Start the Dashboard**
   ```bash
   source .venv/bin/activate
   streamlit run scripts/dashboard_automated.py --server.port=8001 --server.address=0.0.0.0
   ```

2. **Load Issues**
   - Enter repository: `owner/repo`
   - Click "Load Issues"

3. **Process Issues**

   **Single Issue:**
   - Click "🚀 Process This Issue" to process the next unprocessed issue
   - Or click "⏭️ Skip This Issue" to mark it as processed without running

   **Batch Processing:**
   - Click "🔄 Process All Remaining" to automatically process all unprocessed issues
   - The dashboard will continue to the next issue after each completion

4. **View Progress**
   - See "Processed Issues" count
   - See "Remaining" unprocessed count
   - Filter issues: All / Unprocessed / Processed

5. **Issue List**
   - View all issues with status indicators:
     - ✅ = Processed
     - ⏳ = Unprocessed
   - Click individual issues to process them

**Use Cases:**
- Processing multiple issues in sequence
- Automated workflow execution
- Batch issue resolution
- Progress tracking across sessions

---

### 📊 Basic Dashboard (`dashboard.py`)

**Features:**
- Simple issue viewer
- Manual issue execution
- Issue filtering and sorting
- System information display
- Runs and templates metrics

**How to Use:**

1. **Start the Dashboard**
   ```bash
   source .venv/bin/activate
   streamlit run scripts/dashboard.py --server.port=8001 --server.address=0.0.0.0
   ```

2. **Load Issues**
   - Enter repository: `owner/repo`
   - Click "Load Issues"

3. **Filter and Sort**
   - Filter by label
   - Sort by: Updated, Created, or Number

4. **Execute Issues**
   - Browse issues in expandable sections
   - Click "🚀 Execute #N" on any issue
   - View output after completion

5. **View System Info**
   - Check directory status
   - View environment configuration
   - See runs and templates count

**Use Cases:**
- Quick issue exploration
- Manual issue processing
- System status checking
- Simple workflow execution

---

## Configuration

### Environment Variables

Create or edit `.env` file in the project root:

```env
# Required
GITHUB_TOKEN=ghp_your_token_here

# Optional
GITHUB_REPO=owner/repo
OPENAI_API_KEY=sk-your-key-here
PORT=8001
```

### GitHub Token Setup

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes:
   - ✅ `repo` - Full control of private repositories
   - ✅ `read:org` - Read org and team membership
4. Copy the token and add to `.env`

Or use the setup script:
```bash
./scripts/setup_github_integration.sh
```

### Port Configuration

Default port is **8001**. To change:

```bash
# Using start script
export PORT=8080
./scripts/start_dashboard.sh

# Or manually
streamlit run scripts/dashboard_streaming.py --server.port=8080
```

## Accessing the Dashboard

### Local Access
- Open browser: `http://localhost:8001`

### Remote Access
- From another device: `http://YOUR_SERVER_IP:8001`
- Ensure firewall allows port 8001
- Use `--server.address=0.0.0.0` (already included in scripts)

### Network Access
The dashboards are configured to listen on `0.0.0.0`, making them accessible from:
- Localhost
- Local network
- Remote connections (if port is forwarded)

## Troubleshooting

### Dashboard Won't Start

**Issue:** `streamlit: command not found`
```bash
# Solution: Activate virtual environment
source .venv/bin/activate
pip install streamlit
```

**Issue:** Port already in use
```bash
# Solution: Use a different port
export PORT=8080
./scripts/start_dashboard.sh
```

**Issue:** Permission denied on script
```bash
# Solution: Make script executable
chmod +x scripts/start_dashboard.sh
```

### GitHub Authentication Errors

**Issue:** "Failed to authenticate with GitHub"
- Check `.env` file exists and contains `GITHUB_TOKEN`
- Verify token is valid and has correct scopes
- Regenerate token if needed

**Issue:** "GITHUB_TOKEN not found"
- Ensure `.env` file is in project root: `~/ai-dev-team/.env`
- Check file permissions
- Verify token format: `GITHUB_TOKEN=ghp_...`

### Issues Not Loading

**Issue:** "Failed to load issues"
- Verify repository name format: `owner/repo`
- Check repository exists and is accessible
- Ensure token has `repo` scope
- Check network connection

**Issue:** No issues shown
- Repository may have no open issues
- Try a different repository
- Check issue filters

### Processing Errors

**Issue:** "automated_crew.py not found"
- Scripts should be in `scripts/` directory
- Verify file structure is correct
- Check working directory

**Issue:** Execution timeout
- Increase timeout in dashboard code (default: 60-300 seconds)
- Check if issue processing is taking too long
- Review agent configuration

**Issue:** No output shown
- Check if execution completed successfully
- Review error messages in dashboard
- Check script logs

### Performance Issues

**Issue:** Dashboard is slow
- Reduce number of issues loaded (filter)
- Close other resource-intensive applications
- Check server resources

**Issue:** Real-time updates not working
- Ensure using `dashboard_streaming.py` for live updates
- Check browser console for errors
- Refresh the page

## Advanced Usage

### Running Multiple Dashboards

Run different dashboards on different ports:

```bash
# Terminal 1: Streaming Dashboard
streamlit run scripts/dashboard_streaming.py --server.port=8001

# Terminal 2: Automated Dashboard
streamlit run scripts/dashboard_automated.py --server.port=8002

# Terminal 3: Basic Dashboard
streamlit run scripts/dashboard.py --server.port=8003
```

### Background Execution

Run dashboard in background:

```bash
nohup streamlit run scripts/dashboard_streaming.py --server.port=8001 > dashboard.log 2>&1 &
```

Stop background process:
```bash
pkill -f "streamlit run"
```

### Custom Configuration

Create custom dashboard script:

```bash
#!/bin/bash
cd "$HOME/ai-dev-team"
source .venv/bin/activate
export PORT=${PORT:-8001}
export STREAMLIT_SERVER_HEADLESS=true
streamlit run scripts/dashboard_streaming.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true
```

## Best Practices

1. **Start with Streaming Dashboard** for first-time use to understand the workflow
2. **Use Automated Dashboard** for batch processing multiple issues
3. **Check GitHub Token** before starting (saves time)
4. **Monitor Resources** when processing many issues
5. **Save Progress** - Automated dashboard saves to `data/processed_issues.json`
6. **Review Output** after each issue to ensure quality

## Related Documentation

- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [USAGE.md](USAGE.md) - General usage instructions
- [README_GITHUB.md](README_GITHUB.md) - GitHub integration details
- [CREWAI_ORCHESTRATION.md](CREWAI_ORCHESTRATION.md) - CrewAI workflow details

## Support

For issues or questions:
1. Check this guide's troubleshooting section
2. Review error messages in the dashboard
3. Check script logs
4. Verify configuration files

---

**Last Updated:** January 2025
**Dashboard Version:** 1.0
