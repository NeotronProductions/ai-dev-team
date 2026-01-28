# Diff + PR Workflow (How the Crew “Actualises” Code)

This project’s crew generates **text output**. If that output contains a **unified diff**, the automation can apply it to a real git repo, commit it, and (optionally) open a Pull Request.

This doc explains:
- Where the generated “code” goes
- How diffs work
- How to get the changes into your repo (locally and via PR)
- What to do when you “don’t see any code”

---

## Key idea: the crew outputs text, not files

The crew’s “Developer” step is instructed to output a **unified diff patch** (a block starting with `diff --git ...`).

Only when that diff is **applied** to a git repo do files actually change.

---

## Where the output is saved

For each issue, the script writes a report file in the **target work repo**:

```
~/dev/Beautiful-Timetracker-App/implementations/issue_<ISSUE>_plan.md
```

This report contains:
- **Full Crew Output** (all agent text)
- **Extracted Patch** (if a diff was found in the output)

If `~/ai-dev-team/exports/` exists, it also copies the report there:

```
~/ai-dev-team/exports/issue_<ISSUE>_plan.md
```

---

## How the diff becomes real code

Inside `scripts/automated_crew.py`, the flow is:

1. Run the crew (`crew.kickoff()`).
2. Convert the result to text.
3. Extract a diff from the output (`extract_diff()` looks for either):
   - A fenced block: ` ```diff ... ``` `
   - Or raw diff text starting with: `diff --git`
4. Save the diff to a file in the repo:
   - `crewai_patch.diff`
5. Apply it to the repo:
   - `git apply crewai_patch.diff`
6. If files changed:
   - `git add .`
   - `git commit -m "..."`
7. If enabled, push and open a PR.

---

## “Where does the code go once a PR is made?”

If a PR is created, the code lives:
- On GitHub, in the **PR branch** (example branch name: `feature/issue-528`)

Your local `main` branch will **not** show those changes until you:
- Checkout the PR branch locally, or
- Merge the PR on GitHub and then pull `main`

---

## How to actualise the code in your local repo

### Step 1 — Identify the target repo

This script applies changes to the repo configured as `WORK_DIR`.
Default is:

```
~/dev/Beautiful-Timetracker-App
```

### Step 2 — Run the crew

```bash
cd ~/ai-dev-team
source .venv/bin/activate

# Process a specific issue
python3 scripts/automated_crew.py owner/repo 1 <ISSUE_NUMBER>
```

### Step 3 — Check if files changed

```bash
cd ~/dev/Beautiful-Timetracker-App
git status
git diff
```

If you see modified files, the patch applied successfully.

### Step 4A — Commit locally (manual)

```bash
cd ~/dev/Beautiful-Timetracker-App
git checkout -b feature/issue-<ISSUE_NUMBER>
git add .
git commit -m "feat: implement solution for issue #<ISSUE_NUMBER>"
git push -u origin feature/issue-<ISSUE_NUMBER>
```

### Step 4B — Push + PR automatically (optional)

Set:

```env
AUTO_PUSH=true
```

Then rerun the crew. If push succeeds, the script will create a PR using the GitHub API (requires `GITHUB_TOKEN`).

---

## How to get the PR code locally

If you already have a PR created (branch exists on GitHub), pull the branch:

```bash
cd ~/dev/Beautiful-Timetracker-App
git fetch origin
git switch feature/issue-<ISSUE_NUMBER>
```

If you merged the PR on GitHub and want it in `main`:

```bash
cd ~/dev/Beautiful-Timetracker-App
git switch main
git pull
```

---

## If you “don’t see any code”: what to check

### 1) The crew did not produce a diff
Open the report file:

```bash
less ~/dev/Beautiful-Timetracker-App/implementations/issue_<ISSUE>_plan.md
```

Look for an **“Extracted Patch”** section. If there is no diff, nothing can be applied.

### 2) The patch failed to apply
The script writes the patch file in the repo:

```bash
ls -lh ~/dev/Beautiful-Timetracker-App/crewai_patch.diff
```

Try applying manually to see the exact error:

```bash
cd ~/dev/Beautiful-Timetracker-App
git apply --verbose crewai_patch.diff
```

If there are conflicts, you may need to:
- Rebase your repo / update to latest `main`
- Regenerate a diff against the current code
- Manually patch the files

### 3) You’re looking at the wrong branch
If the PR was created, your changes might be on `feature/issue-<N>`:

```bash
cd ~/dev/Beautiful-Timetracker-App
git branch
git log --oneline -10
```

### 4) The “output file” is tiny / incomplete
If the plan file contains only a short line, the crew likely failed or the model returned junk.
Re-run the issue and watch terminal output for LLM/network errors.

---

## Minimal checklist (fast)

1. Run crew for issue `<N>`
2. Check report: `implementations/issue_<N>_plan.md` (does it contain a diff?)
3. Check repo: `git status` + `git diff`
4. If PR exists: `git fetch origin && git switch feature/issue-<N>`

