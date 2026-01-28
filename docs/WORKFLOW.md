# Complete Workflow: Issue → Implementation → Testing → Push

This document explains the complete workflow from running an issue to pushing changes to remote.

---

## Workflow Overview

```
1. Run Issue
   ↓
2. CrewAI Generates Code (Diff)
   ↓
3. Automatic Patch Application (Local)
   ↓
4. Test Locally
   ↓
5. Push to Remote (When Ready)
```

---

## Step-by-Step Process

### Step 1: Run an Issue

```bash
cd ~/ai-dev-team
source .venv/bin/activate
python3 scripts/automated_crew.py owner/repo 1 <ISSUE_NUMBER>
```

**What happens:**
- CrewAI agents analyze the issue
- Developer agent generates a unified diff patch
- Implementation plan is saved to `implementations/issue_<N>_plan.md`
- Patch file is saved to `crewai_patch.diff`

---

### Step 2: Automatic Patch Application

The system **automatically tries multiple strategies** to apply the patch:

1. **Standard git apply** (5 different methods)
2. **File-by-file application** (if full patch fails)
3. **Direct file editing** (last resort - parses diff and edits files directly)

**Success indicators:**
```
✓ Patch applied successfully using whitespace fix
✓ Changes detected in repository - patch applied successfully
```

**If automatic application fails:**
- Patch file is saved for manual review
- Implementation plan contains full code changes
- You can apply manually or copy code from the plan file

---

### Step 3: Test Locally

After the patch is applied (or manually applied), test the changes:

```bash
cd ~/dev/Beautiful-Timetracker-App

# Check what changed
git status
git diff

# Start local server
python3 -m http.server 8000
# Or if it's a Node.js project:
npm start
# Or if it's a Python project:
python3 app.py
```

**Test the functionality:**
- Open browser to `http://localhost:8000`
- Verify the issue is resolved
- Check for any regressions

---

### Step 4: Push to Remote (When Ready)

Once you've tested and confirmed everything works:

```bash
cd ~/dev/Beautiful-Timetracker-App

# Check current branch
git branch

# If branch exists and changes are committed:
git push -u origin feature/issue-<N>

# If you need to commit first:
git add .
git commit -m "feat: implement solution for issue #<N>"
git push -u origin feature/issue-<N>
```

**Or use automatic push (if enabled):**
Set `AUTO_PUSH=true` in your `.env` file, and the system will automatically:
- Create/checkout branch
- Commit changes
- Push to remote
- Create pull request

---

## Status Reporting

After processing an issue, you'll see a detailed status report:

### Local Implementation & Testing Section
- ✅ Code changes applied successfully
- ✅ Implementation plan location
- ⚠️ Any local warnings
- 🧪 Testing steps

### Git & GitHub Operations Section
- ✅ Branch name
- ✅ Commit status
- ✅ Push status
- ⚠️ Any Git/GitHub warnings

---

## Common Scenarios

### Scenario 1: Patch Applied Successfully

```
✓ Patch applied successfully using whitespace fix
✓ Changes detected in repository - patch applied successfully

📦 LOCAL IMPLEMENTATION & TESTING
✅ Code changes applied successfully to local files
✅ Implementation plan: implementations/issue_707_plan.md

🧪 Testing Steps:
   1. Review implementation plan
   2. Test locally: python3 -m http.server 8000
   3. Open in browser and verify functionality

🔀 GIT & GITHUB OPERATIONS
✅ Branch: feature/issue-707
✅ Changes committed locally
⚠️  Branch not pushed to remote
   To push manually:
      cd ~/dev/Beautiful-Timetracker-App
      git push -u origin feature/issue-707
```

**Next steps:**
1. Test locally
2. If working, push: `git push -u origin feature/issue-707`

---

### Scenario 2: Patch Failed to Apply Automatically

```
⚠ Standard patch application failed. Trying file-by-file approach...
⚠ File-by-file approach failed. Attempting to fix patch...
⚠ All standard methods failed. Attempting direct file editing...
✓ Patch applied successfully using direct file editing

📦 LOCAL IMPLEMENTATION & TESTING
✅ Code changes applied successfully to local files
✅ Implementation plan: implementations/issue_707_plan.md
```

**Next steps:**
1. Verify changes: `git status` and `git diff`
2. Test locally
3. If working, push to remote

---

### Scenario 3: All Automatic Methods Failed

```
⚠ Patch failed to apply after all automatic attempts

📦 LOCAL IMPLEMENTATION & TESTING
⚠️  Code changes generated but not automatically applied
   Patch file: crewai_patch.diff
   To apply manually:
      cd ~/dev/Beautiful-Timetracker-App
      git apply --whitespace=fix crewai_patch.diff
      # Or review and apply changes manually from the patch file
✅ Implementation plan: implementations/issue_707_plan.md
```

**Next steps:**
1. Try manual patch: `git apply --whitespace=fix crewai_patch.diff`
2. Or copy code from `implementations/issue_707_plan.md`
3. Test locally
4. Push when ready

---

## Configuration

### Automatic Push (Optional)

To enable automatic push and PR creation:

```bash
# In .env file
AUTO_PUSH=true
GITHUB_TOKEN=your_token_here
```

### Preview Script (Optional)

The system can automatically start a preview server:

```bash
# In .env file
PREVIEW_IN_BACKGROUND=false  # Set to true to run in background
```

---

## Summary

**The workflow is designed to be automatic:**

1. ✅ **Run issue** → CrewAI generates code
2. ✅ **Automatic patch application** → Multiple strategies ensure success
3. ✅ **Test locally** → Verify it works
4. ✅ **Push when ready** → Manual or automatic

**Key points:**
- Patches are applied **automatically** using multiple fallback strategies
- If automatic application fails, patch file is saved for manual review
- You can test locally before pushing
- Push to remote only when you're ready

The system tries its best to apply patches automatically, but always saves the patch file and implementation plan so you can review or apply manually if needed.
