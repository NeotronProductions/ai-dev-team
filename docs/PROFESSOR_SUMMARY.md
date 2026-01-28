## Project summary: Multi‑Agent “AI Dev Team” for GitHub Issues

### One‑sentence overview
This project is an automation layer around **CrewAI** that connects to **GitHub**, runs a **multi‑agent software team workflow** on issues (requirements → plan → implementation → review), and outputs a **reviewed code patch** (and optionally creates a branch/commit/PR).

### What problem it solves
Software work often starts as an unstructured GitHub issue. This project demonstrates how an agent‑orchestration framework can:
- Convert an issue into clear requirements and acceptance criteria
- Produce a minimal technical plan
- Generate an implementation (as a unified diff patch)
- Perform a review pass for correctness/safety/quality
- Optionally automate delivery steps (apply patch locally, commit, push, open PR)

### What CrewAI is (in this project)
**CrewAI** is an **agent orchestration framework** that lets you:
- Define multiple AI agents with distinct roles/goals
- Define tasks with explicit ordering and dependencies
- Pass context/results from one task to the next
- Coordinate LLM calls across the workflow

In this repo, CrewAI is the “workflow engine” that sequences the agent roles and ensures outputs from earlier steps feed later steps (e.g., requirements → architecture plan → patch → review).

### How the AI “dev team” is set up
The main automated workflow (`automated_crew.py`) models a small software team:
- **Product Manager**: turns an issue into a user story + acceptance criteria + scope/risks
- **Software Architect**: proposes a minimal implementation plan, files to change, and test approach
- **Developer**: outputs a **single unified diff patch** implementing the solution
- **Code Reviewer**: reviews the patch for correctness, edge cases, security, and maintainability

The conceptual overview doc also describes a simpler 3‑role pipeline (Analyst → Implementer → Reviewer); the automated script uses the expanded 4‑role “PM/Architect/Dev/Reviewer” team.

### High-level architecture
- **Automation layer (this repo’s scripts)**
  - GitHub API integration (issue fetching, repo access, optional project-board movement)
  - Tracking of processed issues (`processed_issues.json`)
  - Optional UI dashboards (Streamlit) to load issues and trigger runs
  - Optional local git operations (apply patch, branch/commit, push, PR creation)
- **CrewAI orchestration**
  - Agent definitions + tasks + dependency chain
- **LLM backend**
  - Prefers **Ollama** (local model) if available
  - Falls back to **OpenAI** if configured

### Inputs and outputs
- **Inputs**
  - GitHub repository (`owner/repo`)
  - Issue number(s) (one issue or multiple issues)
  - Optional project-board “pipeline” configuration (column names)
  - Optional local working directory that contains the cloned target repo
- **Outputs**
  - Requirements summary (user story + acceptance criteria)
  - Minimal technical plan (files to change, approach, tests)
  - Unified diff patch (can be applied to a repo)
  - Review feedback
  - Saved run artifacts (e.g., per-issue plan/patch files under an `implementations/` folder in the target repo)
  - Optionally: git branch/commit and a GitHub pull request

### What runs where (important implementation note)
`automated_crew.py` uses a **hardcoded default working directory**:
- `WORK_DIR = ~/dev/Beautiful-Timetracker-App`

This means the automated patch-apply / git-commit behavior is intended to operate on a local clone at that path (unless the script is modified).

### LLM backends supported
- **Ollama (local)**: default model is `qwen2.5-coder:3b` (configurable)
- **OpenAI (hosted)**: used if `OPENAI_API_KEY` is set and Ollama is unavailable

### Configuration (environment variables)
Primary:
- `GITHUB_TOKEN`: required to access GitHub via API
- `GITHUB_REPO`: default repo (`owner/repo`) used by some scripts/dashboards

LLM backend:
- `OLLAMA_BASE_URL` (default `http://localhost:11434`)
- `OLLAMA_MODEL` (default `qwen2.5-coder:3b`)
- `OPENAI_API_KEY` (optional; enables OpenAI fallback / some “full” flows)

Automation behavior (used by the automated workflow):
- `PROCESS_SUB_ISSUES` (default true): include or process linked “sub issues”
- `SUB_ISSUE_STRATEGY` (e.g., `include` or `sequential`)
- `MOVE_IN_PIPELINE` (default true): move issues on a GitHub project board
- `PIPELINE_IN_PROGRESS_COLUMN` / `PIPELINE_DONE_COLUMN`
- `AUTO_PUSH` (default false): if true, push branch and attempt to create PR

### How to run (typical demo paths)
CLI examples:
- **Simple GitHub analysis (no OpenAI required)**: `github_simple.py`
- **CrewAI-based GitHub issue execution**: `github_crew.py` / `example_github_issue.py`
- **Automated multi-issue processing with patch generation**: `automated_crew.py`

UI examples:
- **Streamlit dashboard**: `dashboard.py` (manual issue execution)
- **Automated Streamlit dashboard**: `dashboard_automated.py` (process issues one-by-one)

### Guardrails and limitations (what’s “safe” vs “not guaranteed”)
Guardrails in concept:
- Role separation: independent review step after implementation
- Patch-based output: the “Developer” agent is instructed to output a unified diff patch (machine-applicable format)
- Optional “human in the loop”: pushing/PR creation is disabled by default (`AUTO_PUSH=false`)

Practical limitations:
- LLM outputs can be wrong or incomplete (hallucinated code, missing edge cases)
- Repository context is heuristic (reads README/configs and samples; may miss deeper architecture)
- Applying patches requires the target repo to exist locally and be in a clean/applicable state
- GitHub project/board APIs can vary by org/repo and may fail due to permissions or API differences

### Why multi-agent (academic/engineering motivation)
The project demonstrates that splitting responsibilities across agents (PM, Architect, Developer, Reviewer) can:
- Reduce ambiguity (requirements step)
- Improve implementation quality (planning + review)
- Make the workflow auditable (each stage produces an artifact)

### Suggested professor evaluation criteria (optional)
- Correctness of produced patches on a sample repo/issue
- Reproducibility of runs (documented setup + deterministic outputs as much as possible)
- Quality of generated plans and review notes
- Safety controls (PR creation default off, review stage, patch-only outputs)

