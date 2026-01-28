# GitHub Integration - Usage Guide

## ✅ Your Setup Status

- ✓ GitHub token configured
- ✓ Token saved securely in `.env`
- ✓ PyGithub installed

## 🚀 Two Ways to Use

### Option 1: Simple Version (No OpenAI Required) ⭐ Recommended

This version uses direct GitHub API calls and works immediately:

```bash
cd ~/ai-dev-team
source .venv/bin/activate

# Analyze a specific issue
python3 scripts/github_simple.py owner/repo 123
```

**Example:**
```bash
python3 scripts/github_simple.py crewAIInc/crewAI 1
```

### Option 2: Full Version (Requires OpenAI API Key)

For semantic search through codebases, you need an OpenAI API key:

1. Add to `.env`:
```bash
echo "OPENAI_API_KEY=sk-your-key-here" >> ~/ai-dev-team/.env
```

2. Then use:
```bash
python3 scripts/example_github_issue.py owner/repo 123
# or
python3 scripts/github_crew.py 123 owner/repo
```

## 📋 Quick Examples

### Analyze an Issue
```bash
python3 github_simple.py owner/repo 42
```

### List Your Repositories
```python
from github import Github
from dotenv import load_dotenv
import os

load_dotenv()
g = Github(os.getenv("GITHUB_TOKEN"))
for repo in g.get_user().get_repos():
    print(f"{repo.full_name} - {repo.description}")
```

## 🔧 Current Configuration

Your `.env` file contains:
- `GITHUB_TOKEN` ✓ (configured)

To add OpenAI (optional):
```bash
echo "OPENAI_API_KEY=sk-..." >> ~/ai-dev-team/.env
```

## 📚 Available Scripts

1. **`github_simple.py`** - Simple, works without OpenAI ⭐
2. **`github_crew.py`** - Full multi-agent crew (needs OpenAI)
3. **`example_github_issue.py`** - Example with semantic search (needs OpenAI)

## 🎯 Next Steps

Try analyzing an issue:
```bash
cd ~/ai-dev-team
source .venv/bin/activate
python3 github_simple.py owner/repo <issue_number>
```

Replace `owner/repo` with your repository and `<issue_number>` with the issue number!
