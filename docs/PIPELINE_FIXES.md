# CrewAI Pipeline Fixes - Contradictions and Backend Hallucinations

## Summary

Fixed contradictions in logging, reduced backend hallucinations, and improved retry guidance in the CrewAI automation pipeline.

## Problems Fixed

### 1. Backend/API Hallucinations
**Problem**: Agent outputs backend/API paths (models/, routes/, controllers/) and omits required fields like function_name.

**Solution (A)**: Made agent prompting strongly repo-scoped:
- Injected repo type: "static frontend web app; no backend; no Node/Express/Mongoose"
- Injected allowed paths list (top 20 existing files)
- Hard requirements: every change must include "path" and "operation"; upsert_function_js MUST include function_name
- Forbidden paths: api/, routes/, controllers/, models/, backend/, server/
- On retry: includes validator error messages verbatim and restates allowlist

**Files Modified**:
- `scripts/automated_crew.py` lines ~760-844 (developer_task description)
- `scripts/automated_crew.py` lines ~4014-4028 (retry task description - first occurrence)
- `scripts/automated_crew.py` lines ~4362-4376 (retry task description - second occurrence)

### 2. Missing Items Empty Dict
**Problem**: "Missing items: {}" appears after validation failures, making retries useless.

**Solution (B)**: Fixed missing_items handling:
- Initialize missing_items early with validation_errors field
- When validation fails: set `_failure_reason: "validation_failed"` and `_failure_summary`
- When apply fails: track errors in `apply_errors` field
- When parse fails: set `_failure_reason: "parse_failed"`
- Never show empty dict - always show failure reason or actual missing items

**Files Modified**:
- `scripts/automated_crew.py` lines ~2655-2680 (missing_items initialization and validation failure handling)
- `scripts/automated_crew.py` lines ~2685-2695 (apply error tracking)
- `scripts/automated_crew.py` lines ~2811-2818 (parse failure handling)
- `scripts/automated_crew.py` lines ~4168-4171, 4245-4247, 4397-4400, 4474-4476 (missing_items display logic)

### 3. Success Messaging Contradictions
**Problem**: Main flow correctly blocks commit/push when incomplete, but later "LOCAL IMPLEMENTATION & TESTING" claims "Code changes applied successfully" even when run was incomplete.

**Solution (C)**: Fixed success messaging and gating consistency:
- Only print "✅ Code changes applied successfully" if:
  - `apply_structured_changes` returned success AND changed_files
  - AND git status shows changes
- Do NOT proceed to test execution if validation failed OR no changes applied
- Use implementation_status flags to determine patch_applied truthfully
- Show failure reasons in status output

**Files Modified**:
- `scripts/automated_crew.py` lines ~2836-2839 (patch_applied computation using implementation_status)
- `scripts/automated_crew.py` lines ~2909-2916 (success message gating)
- `scripts/automated_crew.py` lines ~3022-3035 (test execution gating)
- `scripts/automated_crew.py` lines ~3005-3009 (summary status)
- `scripts/automated_crew.py` lines ~2783-2784 (test execution only if changes applied)

### 4. Preview Reporting Inaccuracies
**Problem**: Preview shows diffs from working tree but also claims commit/push status incorrectly.

**Solution (D)**: Fixed preview reporting (truthful commit/push status):
- Compute current branch: `get_current_branch(work_dir)` (from git_ops)
- Committed? Check `implementation_status.get("did_commit", False)` (run state flag)
- Pushed? Check `implementation_status.get("did_push", False)` (run state flag)
- If working tree has uncommitted changes, show "Uncommitted changes: ✅"
- Do NOT print "Committed ✅ / Pushed ✅" based on assumptions

**Files Modified**:
- `scripts/automated_crew.py` lines ~2968-2993 (git status reporting using run state flags)
- `scripts/automated_crew.py` lines ~2836-2839 (patch_applied computation)

### 5. Accidental Development Branch Edits
**Problem**: Changes could be applied to development branch unintentionally.

**Solution (E)**: Added safeguard to prevent applying changes to development:
- Before applying changes, check if on protected branch (development, main, master)
- If on protected branch, create/switch to feature branch BEFORE applying changes
- If branch checkout fails, abort with error (no file writes)
- Feature branch name: `feature/issue-{issue_number}`

**Files Modified**:
- `scripts/automated_crew.py` lines ~2649-2705 (branch safeguard before applying changes)

## Key Changes

### A) Repo-Scoped Prompting
```python
# Get repo file allowlist
repo_files = get_repo_file_allowlist(work_dir)
allowed_paths_list = sorted([f for f in repo_files if not f.startswith('test')])[:20]

# Inject into developer task description:
- REPO TYPE: static frontend web app; NO backend
- ALLOWED PATHS: [list of existing files]
- FORBIDDEN: api/, routes/, controllers/, models/
- HARD REQUIREMENTS: path, operation, function_name (for upsert_function_js)
```

### B) Missing Items Structure
```python
missing = {
    "functions": [],
    "css_selectors": [],
    "test_files": [],
    "required_files": [],
    "validation_errors": [],  # NEW
    "_failure_reason": "validation_failed",  # NEW
    "_failure_summary": "Validation failed with 3 error(s). Changes not applied."  # NEW
}
```

### C) Success Gating
```python
# Only show success if:
patch_applied = bool(
    files_changed and 
    git_changed_files and 
    implementation_status.get("coverage_passed", False)
)
```

### D) Truthful Status Reporting
```python
# Use run state flags, not assumptions
git_committed = implementation_status.get("did_commit", False)
git_pushed = implementation_status.get("did_push", False)
has_uncommitted = has_changes(work_dir)
```

### E) Branch Safeguard
```python
# Before applying changes:
if current_branch in ['development', 'main', 'master']:
    # Create/switch to feature branch
    # If fails, abort (return early with error)
```

## Testing

To verify fixes:
1. Run on an issue and check that:
   - Agent doesn't output backend paths
   - Validation failures show meaningful missing_items (not {})
   - Success messages only appear when changes actually applied
   - Commit/push status is truthful (uses run state flags)
   - Branch safeguard prevents edits to development

2. Check logs for consistency:
   - No "Code changes applied successfully" when validation failed
   - No "Committed ✅" when did_commit=False
   - No "Missing items: {}" after failures

## Files Changed

- `scripts/automated_crew.py` - All fixes implemented
- `docs/PIPELINE_FIXES.md` - This documentation

## Backward Compatibility

✅ All changes maintain backward compatibility:
- Same function signatures
- Same return types
- Same CLI interface
- Existing behavior preserved (just more accurate reporting)
