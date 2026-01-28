# AI Dev Team

An automated development team powered by CrewAI that can process GitHub issues, analyze codebases, and implement solutions.

## 📁 Project Structure

```
ai-dev-team/
├── docs/              # Documentation files
├── scripts/           # Python and shell scripts
├── data/              # Data files (JSON, etc.)
├── config/            # Configuration files
├── runs/              # Execution runs and outputs
├── templates/         # Template files
└── README.md          # This file
```

## 🚀 Quick Start

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for detailed setup instructions.

### One-command setup & run

After creating your virtual environment and installing dependencies:

```bash
cd ~/ai-dev-team
source .venv/bin/activate
python3 scripts/main.py
```

The `main.py` script will:

- **Prompt for** your `GITHUB_TOKEN`, `GITHUB_REPO`, and optional `GITHUB_PROJECT_ID`
- **Write them to** the `.env` file
- **Run a simple GitHub issue analysis crew** for your repo

### Basic Setup

1. **Get GitHub Token**
   - Visit: https://github.com/settings/tokens
   - Generate a token with `repo` and `read:org` scopes

2. **Run Setup Script**
   ```bash
   cd ~/ai-dev-team
   ./scripts/setup_github_integration.sh
   ```

3. **Execute an Issue**
   ```bash
   source .venv/bin/activate
   python3 scripts/example_github_issue.py owner/repo 123
   ```

## 📚 Documentation

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Quick setup guide
- **[TERMINAL_COMMANDS.md](docs/TERMINAL_COMMANDS.md)** - Terminal command reference ⭐
- **[USER_STORY_PROCESSING.md](docs/USER_STORY_PROCESSING.md)** - Processing user stories with sub-tasks ⭐
- **[OUTPUT_EXPORT.md](docs/OUTPUT_EXPORT.md)** - Where outputs are saved and how to export ⭐
- **[DASHBOARD_GUIDE.md](docs/DASHBOARD_GUIDE.md)** - Complete dashboard usage guide
- **[USAGE.md](docs/USAGE.md)** - Usage instructions
- **[README_GITHUB.md](docs/README_GITHUB.md)** - Complete GitHub integration guide
- **[CONTEXT_GUIDE.md](docs/CONTEXT_GUIDE.md)** - Project context guide
- **[CREWAI_ORCHESTRATION.md](docs/CREWAI_ORCHESTRATION.md)** - CrewAI orchestration details

## 🛠️ Scripts

### Main Scripts
- `scripts/automated_crew.py` - Automated crew for issue processing
- `scripts/github_crew.py` - Full-featured GitHub crew
- `scripts/example_github_issue.py` - Simple example script
- `scripts/dashboard.py` - Streamlit dashboard
- `scripts/dashboard_streaming.py` - Dashboard with streaming output
- `scripts/dashboard_automated.py` - Automated dashboard

### Setup Scripts
- `scripts/setup_github_integration.sh` - GitHub integration setup
- `scripts/start_dashboard.sh` - Start the dashboard server (see [DASHBOARD_GUIDE.md](docs/DASHBOARD_GUIDE.md))

### Test Scripts
- `scripts/test_*.py` - Various test scripts

## 🔧 Configuration

Create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=owner/repo
OPENAI_API_KEY=your_openai_key_here  # Optional
```

## 📖 More Information

For detailed documentation, see the [docs/](docs/) directory.
