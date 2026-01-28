# Processing User Stories with Sub-Tasks

Guide for processing user stories (like US-001) that have multiple sub-tasks.

## Understanding US-001 Structure

From your GitHub Projects board:

**Main User Story:**
- **US-001: Create New Project #550** ✅ (Marked as Done)

**Sub-Tasks (Still Todo):**
- #551: Create project input form component (US-001-T1)
- #552: Add validation for project name (US-001-T2)
- #553: Implement color assignment logic (US-001-T3)
- #554: Add project to state management (US-001-T4)
- #555: Write unit tests (US-001-T5)

## How the Crew Handles Sub-Issues

The crew has **two strategies** for handling sub-issues:

### Strategy 1: "include" (Default)

When you process issue #550, the crew will:
1. **Detect** all sub-issues (#551-555)
2. **Include** their descriptions in the parent issue context
3. **Generate** a single implementation that addresses all sub-tasks
4. **Create** one unified diff/implementation

**Command:**
```bash
python3 scripts/automated_crew.py owner/repo 1 550
```

**Result:**
- One implementation plan covering all sub-tasks
- One git branch/commit
- One PR (if enabled)

### Strategy 2: "sequential"

Processes each sub-issue separately after the parent:

1. Process parent issue #550
2. Then process #551
3. Then process #552
4. And so on...

**To enable:**
```bash
export SUB_ISSUE_STRATEGY=sequential
python3 scripts/automated_crew.py owner/repo 1 550
```

**Result:**
- Multiple implementation plans (one per sub-issue)
- Multiple git branches/commits
- Multiple PRs (if enabled)

## Will You Have a Runnable Project?

### Current Status

- **US-001 (#550)** is marked "Done" but has incomplete sub-tasks
- **5 sub-tasks** are still "Todo" (green circles)
- These sub-tasks are **critical components**:
  - Form component (#551)
  - Validation (#552)
  - Color logic (#553)
  - State management (#554)
  - Unit tests (#555)

### After Processing US-001

**If using "include" strategy (default):**
- ✅ The crew will **attempt** to implement all sub-tasks in one go
- ✅ You'll get a **complete implementation** covering all components
- ⚠️ **Quality depends on:**
  - How well the crew understands the requirements
  - Whether the diff is complete and correct
  - Whether the patch applies successfully

**If using "sequential" strategy:**
- ✅ Each sub-task gets individual attention
- ✅ More granular control and review
- ⚠️ **Requires:**
  - Processing parent first, then each sub-task
  - More time and API calls
  - Managing multiple branches/PRs

### What "Runnable" Means

A **runnable project** means:
- ✅ Code compiles/runs without errors
- ✅ All components are implemented
- ✅ Features work as expected
- ✅ No critical missing pieces

**After processing US-001, you should have:**
- ✅ Project creation form
- ✅ Input validation
- ✅ Color assignment
- ✅ State management integration
- ⚠️ Unit tests (may need manual verification)

## Recommended Approach for US-001

### Option 1: Process Parent with Sub-Issues Included (Recommended)

```bash
cd ~/ai-dev-team
source .venv/bin/activate

# Process US-001 with all sub-tasks included
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 550
```

**What happens:**
1. Crew detects sub-issues #551-555
2. Includes them in the implementation context
3. Generates comprehensive solution
4. Applies all changes in one diff

**Check result:**
```bash
cd ~/dev/Beautiful-Timetracker-App
git status
git diff
```

### Option 2: Process Each Sub-Task Sequentially

```bash
# Set sequential strategy
export SUB_ISSUE_STRATEGY=sequential

# Process parent (will then process all sub-tasks)
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 550
```

**What happens:**
1. Process #550 (parent)
2. Process #551 (form component)
3. Process #552 (validation)
4. Process #553 (color logic)
5. Process #554 (state management)
6. Process #555 (unit tests)

### Option 3: Process Sub-Tasks Individually

```bash
# Process each sub-task separately
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 551
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 552
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 553
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 554
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 555
```

## Verifying Runnable Project

After processing, check:

### 1. Check Implementation Files

```bash
# View the implementation plan
cat ~/dev/Beautiful-Timetracker-App/implementations/issue_550_plan.md

# Check if diff was extracted
grep -A 20 "Extracted Patch" ~/dev/Beautiful-Timetracker-App/implementations/issue_550_plan.md
```

### 2. Check Git Changes

```bash
cd ~/dev/Beautiful-Timetracker-App
git status
git diff
```

### 3. Check Code Files

```bash
# Look for new/modified files
find ~/dev/Beautiful-Timetracker-App -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | xargs ls -lt | head -10

# Check if form component exists
ls -la ~/dev/Beautiful-Timetracker-App/src/components/ 2>/dev/null || echo "Components directory not found"
```

### 4. Test the Application

```bash
cd ~/dev/Beautiful-Timetracker-App

# If it's a web app, start a server
python3 -m http.server 8080

# Or if it has a package.json
npm install
npm start
```

### 5. Check for Missing Pieces

Look for:
- ✅ Form component file created
- ✅ Validation logic implemented
- ✅ State management updated
- ✅ Color assignment logic added
- ⚠️ Unit tests (may need manual verification)

## Troubleshooting

### Sub-Issues Not Detected

If sub-issues aren't found:

1. **Check GitHub API:**
   - Sub-issues API may require GitHub Enterprise
   - Fallback uses issue body references (#551, #552, etc.)

2. **Verify Issue #550 Body:**
   - Should contain references like "#551", "#552", etc.
   - Or use GitHub's sub-issue feature

3. **Manual Processing:**
   - Process sub-tasks individually if needed

### Incomplete Implementation

If the implementation is incomplete:

1. **Check Output File:**
   ```bash
   cat ~/dev/Beautiful-Timetracker-App/implementations/issue_550_plan.md
   ```

2. **Check Diff:**
   ```bash
   cat ~/dev/Beautiful-Timetracker-App/crewai_patch.diff
   ```

3. **Reprocess:**
   ```bash
   python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 550
   ```

### Patch Won't Apply

If `git apply` fails:

1. **Check for conflicts:**
   ```bash
   cd ~/dev/Beautiful-Timetracker-App
   git apply --check crewai_patch.diff
   ```

2. **Apply manually:**
   - Review the diff
   - Apply changes manually
   - Or fix conflicts and reapply

## Best Practices

### For User Stories with Sub-Tasks

1. **Use "include" strategy** for cohesive implementation
2. **Review the output** before applying
3. **Test incrementally** - don't assume everything works
4. **Process sub-tasks individually** if parent implementation is incomplete

### For Production Readiness

1. **Run tests** after implementation
2. **Review code quality** (the crew includes a reviewer agent)
3. **Check for edge cases** (validation, error handling)
4. **Verify integration** (state management, component connections)

## Summary

**Will you have a runnable project after processing US-001?**

**Most likely: YES**, if:
- ✅ The crew successfully generates a complete diff
- ✅ The diff includes all sub-task implementations
- ✅ The patch applies without conflicts
- ✅ All components are properly integrated

**But you should:**
- ⚠️ **Test** the implementation
- ⚠️ **Verify** all sub-tasks are addressed
- ⚠️ **Check** for missing pieces
- ⚠️ **Review** the code quality

**Recommended command for US-001:**
```bash
python3 scripts/automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 550
```

This will process US-001 with all sub-tasks included, giving you the best chance of a complete, runnable implementation.

---

**Related Documentation:**
- [TERMINAL_COMMANDS.md](TERMINAL_COMMANDS.md) - How to run the crew
- [DIFF_AND_PR_WORKFLOW.md](DIFF_AND_PR_WORKFLOW.md) - How code changes are applied
- [PROCESSED_ISSUES.md](PROCESSED_ISSUES.md) - Skip vs override behavior

---

**Last Updated:** January 2025
