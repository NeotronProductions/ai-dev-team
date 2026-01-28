# AI Dev Team

An automated, multi-agent development workflow powered by **CrewAI**. It can connect to GitHub, analyze issues + repository context, and (optionally) apply changes in a local checkout of a target project.

- **Docs index**: `docs/README.md`
- **Quick start**: `docs/QUICKSTART.md`
- **Reference implementation target**: [NeotronProductions/Beautiful-Timetracker-App](https://github.com/NeotronProductions/Beautiful-Timetracker-App)

---

## What this repo is (and isn’t)

- **This repo**: the runner/orchestrator (scripts + helpers) that talks to GitHub and coordinates agents.
- **Not this repo**: the app you are changing. For implementation runs you’ll typically clone a *separate* target repo locally (example target: `~/dev/Beautiful-Timetracker-App`).

---

## Project structure

```
ai-dev-team/
├── crew_runner/          # Refactored core modules (schema, safety, git ops, etc.)
├── docs/                 # Documentation
├── presentation/         # Slides / infographic
├── scripts/              # Entrypoints and utilities
└── tests/                # Unit tests for safety/patch logic
```

---

## Setup

### Prerequisites

- **Python**: 3.10+ recommended
- **Git**: required for the *target repo* you plan to modify
- **GitHub token**: classic PAT with `repo` and `read:org` scopes (for private repos / orgs)
- **LLM (choose one)**:
  - **Ollama (local)**: recommended for “no-OpenAI” flows
  - **OpenAI API key**: optional, used when you force OpenAI or use scripts that depend on it

### Create a virtualenv and install dependencies

This project doesn’t currently ship a `requirements.txt`, so install dependencies directly:

```bash
cd ~/ai-dev-team
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -U pip

# Core
pip install crewai crewai-tools python-dotenv PyGithub requests pydantic

# Dashboard (optional)
pip install streamlit

# Composio (optional, advanced GitHub actions)
pip install composio-core composio-openai
```

### Configure `.env`

Run the interactive setup script (expects `.venv` to exist):

```bash
cd ~/ai-dev-team
./scripts/setup_github_integration.sh
```

Minimum `.env`:

```env
GITHUB_TOKEN=ghp_...
GITHUB_REPO=owner/repo
```

Optional `.env` keys used by some scripts:

```env
OPENAI_API_KEY=sk-...
FORCE_OPENAI=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:3b
OLLAMA_TIMEOUT=1200
```

---

## Run it

### 1) Interactive initializer (good first run)

```bash
source .venv/bin/activate
python3 scripts/main.py
```

### 2) Analyze a single GitHub issue (simple)

- **Option A (local LLM via Ollama)**: `scripts/github_simple.py` (no OpenAI key, but requires Ollama)

```bash
source .venv/bin/activate
python3 scripts/github_simple.py owner/repo 123
```

- **Option B (GitHub search tool / semantic-ish)**: `scripts/example_github_issue.py`

```bash
source .venv/bin/activate
python3 scripts/example_github_issue.py owner/repo 123
```

### 3) Automated end-to-end processing (plan → apply → verify → git ops)

`scripts/automated_crew.py` is the “full pipeline” runner.

```bash
source .venv/bin/activate

# Process up to N issues (default: 5)
python3 scripts/automated_crew.py owner/repo 3

# Process a specific issue
python3 scripts/automated_crew.py owner/repo 1 529

# Force OpenAI (skip Ollama)
python3 scripts/automated_crew.py owner/repo 1 529 --openai
```

Notes:
- The script applies changes in a **local checkout of the target repo**.
- By default, it uses a hard-coded work directory: `~/dev/Beautiful-Timetracker-App` (see `WORK_DIR` near the top of `scripts/automated_crew.py`).

### 4) Dashboard (optional)

```bash
./scripts/start_dashboard.sh
```

By default it binds to `0.0.0.0` on port `8001` (override with `PORT=...`).

---

## Outputs & artifacts (where to look)

- **Target repo** (the project being modified):
  - `implementations/issue_<N>_plan.md` (implementation plan)
  - `crewai_patch.diff` (patch / diff artifact)
- **This repo**:
  - Unit tests in `tests/`
  - Most user-facing guidance in `docs/` (start at `docs/README.md`)

---

## Tests

```bash
source .venv/bin/activate
python -m unittest -v
```

---

## Status

This is an active experiment; expect breaking changes as the workflow evolves.

---

## License

Intended license is **MIT**, but this repo does not currently include a `LICENSE` file.