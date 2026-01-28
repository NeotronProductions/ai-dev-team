# Terminal Commands Guide

Quick reference for running CrewAI crews and dashboards from the terminal.

## 🚀 Quick Reference

### Run Automated Crew (Full Processing)
```bash
cd ~/ai-dev-team
source .venv/bin/activate
python3 scripts/automated_crew.py owner/repo [max_issues|issue_number]
```

### Run Simple Issue Analysis
```bash
python3 scripts/example_github_issue.py owner/repo [issue_number]
```

### Run Dashboard
```bash
./scripts/start_dashboard.sh
```

---

## 📋 Detailed Commands

### 1. Automated Crew (`automated_crew.py`)

The main crew script that processes GitHub issues with full agent workflow.

**Basic Usage:**
```bash
cd ~/ai-dev-team
source .venv/bin/activate
python3 scripts/automated_crew.py owner/repo
```

**Force OpenAI (Skip Ollama):**
```bash
# Use --openai flag to force OpenAI instead of Ollama
python3 scripts/automated_crew.py owner/repo 1 550 --openai

# Or set environment variable
export FORCE_OPENAI=true
python3 scripts/automated_crew.py owner/repo 1 550
```

**Process Multiple Issues:**
```bash
# Process up to 5 issues (default)
python3 scripts/automated_crew.py owner/repo 5

# Process up to 10 issues
python3 scripts/automated_crew.py owner/repo 10
```

**Process Specific Issue:**
```bash
# Process issue #123
python3 scripts/automated_crew.py owner/repo 1 123

# Process issue #123 with OpenAI (skip Ollama)
python3 scripts/automated_crew.py owner/repo 1 123 --openai
```

**Examples:**
```bash
# Process 3 issues from a repository
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 3

# Process specific issue #608
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 608

# Process issue #550 with OpenAI (faster, avoids timeout)
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 550 --openai
```

**What it does:**
- Creates a crew with 4 agents: Product Manager, Architect, Developer, Code Reviewer
- Processes issues sequentially
- Implements solutions
- Creates commits and PRs (if configured)

---

### 2. Simple Example (`example_github_issue.py`)

Quick issue analysis without full implementation.

**Basic Usage:**
```bash
cd ~/ai-dev-team
source .venv/bin/activate
python3 scripts/example_github_issue.py owner/repo
```

**Analyze Specific Issue:**
```bash
python3 scripts/example_github_issue.py owner/repo 123
```

**Examples:**
```bash
# Analyze issue #123
python3 scripts/example_github_issue.py crewAIInc/crewAI 123

# Search and analyze top issues
python3 scripts/example_github_issue.py owner/repo
```

**What it does:**
- Analyzes GitHub issues
- Searches repository code
- Provides solution plans
- No code implementation

---

### 3. GitHub Working (`github_working.py`)

Basic GitHub issue analysis and display.

**Usage:**
```bash
cd ~/ai-dev-team
source .venv/bin/activate
python3 scripts/github_working.py owner/repo issue_number
```

**Example:**
```bash
python3 scripts/github_working.py owner/repo 123
```

**What it does:**
- Fetches issue from GitHub
- Analyzes issue content
- Displays formatted results

---

### 4. GitHub Simple (`github_simple.py`)

Simple GitHub API-based issue analysis (no OpenAI required).

**Usage:**
```bash
cd ~/ai-dev-team
source .venv/bin/activate
python3 scripts/github_simple.py owner/repo issue_number
```

**Example:**
```bash
python3 scripts/github_simple.py crewAIInc/crewAI 1
```

**What it does:**
- Uses direct GitHub API calls
- No OpenAI API key needed
- Fast and simple analysis

---

### 5. GitHub Crew (`github_crew.py`)

Full-featured GitHub crew with multiple agents.

**Usage:**
```bash
cd ~/ai-dev-team
source .venv/bin/activate
python3 scripts/github_crew.py issue_number owner/repo
```

**Example:**
```bash
python3 scripts/github_crew.py 123 owner/repo
```

**What it does:**
- Full crew with multiple specialized agents
- Comprehensive issue analysis
- Code search and implementation planning

---

## 🎯 Common Workflows

### Workflow 1: Quick Issue Analysis
```bash
# Simple analysis without implementation
python3 scripts/example_github_issue.py owner/repo 123
```

### Workflow 2: Process Single Issue
```bash
# Full processing with implementation
python3 scripts/automated_crew.py owner/repo 1 123
```

### Workflow 3: Batch Process Issues
```bash
# Process multiple issues automatically
python3 scripts/automated_crew.py owner/repo 5
```

### Workflow 4: Monitor with Dashboard
```bash
# Terminal 1: Start dashboard
./scripts/start_dashboard.sh

# Terminal 2: Run crew (dashboard will show progress)
python3 scripts/automated_crew.py owner/repo 3
```

---

## 🔧 Prerequisites

Before running any script:

1. **Activate Virtual Environment**
   ```bash
   cd ~/ai-dev-team
   source .venv/bin/activate
   ```

2. **Check Environment Variables**
   ```bash
   # Check if .env exists
   cat .env
   
   # Should contain at minimum:
   # GITHUB_TOKEN=your_token_here
   ```

3. **Verify GitHub Token**
   ```bash
   # Test GitHub connection
   python3 scripts/test_github_connection.py
   ```

---

## 📊 Command Comparison

| Script | Purpose | Arguments | Output |
|-------|---------|-----------|--------|
| `automated_crew.py` | Full processing | `repo [max\|issue]` | Implementation |
| `example_github_issue.py` | Quick analysis | `repo [issue]` | Analysis only |
| `github_working.py` | Basic analysis | `repo issue` | Formatted display |
| `github_simple.py` | Simple API | `repo issue` | Basic info |
| `github_crew.py` | Full crew | `issue repo` | Comprehensive |

---

## 🐛 Troubleshooting

### Error: "GITHUB_TOKEN not found"
```bash
# Check .env file
cat .env

# Or set manually
export GITHUB_TOKEN=your_token_here
```

### Error: "Module not found"
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Error: "Repository not found"
- Verify repository name format: `owner/repo`
- Check repository exists and is accessible
- Ensure token has correct permissions

### Script Hangs or Takes Too Long
- Check network connection
- Verify GitHub API rate limits
- Review issue complexity (large issues take longer)

---

## 💡 Tips

1. **Start Simple**: Use `example_github_issue.py` for quick tests
2. **Use Dashboard**: Monitor long-running tasks with dashboard
3. **Check Logs**: Review output for detailed progress
4. **Test First**: Try with a small issue before batch processing
5. **Save Output**: Redirect output to file for review:
   ```bash
   python3 scripts/automated_crew.py owner/repo 3 > output.log 2>&1
   ```

---

## 📝 Example Session

```bash
# 1. Navigate to project
cd ~/ai-dev-team

# 2. Activate environment
source .venv/bin/activate

# 3. Quick test with simple script
python3 scripts/example_github_issue.py owner/repo 123

# 4. If successful, run full crew
python3 scripts/automated_crew.py owner/repo 1 123

# 5. Or process multiple issues
python3 scripts/automated_crew.py owner/repo 5

# 6. Monitor in another terminal with dashboard
./scripts/start_dashboard.sh
```

---

## 🔗 Related Documentation

- [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md) - Dashboard usage
- [QUICKSTART.md](QUICKSTART.md) - Initial setup
- [USAGE.md](USAGE.md) - General usage guide

---

**Last Updated:** January 2025
