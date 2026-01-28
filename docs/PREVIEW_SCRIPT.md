# Preview Implementation Script

## Overview

The `preview_implementation.py` script automatically runs after CrewAI generates code to:
1. **Apply patches** automatically (with multiple fallback strategies)
2. **Show preview** of all changes (diff, changed files, git status)
3. **Start local server** for immediate testing
4. **Display summary** of what was implemented

## Integration

The script is **automatically integrated** into `automated_crew.py` and runs after each issue is processed.

## Usage

### Automatic (Integrated)
The script runs automatically after CrewAI processes an issue. No manual action needed!

### Manual Usage
You can also run it manually to preview any issue:

```bash
# Preview latest processed issue
python ~/ai-dev-team/scripts/preview_implementation.py

# Preview specific issue
python ~/ai-dev-team/scripts/preview_implementation.py 707
```

## What It Does

### 1. Patch Application
- Tries multiple strategies to apply the patch:
  - `git apply --whitespace=fix`
  - `git apply --ignore-whitespace`
  - `git apply --3way`
  - `git apply --unidiff-zero`
- Shows status and manual instructions if auto-apply fails

### 2. Preview Display
Shows comprehensive preview:
- **Patch Status**: Whether patch was applied
- **Implementation Plan**: Location and size
- **Changed Files**: List of modified files
- **Diff Preview**: Actual code changes (limited to 100 lines)
- **Git Status**: Branch, commit, push status
- **Testing Instructions**: Step-by-step commands

### 3. Server Startup
Automatically detects and starts the appropriate server:
- **Node.js**: `npm start` or `node server.js` (port 9000)
- **Python**: `python3 -m http.server 8000`
- Checks if server is already running to avoid conflicts

### 4. Summary
Final summary showing:
- ✅ Patch file generated
- ✅ Implementation plan saved
- ✅ Files modified count
- ✅ Git operations status

## Example Output

```
======================================================================
🔍 PREVIEW: Issue #707 Implementation
======================================================================

📦 PATCH STATUS
----------------------------------------------------------------------
✅ Patch file found: /home/hempfinder/dev/Beautiful-Timetracker-App/crewai_patch.diff
   ✅ Applied using whitespace fix

📄 IMPLEMENTATION PLAN
----------------------------------------------------------------------
✅ Plan file: /home/hempfinder/dev/Beautiful-Timetracker-App/implementations/issue_707_plan.md
   Size: 20,709 bytes

📝 CHANGED FILES
----------------------------------------------------------------------
✅ 3 file(s) modified:
   - index.html
   - app.js
   - styles.css

🔍 DIFF PREVIEW
----------------------------------------------------------------------
 index.html | 5 +++++
 app.js     | 25 +++++++++++++++++++++++++
 styles.css | 6 ++++++
 3 files changed, 36 insertions(+)

diff --git a/index.html b/index.html
index 1234567..89abcde 100644
--- a/index.html
+++ b/index.html
@@ -10,6 +10,10 @@
                </select>
                </div>
                <div class="custom-project">
+                    <span class="project-badge" data-color="#ff6347">Project A</span>
+                    <span class="project-badge" data-color="#4682b4">Project B</span>
+                    <span class="project-badge" data-color="#3cb371">Project C</span>
...

🔀 GIT STATUS
----------------------------------------------------------------------
Branch: feature/issue-707
Committed: ✅
Pushed: ✅
Uncommitted changes: ✅

🧪 TESTING
----------------------------------------------------------------------
To test locally:
  1. cd /home/hempfinder/dev/Beautiful-Timetracker-App
  2. npm start
  3. Open http://localhost:9000 in your browser

🚀 Starting preview server...
   ✅ Server starting in background
   📍 Preview at: http://localhost:9000
   ⚠️  Press Ctrl+C to stop the server

======================================================================
📊 SUMMARY
======================================================================
   ✅ Patch file generated
   ✅ Implementation plan saved
   ✅ 3 file(s) modified
   ✅ Changes committed
   ✅ Branch pushed
```

## Configuration

### Environment Variables

- `PREVIEW_IN_BACKGROUND`: Set to `"true"` to run preview in background (non-blocking)
  - Default: `"false"` (runs in foreground to show output)

### Running in Background

If you want the preview to run in background so it doesn't block:

```bash
export PREVIEW_IN_BACKGROUND=true
```

Then the preview script will start but won't show output in the main terminal.

## Features

### ✅ Automatic Patch Application
- Multiple fallback strategies
- Clear error messages
- Manual instructions if auto-apply fails

### ✅ Comprehensive Preview
- File-by-file changes
- Diff preview (limited to prevent overwhelming output)
- Git status at a glance

### ✅ Smart Server Detection
- Detects project type (Node.js, Python, etc.)
- Checks if server already running
- Starts appropriate server automatically

### ✅ Actionable Instructions
- Step-by-step testing commands
- Manual patch application steps
- Git push commands when needed

## Troubleshooting

### Patch Not Applying
If the patch fails to apply automatically:
1. Review the patch file: `crewai_patch.diff`
2. Try manual application: `git apply --whitespace=fix crewai_patch.diff`
3. Or copy code manually from the implementation plan

### Server Not Starting
- Check if port is already in use
- Verify project type (Node.js vs Python)
- Check if `package.json` or `server.js` exists

### No Changes Detected
- Patch may not have applied
- Check if changes were already committed
- Review patch file manually

## Integration with Automated Crew

The preview script is automatically called at the end of `print_issue_status()` in `automated_crew.py`:

```python
# After showing status, run preview
run_preview_script(issue.number, work_dir)
```

This ensures every issue gets a preview automatically!

## Summary

**Before**: Manual steps to apply patches, check changes, start server  
**After**: Automatic preview with patch application, diff display, and server startup

The preview script makes it easy to see what changed and test it immediately! 🎉
