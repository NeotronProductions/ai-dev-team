# Automatic Preview Integration

## Overview

The preview script (`preview_implementation.py`) is **fully integrated** into `automated_crew.py` and runs automatically after every issue is processed.

## How It Works

### Automatic Execution

After CrewAI processes an issue, the workflow is:

1. **Code Generation** → CrewAI generates implementation
2. **Patch Application** → System tries to apply patch automatically
3. **Status Report** → Shows local vs Git/GitHub status
4. **Preview Script** → **Automatically runs** to show changes and start server

### Integration Points

The preview script is called in two places:

1. **Single Issue Processing** (line ~1979):
   ```python
   print_issue_status(issue.number, work_dir, warnings)
   run_preview_script(issue.number, work_dir)  # ← Automatic
   ```

2. **Batch Processing** (line ~2113):
   ```python
   print_issue_status(issue.number, work_dir, warnings)
   run_preview_script(issue.number, work_dir)  # ← Automatic
   ```

## What Happens Automatically

When you run `automated_crew.py`, after each issue:

1. ✅ **Patch Application** - Tries to apply the patch automatically
2. ✅ **Diff Preview** - Shows what changed (up to 100 lines)
3. ✅ **File List** - Lists all modified files
4. ✅ **Git Status** - Shows branch, commit, push status
5. ✅ **Server Startup** - Starts local server automatically
6. ✅ **Testing Instructions** - Shows how to test

## Configuration

### Run in Foreground (Default)

By default, the preview runs in **foreground** to show all output:

```bash
python ~/ai-dev-team/scripts/automated_crew.py
```

You'll see:
- Status report
- Preview output
- Diff preview
- Server startup

### Run in Background

To run preview in background (non-blocking):

```bash
export PREVIEW_IN_BACKGROUND=true
python ~/ai-dev-team/scripts/automated_crew.py
```

This will:
- Start preview script in background
- Continue processing without waiting
- Show a message with manual command

## Example Output Flow

```
======================================================================
📦 LOCAL IMPLEMENTATION & TESTING - Issue #707
======================================================================
✅ Code changes applied successfully to local files
...

======================================================================
🔀 GIT & GITHUB OPERATIONS - Issue #707
======================================================================
✅ Branch: feature/issue-707
...

======================================================================
🔍 Running preview script to show changes and start server...
======================================================================

======================================================================
🔍 PREVIEW: Issue #707 Implementation
======================================================================

📦 PATCH STATUS
----------------------------------------------------------------------
✅ Patch file found: ...
✅ Applied using whitespace fix

📝 CHANGED FILES
----------------------------------------------------------------------
✅ 3 file(s) modified:
   - index.html
   - app.js
   - styles.css

🔍 DIFF PREVIEW
----------------------------------------------------------------------
[Shows actual diff of changes]

🧪 TESTING
----------------------------------------------------------------------
🚀 Starting preview server...
   ✅ Server starting in background
   📍 Preview at: http://localhost:9000
```

## Error Handling

The preview script is designed to **never break** the main workflow:

- ✅ If preview script fails → Shows warning, continues
- ✅ If preview script times out → Shows warning, continues
- ✅ If preview script not found → Silently skips
- ✅ If Python not found → Shows warning, continues

All errors are **non-critical** - the main issue processing always completes.

## Manual Override

Even though it runs automatically, you can still run it manually:

```bash
# Preview latest issue
python ~/ai-dev-team/scripts/preview_implementation.py

# Preview specific issue
python ~/ai-dev-team/scripts/preview_implementation.py 707
```

## Benefits

### ✅ Zero Manual Steps
- No need to manually run preview
- No need to manually start server
- Everything happens automatically

### ✅ Immediate Feedback
- See changes right after generation
- Test immediately in browser
- No waiting or manual steps

### ✅ Comprehensive View
- See all changes at once
- Understand what was modified
- Get testing instructions

### ✅ Non-Blocking
- Can run in background if needed
- Never blocks main workflow
- Always completes successfully

## Summary

**Before**: Manual steps after code generation
1. Check patch file
2. Apply patch manually
3. Review changes
4. Start server manually
5. Test in browser

**After**: Fully automatic
1. Code generated ✅
2. Patch applied ✅
3. Preview shown ✅
4. Server started ✅
5. Ready to test ✅

The preview is now **fully integrated** and runs automatically! 🎉
