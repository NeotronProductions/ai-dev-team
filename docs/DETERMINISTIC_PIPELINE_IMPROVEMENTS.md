# Deterministic Pipeline Improvements

This document describes the improvements made to `ai-dev-crew` to ensure issues get implemented correctly with deterministic, enforceable gates.

## Overview

The improvements transform `ai-dev-crew` from a "hopeful" pipeline into a **deterministic pipeline** that:
1. Loads the *right* repo files with verification
2. Forces output that is directly applicable (no placeholders/stubs)
3. Blocks completion if requirements aren't satisfied

---

## 1. Canonical Work Directory + Context Manifest

### What Changed

- **`get_project_context()` → `get_project_context_bundle()`**
  - Returns `(context_text, manifest_entries, fatal_errors)`
  - **Aborts early** if canonical UI files (`index.html`, `app.js`, `styles.css`) are missing or empty

### Implementation

- **Canonical files are always included**:
  - `index.html`: Full content
  - `app.js`: First 220 lines + keyword snippets (session/edit/modal/duration/toast/undo)
  - `styles.css`: First 260 lines + keyword snippets (modal/toast/dialog/session/button)

- **Context manifest** lists every file loaded with:
  - Path, required flag, character count, byte count, empty flag

- **Fatal errors** block execution before CrewAI runs if:
  - Any canonical file is missing
  - Any canonical file is empty

### Code Location

- `scripts/automated_crew.py`: `get_project_context_bundle()` (line ~550)
- `scripts/automated_crew.py`: `CANONICAL_UI_FILES` constant (line ~550)
- `scripts/automated_crew.py`: Context gate check in `process_issue()` (line ~729)

---

## 2. Explicit Canonical File Paths in Prompts

### What Changed

- **Architect task** explicitly states canonical files are source of truth
- **Developer task** includes canonical files in constraints
- **File allowlist** prioritizes canonical files first

### Implementation

- Architect prompt: "CANONICAL SOURCE OF TRUTH: The canonical UI files are `index.html`, `app.js`, `styles.css` in the repo root"
- Developer prompt: "CANONICAL UI FILES: `index.html`, `app.js`, `styles.css` in work_dir are the source of truth"
- Allowlist building: canonical paths prepended to allowed_paths_list

### Code Location

- `scripts/automated_crew.py`: Architect task (line ~780)
- `scripts/automated_crew.py`: Developer task (line ~827)
- `scripts/automated_crew.py`: Allowlist building (line ~805)

---

## 3. Context Auditor Agent

### What Changed

- **New agent**: "Context Auditor" runs before Architect/Developer
- **Must cite exact identifiers** from loaded context
- **Aborts if required elements missing**

### Implementation

- Auditor task outputs JSON with:
  - `canonical_files_present`: boolean flags per file
  - `dom_ids`, `dom_classes_or_attrs`, `css_selectors`, `js_functions_or_anchors`: arrays
  - `evidence`: array of file quotes proving each identifier exists
  - `missing`: array of what couldn't be found

- **Gate**: If `missing` is non-empty, `apply_implementation()` aborts before applying changes

### Code Location

- `scripts/automated_crew.py`: `create_implementation_crew()` - auditor agent (line ~530)
- `scripts/automated_crew.py`: `auditor_task` definition (line ~779)
- `scripts/automated_crew.py`: `parse_context_audit()` (line ~1096)
- `scripts/automated_crew.py`: Context audit gate in `apply_implementation()` (line ~2864)

---

## 4. Deterministic Validators (Placeholder/TODO/Stub Rejection)

### What Changed

- **Forbidden substring detection** in structured changes validation
- **Post-apply content scan** for forbidden text
- **Blocks completion** if placeholders/stubs detected

### Implementation

- **Forbidden patterns**:
  - Placeholders: "todo", "placeholder", "logic to ", "tbd", "replace_me", "fill in"
  - New deps: "moment(", "import moment", "require('moment"

- **Validation points**:
  1. During `validate_structured_changes()`: checks content fields before applying
  2. After applying changes: scans all changed files for forbidden text

- **Failure behavior**: Sets `is_complete = False`, adds to `missing["validation_errors"]`

### Code Location

- `scripts/automated_crew.py`: `_FORBIDDEN_PLACEHOLDER_SUBSTRINGS`, `_FORBIDDEN_NEW_DEP_SUBSTRINGS` (line ~1124)
- `scripts/automated_crew.py`: `_find_forbidden_substrings()` (line ~1135)
- `scripts/automated_crew.py`: Validation in `validate_structured_changes()` (line ~1207)
- `scripts/automated_crew.py`: Post-apply scan (line ~2905)

---

## 5. Reviewer as Enforceable Gate

### What Changed

- **Reviewer outputs structured JSON** (not freeform text)
- **Gate format**: `{"pass": bool, "failed_requirements": [...], "failed_integration_checks": [...], "notes": "..."}`
- **Blocks completion** if `pass=false`

### Implementation

- Reviewer task explicitly requests JSON output with pass/fail + failure lists
- `parse_review_gate()` extracts the JSON from crew output
- **Gate**: If `pass=false`, `apply_implementation()` aborts before applying changes
- Failed requirements/integration checks added to `missing_items` for retry

### Code Location

- `scripts/automated_crew.py`: `review_task` definition (line ~974)
- `scripts/automated_crew.py`: `parse_review_gate()` (line ~1106)
- `scripts/automated_crew.py`: Review gate check in `apply_implementation()` (line ~2900)

---

## 6. Requirements as Contracts

### What Changed

- **Requirements extracted** from issue body (AC/DoD sections)
- **Injected into every task** (PM, Architect, Developer, Reviewer)
- **Semantic check** after coverage: plan must satisfy all requirements

### Implementation

- `extract_requirements()` parses issue body for:
  - `## Acceptance criteria`, `## Definition of Done`, `## Requirements`, etc.
  - Bullets under those sections
  - Fallback: first 15 bullets if no structured sections

- **Semantic validation**: `check_requirements_satisfied()` uses keyword overlap
- **Gate**: If any requirement unsatisfied, `is_complete = False`, added to `missing["unsatisfied_requirements"]`

### Code Location

- `crew_runner/issue_requirements.py`: `extract_requirements()`, `check_requirements_satisfied()`
- `scripts/automated_crew.py`: Requirements extraction in `process_issue()` (line ~753)
- `scripts/automated_crew.py`: Requirements check in `apply_implementation()` (line ~2850)

---

## 7. Retry Includes All Failure Types

### What Changed

- **Retry missing_text** includes:
  - Structural: missing functions, CSS, tests, files
  - Semantic: unsatisfied requirements
  - Validation: placeholder/stub errors, context audit failures, review gate failures

### Implementation

- Retry builds `missing_parts` list with all failure types
- Filters empty strings before joining
- Retry task explicitly mentions "Unsatisfied requirements" and "Validation errors"

### Code Location

- `scripts/automated_crew.py`: Retry missing_parts building (line ~4423, ~4659)

---

## Summary: Gates That Block Completion

The pipeline now has **multiple gates** that prevent incomplete implementations from being marked "complete":

1. **Context Gate** (before CrewAI): Required canonical files missing/empty → abort
2. **Context Audit Gate** (after crew, before apply): Auditor couldn't find required IDs → abort
3. **Review Gate** (after crew, before apply): Reviewer marked pass=false → abort
4. **Validation Gate** (during apply): Placeholders/stubs/new deps in structured changes → reject
5. **Post-Apply Gate** (after apply): Placeholders/stubs in written files → mark incomplete
6. **Coverage Gate** (after apply): Missing functions/CSS/tests/files → mark incomplete
7. **Requirements Gate** (after apply): Unsatisfied AC/DoD → mark incomplete

**Only if ALL gates pass** does the run get marked `status="complete"` and proceed to commit/PR/Done.

---

## Testing

To verify these improvements work:

1. **Test context gate**: Remove `index.html` → should abort before crew runs
2. **Test context audit**: Issue requiring IDs not in HTML → should abort before apply
3. **Test review gate**: Reviewer marks pass=false → should abort before apply
4. **Test placeholder rejection**: Developer outputs "TODO" → should reject in validation
5. **Test requirements check**: Issue with AC not satisfied in plan → should mark incomplete

---

## Files Modified

- `scripts/automated_crew.py`: Main pipeline with all gates
- `crew_runner/issue_requirements.py`: Requirement extraction/checking (already existed)
- `crew_runner/git_ops.py`: No changes (branch safety already existed)

---

## Next Steps (Optional Future Enhancements)

- Add project-specific `PROJECT_CONTEXT.md` parsing for extra requirements
- Add LLM-based semantic check (beyond keyword overlap) for requirements
- Add "dry-run" mode that shows what would be blocked without applying
- Add manifest export to plan file for debugging
