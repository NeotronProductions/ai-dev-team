#!/usr/bin/env python3
"""
Preview and Apply Implementation Script

This script runs after CrewAI generates code to:
1. Apply patches automatically
2. Show preview of changes
3. Start local server for testing
4. Display summary of what changed

Usage:
    python preview_implementation.py [issue_number]
    python preview_implementation.py  # Shows latest issue
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

WORK_DIR = Path.home() / "dev" / "Beautiful-Timetracker-App"
PROCESSED_ISSUES_FILE = Path.home() / "ai-dev-team" / "processed_issues.json"

def get_latest_issue() -> Optional[int]:
    """Get the most recently processed issue number"""
    if not PROCESSED_ISSUES_FILE.exists():
        return None
    
    try:
        with open(PROCESSED_ISSUES_FILE, 'r') as f:
            issues = json.load(f)
            if isinstance(issues, list) and issues:
                return max(issues)
    except Exception:
        pass
    
    return None

def get_issue_files(issue_number: int) -> Tuple[Path, Path]:
    """Get paths to patch file and implementation plan"""
    patch_file = WORK_DIR / "crewai_patch.diff"
    plan_file = WORK_DIR / "implementations" / f"issue_{issue_number}_plan.md"
    return patch_file, plan_file

def apply_patch(work_dir: Path, patch_file: Path) -> Tuple[bool, str]:
    """Try to apply patch with multiple strategies"""
    if not patch_file.exists():
        return False, "Patch file not found"
    
    strategies = [
        (["git", "apply", "--whitespace=fix", str(patch_file)], "whitespace fix"),
        (["git", "apply", "--ignore-whitespace", str(patch_file)], "ignore whitespace"),
        (["git", "apply", "--3way", str(patch_file)], "3-way merge"),
        (["git", "apply", "--unidiff-zero", str(patch_file)], "unidiff-zero"),
    ]
    
    for cmd, strategy in strategies:
        try:
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return True, f"Applied using {strategy}"
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            continue
    
    return False, "All automatic strategies failed"

def has_changes(work_dir: Path) -> bool:
    """Check if there are uncommitted changes"""
    if not (work_dir / ".git").exists():
        return False
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=work_dir,
        capture_output=True,
        text=True,
        check=False
    )
    return bool(result.stdout.strip())

def get_changed_files(work_dir: Path) -> List[str]:
    """Get list of changed files"""
    if not (work_dir / ".git").exists():
        return []
    
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=work_dir,
        capture_output=True,
        text=True,
        check=False
    )
    
    if result.returncode == 0:
        files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        return files
    return []

def get_diff_preview(work_dir: Path, max_lines: int = 100) -> str:
    """Get a preview of the diff"""
    if not (work_dir / ".git").exists():
        return "Not a git repository"
    
    # Get diff stat (summary)
    result = subprocess.run(
        ["git", "diff", "--stat"],
        cwd=work_dir,
        capture_output=True,
        text=True,
        check=False
    )
    
    stat = result.stdout.strip() if result.returncode == 0 else ""
    
    # Get actual diff (limited)
    result = subprocess.run(
        ["git", "diff", "--color=never"],
        cwd=work_dir,
        capture_output=True,
        text=True,
        check=False
    )
    
    diff = result.stdout.strip() if result.returncode == 0 else ""
    
    # If no diff, check if patch file exists and show it
    if not diff:
        patch_file = work_dir / "crewai_patch.diff"
        if patch_file.exists():
            try:
                with open(patch_file, 'r') as f:
                    patch_content = f.read()
                    # Limit patch lines
                    lines = patch_content.split('\n')
                    if len(lines) > max_lines:
                        diff = '\n'.join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"
                    else:
                        diff = patch_content
            except Exception:
                diff = "Could not read patch file"
    
    # Limit diff lines if too long
    if diff:
        lines = diff.split('\n')
        if len(lines) > max_lines:
            diff = '\n'.join(lines[:max_lines]) + f"\n... ({len(lines) - max_lines} more lines)"
    
    return f"{stat}\n\n{diff}" if stat else diff

def get_git_status(work_dir: Path) -> dict:
    """Get current git status"""
    status = {
        "branch": None,
        "committed": False,
        "pushed": False,
        "has_changes": False
    }
    
    if not (work_dir / ".git").exists():
        return status
    
    # Get branch
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=work_dir,
        capture_output=True,
        text=True,
        check=False,
        timeout=5
    )
    if result.returncode == 0:
        status["branch"] = result.stdout.strip()
    
    # Check if committed
    result = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=work_dir,
        capture_output=True,
        text=True,
        check=False,
        timeout=5
    )
    if result.returncode == 0 and result.stdout.strip():
        status["committed"] = True
    
    # Check if pushed
    if status["branch"]:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "@{u}"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            check=False,
            timeout=5
        )
        if result.returncode == 0:
            status["pushed"] = True
    
    status["has_changes"] = has_changes(work_dir)
    return status

def start_preview_server(work_dir: Path) -> Optional[subprocess.Popen]:
    """Start a local server for preview"""
    # Check what type of server to start
    if (work_dir / "package.json").exists():
        # Node.js project
        try:
            # Check if server is already running
            result = subprocess.run(
                ["lsof", "-ti", ":9000"],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                print("   ℹ️  Server already running on port 9000")
                return None
            
            # Start npm server
            process = subprocess.Popen(
                ["npm", "start"],
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            return process
        except Exception as e:
            print(f"   ⚠️  Could not start npm server: {e}")
            return None
    elif (work_dir / "server.js").exists():
        # Node.js server file
        try:
            result = subprocess.run(
                ["lsof", "-ti", ":9000"],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                print("   ℹ️  Server already running on port 9000")
                return None
            
            process = subprocess.Popen(
                ["node", "server.js"],
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            return process
        except Exception as e:
            print(f"   ⚠️  Could not start node server: {e}")
            return None
    else:
        # Try Python simple server
        try:
            result = subprocess.run(
                ["lsof", "-ti", ":8000"],
                capture_output=True,
                check=False
            )
            if result.returncode == 0:
                print("   ℹ️  Server already running on port 8000")
                return None
            
            process = subprocess.Popen(
                [sys.executable, "-m", "http.server", "8000"],
                cwd=work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )
            return process
        except Exception as e:
            print(f"   ⚠️  Could not start Python server: {e}")
            return None
    
    return None

def print_preview(issue_number: int, work_dir: Path):
    """Print comprehensive preview of changes"""
    patch_file, plan_file = get_issue_files(issue_number)
    
    print("\n" + "="*70)
    print(f"🔍 PREVIEW: Issue #{issue_number} Implementation")
    print("="*70)
    
    # 1. Patch Status
    print(f"\n📦 PATCH STATUS")
    print("-" * 70)
    if patch_file.exists():
        print(f"✅ Patch file found: {patch_file}")
        
        # Try to apply if not already applied
        if not has_changes(work_dir):
            print("   Attempting to apply patch...")
            applied, message = apply_patch(work_dir, patch_file)
            if applied:
                print(f"   ✅ {message}")
            else:
                print(f"   ⚠️  {message}")
                print(f"   💡 To apply manually:")
                print(f"      cd {work_dir}")
                print(f"      git apply --whitespace=fix crewai_patch.diff")
        else:
            print("   ✅ Changes already detected in repository")
    else:
        print(f"⚠️  No patch file found")
    
    # 2. Implementation Plan
    print(f"\n📄 IMPLEMENTATION PLAN")
    print("-" * 70)
    if plan_file.exists():
        print(f"✅ Plan file: {plan_file}")
        # Get file size
        size = plan_file.stat().st_size
        print(f"   Size: {size:,} bytes")
    else:
        print(f"⚠️  Plan file not found")
    
    # 3. Changed Files
    print(f"\n📝 CHANGED FILES")
    print("-" * 70)
    changed_files = get_changed_files(work_dir)
    if changed_files:
        print(f"✅ {len(changed_files)} file(s) modified:")
        for file in changed_files:
            print(f"   - {file}")
    else:
        print("ℹ️  No changes detected (patch may not have applied)")
    
    # 4. Diff Preview
    # Show diff if there are changes OR if patch file exists (even if not applied)
    if changed_files or patch_file.exists():
        print(f"\n🔍 DIFF PREVIEW")
        print("-" * 70)
        diff_preview = get_diff_preview(work_dir, max_lines=100)
        if diff_preview and diff_preview.strip():
            print(diff_preview)
        else:
            print("No diff available")
            if patch_file.exists():
                print(f"   💡 Patch file exists but not applied - review: {patch_file}")
    
    # 5. Git Status
    print(f"\n🔀 GIT STATUS")
    print("-" * 70)
    git_status = get_git_status(work_dir)
    if git_status["branch"]:
        print(f"Branch: {git_status['branch']}")
        print(f"Committed: {'✅' if git_status['committed'] else '❌'}")
        print(f"Pushed: {'✅' if git_status['pushed'] else '❌'}")
        print(f"Uncommitted changes: {'✅' if git_status['has_changes'] else '❌'}")
    else:
        print("Not a git repository")
    
    # 6. Testing Instructions
    print(f"\n🧪 TESTING")
    print("-" * 70)
    
    # Determine server type
    server_type = None
    server_port = None
    
    if (work_dir / "package.json").exists():
        server_type = "npm"
        server_port = 9000
    elif (work_dir / "server.js").exists():
        server_type = "node"
        server_port = 9000
    else:
        server_type = "python"
        server_port = 8000
    
    print(f"To test locally:")
    print(f"  1. cd {work_dir}")
    if server_type == "npm":
        print(f"  2. npm start")
    elif server_type == "node":
        print(f"  2. node server.js")
    else:
        print(f"  2. python3 -m http.server {server_port}")
    print(f"  3. Open http://localhost:{server_port} in your browser")
    
    # Try to start server automatically
    print(f"\n🚀 Starting preview server...")
    server_process = start_preview_server(work_dir)
    if server_process:
        print(f"   ✅ Server starting in background")
        print(f"   📍 Preview at: http://localhost:{server_port}")
        print(f"   ⚠️  Press Ctrl+C to stop the server")
    else:
        print(f"   ℹ️  Server may already be running or could not start")
        print(f"   📍 Try: http://localhost:{server_port}")
    
    # 7. Summary
    print(f"\n" + "="*70)
    print(f"📊 SUMMARY")
    print("="*70)
    
    summary_items = []
    if patch_file.exists():
        summary_items.append("✅ Patch file generated")
    if plan_file.exists():
        summary_items.append("✅ Implementation plan saved")
    if changed_files:
        summary_items.append(f"✅ {len(changed_files)} file(s) modified")
    if git_status["committed"]:
        summary_items.append("✅ Changes committed")
    if git_status["pushed"]:
        summary_items.append("✅ Branch pushed")
    
    if summary_items:
        for item in summary_items:
            print(f"   {item}")
    else:
        print("   ⚠️  No changes detected - review patch file manually")
    
    print("\n" + "="*70 + "\n")

def main():
    """Main entry point"""
    # Get issue number from command line or latest
    issue_number = None
    if len(sys.argv) > 1:
        try:
            issue_number = int(sys.argv[1])
        except ValueError:
            print(f"❌ Invalid issue number: {sys.argv[1]}")
            sys.exit(1)
    else:
        issue_number = get_latest_issue()
        if not issue_number:
            print("❌ No issue number provided and no processed issues found")
            print("Usage: python preview_implementation.py [issue_number]")
            sys.exit(1)
    
    # Check if work directory exists
    if not WORK_DIR.exists():
        print(f"❌ Work directory not found: {WORK_DIR}")
        sys.exit(1)
    
    # Print preview
    try:
        print_preview(issue_number, WORK_DIR)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
