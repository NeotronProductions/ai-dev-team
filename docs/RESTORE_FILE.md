# File Restoration Needed

## ⚠️ Current Status

The `automated_crew.py` file was accidentally overwritten and now only contains:
- `move_issue_in_project_v2()` function (160 lines)

## ✅ What Needs to Be Restored

The complete file should have ~800+ lines including:

1. **Imports** (os, sys, subprocess, re, Path, dotenv, github, crewai, json, requests)
2. **Environment setup** (load_dotenv, GITHUB_TOKEN, WORK_DIR)
3. **Helper functions**:
   - `get_github_client()`
   - `get_next_issue()`
   - `mark_issue_processed()`
4. **Crew creation**:
   - `create_implementation_crew()` - Product Manager, Architect, Developer, Reviewer
5. **Issue processing**:
   - `process_issue()` - Runs the crew
6. **Patch handling**:
   - `extract_diff()` - Extracts unified diff from crew output
   - `apply_patch()` - Applies patch to repo
   - `has_changes()` - Checks for git changes
   - `apply_implementation()` - Saves plan and applies patch
7. **Git operations**:
   - `create_branch_and_commit()` - Creates branch, commits (with push/PR support)
   - `create_pr()` - Creates pull request
8. **Pipeline movement**:
   - `move_issue_in_project()` - Main function (tries GraphQL V2 first, falls back to classic)
   - `move_issue_in_project_v2()` - GraphQL Projects V2 implementation (already in file)
9. **Main execution**:
   - `run_automated_crew()` - Orchestrates the workflow
   - `if __name__ == "__main__":` - Command line interface

## 🔧 Solution

The file needs to be completely restored. The transcript shows all the code, but it's scattered across many edits.

## 📋 Quick Answer to User's Question

**"So will the agent developer of crew ai program the user story and push to the project repo?"**

**Current implementation:**
- ✅ Developer agent produces unified diff patch
- ✅ System applies patch to local repo
- ✅ Creates branch and commits
- ❌ Does NOT push (unless `AUTO_PUSH=true` in .env)
- ❌ Does NOT create PR (unless push enabled)

**To enable push/PR:**
```bash
echo "AUTO_PUSH=true" >> ~/ai-dev-team/.env
```

Then the workflow will:
1. Developer writes code (diff patch)
2. Patch applied to repo
3. Branch created
4. Changes committed
5. **Branch pushed to GitHub** (if AUTO_PUSH=true)
6. **Pull Request created** (if AUTO_PUSH=true)
