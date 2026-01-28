# Robust Structured Changes + Completion Gating

## Overview

The CrewAI pipeline has been upgraded to:
1. **Robust structured change application** - No more brittle exact string matching
2. **Completion gating** - Prevents partial implementations from being marked Done
3. **Automatic retry** - Up to 2 retry passes with missing items checklist
4. **Deterministic patch generation** - Always via `git diff`

## New Structured Change Operations

### Supported Operations

1. **`replace_file`** or **`replace`**
   - Replace entire file content
   - Requires: `content` (full file)

2. **`create`**
   - Create new file
   - Requires: `content` (full file)

3. **`upsert_function_js`** ⭐ NEW
   - Upsert JavaScript function (replace if exists, append if not)
   - Requires: `function_name`, `content` (full function definition)
   - Example:
   ```json
   {
     "path": "app.js",
     "operation": "upsert_function_js",
     "function_name": "openEditModal",
     "content": "function openEditModal(sessionId) { ... }"
   }
   ```

4. **`upsert_css_selector`** ⭐ NEW
   - Upsert CSS selector (replace if exists, append if not)
   - Requires: `selector` (e.g., ".modal"), `content` (full CSS block)
   - Example:
   ```json
   {
     "path": "styles.css",
     "operation": "upsert_css_selector",
     "selector": ".modal",
     "content": ".modal { display: none; ... }"
   }
   ```

5. **`insert_after_anchor`** ⭐ NEW
   - Insert content after anchor string/regex
   - Requires: `anchor`, `content`, optional `use_regex` (default: false)

6. **`insert_before_anchor`** ⭐ NEW
   - Insert content before anchor string/regex
   - Requires: `anchor`, `content`, optional `use_regex` (default: false)

7. **`append_if_missing`** ⭐ NEW
   - Append content only if signature not present
   - Requires: `content`, `signature` (substring to check)

8. **`edit`** (improved)
   - Targeted edits with regex fallback
   - Requires: `edits` array with find/replace pairs
   - Falls back to regex if exact match fails

9. **`delete`**
   - Delete file

## Coverage Checking

### What Gets Checked

1. **Required Functions** (from plan's "New Functions" section)
   - Checks if function names exist in JS files (app.js, index.js, main.js)
   - Supports: `function name()`, `const name =`, `let name =`, `var name =`

2. **Required CSS Selectors** (from plan's "styles.css" mentions)
   - Checks if selectors exist in styles.css
   - Supports: `.class`, `#id`, `element`

3. **Required Test Files** (from plan's "Test Approach" section)
   - Checks if test files exist (test/*.js, test/*.ts, test/*.py)

4. **Required Files** (from plan's "Files to Change" section)
   - Checks if all mentioned files exist

### Coverage Check Flow

```
Apply Changes → Git Status Check → Coverage Check
  ↓
If Complete:
  ✅ Generate patch via git diff
  ✅ Commit changes
  ✅ Move issue to Done
  
If Incomplete:
  ❌ Show missing items checklist
  🔄 Retry (up to 2 more attempts)
  ⚠️  Do NOT commit
  ⚠️  Do NOT move to Done
```

## Retry Mechanism

### Automatic Retry

If coverage check fails:
1. Extract missing items checklist
2. Create retry task with missing items
3. Re-run developer agent with missing items context
4. Re-apply changes
5. Re-check coverage
6. Repeat up to 2 additional times (3 total attempts)

### Retry Task Format

```
Previous implementation attempt was incomplete. Please implement the missing items:

- Missing functions: openEditModal, calculateDuration, validateTimes
- Missing CSS selectors: .modal, .modal-content, .toast
- Missing test files: test/app.test.js

Use the same structured JSON format with appropriate operations...
```

## Completion Gating

### Status Values

- **`complete`**: All requirements met, patch generated, ready for commit
- **`incomplete`**: Missing items, no patch generated, not ready for commit

### Gating Rules

1. **Patch Generation**: Only if `status == "complete"` AND git shows changes
2. **Commit**: Only if `status == "complete"`
3. **Move to Done**: Only if `status == "complete"`
4. **GitHub Operations**: Only if `status == "complete"`

### Output Contract

```python
{
    "status": "complete" | "incomplete",
    "files_changed": ["app.js", "styles.css"],
    "git_changed_files": ["app.js", "styles.css"],
    "patch_path": "/path/to/crewai_patch.diff" | None,
    "missing_items": {
        "functions": ["openEditModal"],
        "css_selectors": [".modal"],
        "test_files": ["test/app.test.js"],
        "required_files": []
    },
    "patch_content": "diff --git ..." | None
}
```

## Flow Ordering

### Correct Flow

1. **Create/switch branch** (if git repo)
2. **Apply structured changes** (robust operations)
3. **Verify with git status** (check actual changes)
4. **Coverage check** (verify plan requirements)
5. **If complete:**
   - Generate patch via `git diff --no-color --minimal`
   - Commit changes
   - Generate patch file
6. **If incomplete:**
   - Show missing items
   - Retry (if attempts remaining)
   - Do NOT commit
   - Do NOT move to Done
7. **GitHub operations** (only if complete)
   - Push branch (if enabled)
   - Move issue to Done (if enabled)

## Example: Issue #529

### Before (Partial Implementation)

- ✅ HTML modal added to index.html
- ❌ JavaScript functions missing (openEditModal, calculateDuration, etc.)
- ❌ CSS styles missing (.modal, .toast)
- ❌ Test file missing
- ⚠️  Issue marked Done anyway

### After (With Completion Gating)

- ✅ HTML modal added
- ❌ Coverage check fails (missing functions, CSS, tests)
- ⚠️  Status: `incomplete`
- 🔄 Retry pass 1: Agent adds missing functions
- ✅ Coverage check passes
- ✅ Patch generated via git diff
- ✅ Issue moved to Done

## Files Modified

1. **`automated_crew.py`**
   - `apply_structured_changes()` - Robust operations with fallbacks
   - `check_coverage()` - Coverage checker
   - `parse_plan_requirements()` - Plan parser
   - `get_git_changed_files()` - Git status checker
   - `apply_implementation()` - Returns status dict
   - Retry mechanism in main flow
   - Completion gating in commit/Done logic

## Testing

### Unit Tests Needed

1. **`upsert_function_js()`**
   - Test function replacement
   - Test function appending
   - Test various function formats

2. **`upsert_css_selector()`**
   - Test selector replacement
   - Test selector appending
   - Test various selector formats

3. **`check_coverage()`**
   - Test function detection
   - Test CSS selector detection
   - Test test file detection

## Verification

To verify the fixes work:

```bash
# Run on issue #529
cd /home/hempfinder/ai-dev-team
python scripts/automated_crew.py --issue 529

# Check output:
# - Should show coverage check
# - Should show missing items if incomplete
# - Should retry if incomplete
# - Should NOT move to Done if incomplete
# - Should generate patch only if complete
```

## Benefits

1. **No More Partial Implementations**: Coverage check prevents incomplete work
2. **Robust Change Application**: Multiple operation types with fallbacks
3. **Automatic Recovery**: Retry mechanism fixes missing items
4. **Deterministic Patches**: Always generated by git diff
5. **Clear Status**: Always know if implementation is complete
