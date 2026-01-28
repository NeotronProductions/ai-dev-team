"""
Logging helpers: consistent formatting for status summaries.
"""

import re
import subprocess
from pathlib import Path
from .git_ops import get_current_branch, get_head_sha, has_changes


def print_issue_status(issue_number: int, work_dir: Path, warnings: list[str], implementation_status: dict = None):
    """
    Print issue status separated into two sections:
    1. Local Implementation & Testing (what you can do locally)
    2. Git/GitHub Operations (version control status)
    
    Args:
        issue_number: Issue number
        work_dir: Working directory path
        warnings: List of warning messages
        implementation_status: Optional dict with did_commit, did_push flags
    """
    # Separate warnings into local and git/github categories
    local_warnings = []
    git_warnings = []
    
    for warning in warnings:
        warning_lower = warning.lower()
        if any(keyword in warning_lower for keyword in ['patch', 'implementation', 'plan', 'file']):
            local_warnings.append(warning)
        elif any(keyword in warning_lower for keyword in ['git', 'github', 'push', 'branch', 'pipeline', 'remote', 'network']):
            git_warnings.append(warning)
        else:
            local_warnings.append(warning)
    
    # Check local implementation status (per-issue preferred, legacy fallback)
    issue_patch = work_dir / "patches" / f"issue_{issue_number}.diff"
    legacy_patch = work_dir / "crewai_patch.diff"
    patch_file = issue_patch if issue_patch.exists() else legacy_patch
    plan_file = work_dir / "implementations" / f"issue_{issue_number}_plan.md"
    patch_applied = has_changes(work_dir) if (work_dir / ".git").exists() else False
    
    # Check test execution status from implementation plan
    test_status = None
    test_executed = False
    if plan_file.exists():
        try:
            plan_content = plan_file.read_text(encoding='utf-8')
            if "## Test Results" in plan_content or "Test Execution Status" in plan_content:
                test_executed = True
                status_match = re.search(r"Test Execution Status:\s*([✅❌⚠️ℹ️]+)\s*([A-Z]+)", plan_content)
                if status_match:
                    test_status = f"{status_match.group(1)} {status_match.group(2)}"
                elif "Status: ✅ PASSED" in plan_content:
                    test_status = "✅ PASSED"
                elif "Status: ❌ FAILED" in plan_content:
                    test_status = "❌ FAILED"
                elif "Status: ⚠️  NO TESTS FOUND" in plan_content:
                    test_status = "⚠️  NO TESTS FOUND"
                else:
                    test_status = "ℹ️  COMPLETED"
        except:
            pass
    
    # Capture ACTUAL current git branch and HEAD commit
    current_branch = get_current_branch(work_dir)
    head_sha = get_head_sha(work_dir, short=True)
    git_committed = False
    git_pushed = False
    
    if (work_dir / ".git").exists():
        # Use implementation_status flags if available (most accurate)
        if implementation_status:
            git_committed = implementation_status.get("did_commit", False)
            git_pushed = implementation_status.get("did_push", False)
        else:
            # Fallback: Check if there are commits on this branch
            try:
                result = subprocess.run(['git', 'log', '--oneline', '-1'], 
                                      cwd=work_dir, capture_output=True, text=True, check=False, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    git_committed = True
                
                # Check if branch is pushed (fallback method)
                if current_branch:
                    result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', '@{u}'], 
                                          cwd=work_dir, capture_output=True, text=True, check=False, timeout=5)
                    if result.returncode == 0:
                        git_pushed = True
            except Exception:
                pass
    
    # Print Section 1: Local Implementation & Testing
    print(f"\n{'='*70}")
    print(f"📦 LOCAL IMPLEMENTATION & TESTING - Issue #{issue_number}")
    print(f"{'='*70}")
    
    if patch_applied:
        print(f"✅ Code changes applied successfully to local files")
    elif patch_file.exists():
        print(f"⚠️  Code changes generated but not automatically applied")
        print(f"   Patch file: {patch_file}")
        print(f"   To apply manually:")
        print(f"      cd {work_dir}")
        try:
            rel_patch = patch_file.relative_to(work_dir)
        except Exception:
            rel_patch = patch_file.name
        print(f"      git apply --whitespace=fix {rel_patch}")
    else:
        print(f"ℹ️  Implementation plan generated (no patch file)")
    
    if plan_file.exists():
        print(f"✅ Implementation plan: {plan_file}")
        print(f"   Contains full code changes and implementation details")
    
    # Show test execution status
    if test_executed:
        print(f"\n🧪 Test Execution Status:")
        if test_status:
            print(f"   {test_status}")
        else:
            print(f"   ℹ️  Tests were executed (check plan file for details)")
        print(f"   Review test results in: {plan_file}")
    elif patch_applied:
        print(f"\n⚠️  Test Execution:")
        print(f"   Tests were not executed (may have been skipped or failed to start)")
    
    if local_warnings:
        print(f"\n⚠️  Local Warnings:")
        for warning in local_warnings:
            print(f"   - {warning}")
    
    # Testing instructions
    if not test_executed:
        print(f"\n🧪 Manual Testing Steps:")
    print(f"   1. Review implementation plan: {plan_file}")
    if patch_file.exists() and not patch_applied:
        print(f"   2. Apply patch manually (see above) or copy code from plan file")
    print(f"   3. Test locally:")
    print(f"      cd {work_dir}")
    if (work_dir / "package.json").exists():
        print(f"      npm start  # or: node server.js")
    elif (work_dir / "server.js").exists():
        print(f"      node server.js")
    else:
        print(f"      python3 -m http.server 8000  # or your preferred method")
    print(f"   4. Open in browser and verify functionality")
    
    # Print Section 2: Git/GitHub Operations
    print(f"\n{'='*70}")
    print(f"🔀 GIT STATUS / SUMMARY - Issue #{issue_number}")
    print(f"{'='*70}")
    
    if not (work_dir / ".git").exists():
        print(f"ℹ️  Not a git repository - Git operations skipped")
    else:
        if current_branch:
            print(f"📍 Current Branch: {current_branch}")
        else:
            print(f"⚠️  Branch status unknown")
        
        if head_sha:
            print(f"📍 HEAD Commit: {head_sha}")
        else:
            print(f"⚠️  HEAD commit unknown")
        
        # Only show "Committed ✅" if commit actually succeeded
        if git_committed:
            print(f"✅ Committed")
        else:
            print(f"⚠️  Not committed")
        
        # Only show "Pushed ✅" if push actually succeeded
        if git_pushed:
            print(f"✅ Pushed")
        else:
            print(f"⚠️  Not pushed")
            if current_branch:
                print(f"   To push manually:")
                print(f"      cd {work_dir}")
                print(f"      git push -u origin {current_branch}")
        
        if git_warnings:
            print(f"\n⚠️  Git/GitHub Warnings:")
            for warning in git_warnings:
                print(f"   - {warning}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 SUMMARY - Issue #{issue_number}")
    print(f"{'='*70}")
    
    if patch_applied:
        print(f"✅ Code changes: Applied successfully")
    else:
        print(f"⚠️  Code changes: Not applied (check patch file)")
    
    # Test status
    if test_executed:
        if test_status and "PASSED" in test_status:
            print(f"✅ Tests: Executed and PASSED")
        elif test_status and "FAILED" in test_status:
            print(f"❌ Tests: Executed but FAILED - Review test results")
        elif test_status and "NO TESTS FOUND" in test_status:
            print(f"⚠️  Tests: No tests found - Manual verification recommended")
        else:
            print(f"ℹ️  Tests: Executed (check results in plan file)")
    else:
        print(f"⚠️  Tests: Not executed")
    
    # Git status
    if git_warnings:
        print(f"⚠️  Git/GitHub: Some operations had issues (non-critical for local testing)")
    elif current_branch and git_committed and git_pushed:
        print(f"✅ Git/GitHub: All operations completed successfully")
    elif current_branch:
        print(f"ℹ️  Git/GitHub: Partial completion (check status above)")
    
    print(f"{'='*70}")
    print(f"{'='*70}\n")
