# Running the Automated Crew on a Single Issue

## Command

```bash
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 529 --openai
```

## How the Script Parses This

| Argument | Meaning |
|----------|---------|
| `NeotronProductions/Beautiful-Timetracker-App` | Repository (owner/repo) |
| `1` | `max_issues=1` (process only one issue) |
| `529` | Process **issue #529** only |
| `--openai` | Force use of **OpenAI** (skip Ollama); sets `FORCE_OPENAI=true` |

So the script calls:

`run_automated_crew("NeotronProductions/Beautiful-Timetracker-App", max_issues=1, issue_number=529)` with OpenAI forced.

---

## What Happens When You Run It

### 1. Setup

- **Working directory:** `WORK_DIR` (default: `~/dev/Beautiful-Timetracker-App`)
- GitHub client is created using `GITHUB_TOKEN`; repository existence is verified

### 2. Fetch Issue #529

- Fetches issue **#529** from `NeotronProductions/Beautiful-Timetracker-App`
- If the issue does not exist or is not accessible, the script prints an error and exits

### 3. Process That Single Issue

- **Requirements extraction:** `extract_requirements(issue.body, issue.title)` parses the issue for acceptance criteria and Definition of Done (and similar sections)
- **Crew execution:** Product Manager → Architect → Developer → Reviewer, with the extracted requirement list injected into every task (user story + DoD, AC/DoD mapping, "must satisfy each requirement," and review for requirement coverage)
- **Output:** One implementation plan plus structured changes (and possibly review comments)

### 4. Apply Implementation

- Plan is written to:  
  **`~/dev/Beautiful-Timetracker-App/implementations/issue_529_plan.md`**
- Structured changes are applied under `WORK_DIR`; branch safety ensures a feature branch (e.g. `feature/issue-529`)
- **Coverage check:** Structural check (functions, CSS, tests, files mentioned in the plan)
- **Requirements check:** If any extracted requirement is not satisfied in the plan text, the run is marked incomplete and `missing["unsatisfied_requirements"]` is set

### 5. Retries (if incomplete)

- Up to **2 retries** with "missing items" (including "Unsatisfied requirements") so the developer agent can add the missing implementation

### 6. If Complete

- Patch is generated (`crewai_patch.diff` in the work directory), changes are committed on the feature branch, and optionally (if env is set) the script pushes, creates a PR, and moves the issue on the project board (e.g. to "Done")

### 7. LLM Used

- All agents use **OpenAI** because of the `--openai` flag (Ollama is not used)

---

## Summary

You run the crew on **one issue (#529)** in `NeotronProductions/Beautiful-Timetracker-App`, using **OpenAI**, with requirement extraction and semantic checks. The main artifact you can use for implementation is:

- **`~/dev/Beautiful-Timetracker-App/implementations/issue_529_plan.md`**
- Optionally a copy under **`~/ai-dev-team/exports/issue_529_plan.md`** if that directory exists

---

## Prerequisites

- **`GITHUB_TOKEN`** in `.env` (or in the environment)
- **`OPENAI_API_KEY`** set (required when using `--openai`)
- Repository **`NeotronProductions/Beautiful-Timetracker-App`** cloned at **`~/dev/Beautiful-Timetracker-App`** (or `WORK_DIR` overridden)
