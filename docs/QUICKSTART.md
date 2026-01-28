# Quick Start: Connect CrewAI to GitHub

## 🚀 3-Step Setup

### Step 1: Get GitHub Token
1. Visit: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:org`
4. Copy the token

### Step 2: Run Setup
```bash
cd ~/ai-dev-team
./scripts/setup_github_integration.sh
```
Enter your token when prompted.

### Step 3: Execute an Issue
```bash
source .venv/bin/activate
python3 scripts/example_github_issue.py owner/repo 123
```

## 📁 Project Structure

- `scripts/` - All Python and shell scripts
  - `github_crew.py` - Full-featured GitHub crew with multiple agents
  - `example_github_issue.py` - Simple example script
  - `setup_github_integration.sh` - Interactive setup script
- `docs/` - Documentation files
  - `README_GITHUB.md` - Complete documentation

## 🔧 Configuration

Your `.env` file should contain:
```env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=owner/repo
```

## 💡 Examples

### Simple Issue Analysis
```bash
python3 scripts/example_github_issue.py owner/repo 123
```

### Full Crew Execution
```bash
python3 scripts/github_crew.py 123 owner/repo
```

### Search All Issues
```bash
python3 scripts/example_github_issue.py owner/repo
```

## 🎯 What It Does

1. **Searches** GitHub repositories for issues, code, and PRs
2. **Analyzes** issue requirements and context
3. **Finds** relevant code files
4. **Provides** implementation plans and solutions

## 📚 More Info

See `README_GITHUB.md` for detailed documentation.
