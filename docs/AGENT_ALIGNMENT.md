# CrewAI Agent Alignment

## ✅ Agents Now Aligned with run_autopr.py Structure

The `automated_crew.py` has been updated to match the agent structure from your reference script.

### Agent Roles (Aligned)

1. **Product Manager** (was "Issue Analyst")
   - Goal: Convert issue into user story + acceptance criteria
   - Backstory: Expert agile PM who clarifies scope and defines Done
   - Output: User story, acceptance criteria, out of scope, risks

2. **Software Architect** (was "Code Implementer")
   - Goal: Create minimal technical plan and identify files to change
   - Backstory: Favors small diffs, maintainability, testability
   - Output: Implementation plan, files to change, test approach

3. **Developer** (new - produces actual patches)
   - Goal: Produce single unified diff patch implementing the issue
   - Backstory: Writes production-grade code with tests
   - Output: Unified diff patch in ```diff fenced block

4. **Code Reviewer** (aligned)
   - Goal: Catch bugs/security issues; ensure edge cases and quality
   - Backstory: Strict but practical; requests changes if needed
   - Output: Review feedback on correctness, security, edge cases

### Workflow Alignment

**Before:**
```
Analyst → Implementer → Reviewer
```

**Now (Aligned):**
```
Product Manager → Architect → Developer → Reviewer
     ↓              ↓            ↓           ↓
  User Story    Tech Plan    Diff Patch   Review
```

### Key Improvements

1. **Unified Diff Output**: Developer agent now produces actual git patches
2. **Patch Extraction**: Added `extract_diff()` function to parse crew output
3. **Patch Application**: Added `apply_patch()` to apply diffs to repo
4. **Ollama Configuration**: Aligned with run_autopr.py (OLLAMA_BASE_URL, OLLAMA_MODEL)
5. **Task Descriptions**: Match the reference script exactly

### Configuration Alignment

The script now uses the same environment variables:
- `OLLAMA_BASE_URL` (default: http://localhost:11434)
- `OLLAMA_MODEL` (default: qwen2.5-coder:3b)
- `GITHUB_TOKEN`
- `GITHUB_REPO`

### Next Steps

The agents are now aligned! The crew will:
1. Product Manager creates user story
2. Architect creates technical plan
3. Developer produces unified diff patch
4. Reviewer checks quality
5. System extracts and applies patch (if in git repo)

This matches the workflow from your reference script.
