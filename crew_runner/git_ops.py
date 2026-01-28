"""
Git operations: branch management, commits, pushes.
Side-effect wrappers with clear return codes.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional


def get_current_branch(work_dir: Path) -> Optional[str]:
    """Get current git branch name."""
    if not (work_dir / ".git").exists():
        return None
    
    try:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                              cwd=work_dir, capture_output=True, text=True, check=False, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_head_sha(work_dir: Path, short: bool = False) -> Optional[str]:
    """Get HEAD commit SHA."""
    if not (work_dir / ".git").exists():
        return None
    
    try:
        cmd = ['git', 'rev-parse', '--short', 'HEAD'] if short else ['git', 'rev-parse', 'HEAD']
        result = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True, check=False, timeout=5)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def get_git_changed_files(work_dir: Path) -> list[str]:
    """Get list of changed files from git status. Returns empty list if no changes."""
    if not (work_dir / ".git").exists():
        return []
    
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return []
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Format: " M file.js" or "?? newfile.js"
                file_path = line[3:].strip()
                if file_path:
                    files.append(file_path)
        
        return files
    except Exception:
        return []


def has_changes(cwd: Path) -> bool:
    """Check if there are uncommitted changes."""
    if not (cwd / ".git").exists():
        return False
    
    try:
        r = subprocess.run(["git", "status", "--porcelain"], 
                          cwd=cwd, text=True, capture_output=True, check=True)
        return bool(r.stdout.strip())
    except Exception:
        return False


def ensure_feature_branch(repo_root: Path, issue_number: Optional[int] = None) -> str:
    """
    Hard branch-safety guard: Ensure we're on a feature branch before applying changes.
    
    If on protected branch (development/main/master):
    - Check for uncommitted changes (abort if found)
    - Auto-create/checkout feature branch if issue_number provided
    - Abort with error if issue_number not provided
    
    Args:
        repo_root: Path to git repository root
        issue_number: Optional issue number for auto-remediation
        
    Returns:
        str: The branch name we ended up on
        
    Raises:
        ValueError: If on protected branch and cannot remediate
    """
    if not (repo_root / ".git").exists():
        # Not a git repo, allow proceeding (may be a test scenario)
        return "not-a-git-repo"
    
    # Get current branch
    current_branch = get_current_branch(repo_root)
    if not current_branch:
        # Detached HEAD or no branch - allow but warn
        print("⚠️  Warning: Not on a named branch (detached HEAD)")
        return "detached-head"
    
    # Protected branches that should never receive direct changes
    protected_branches = ['development', 'main', 'master']
    
    if current_branch not in protected_branches:
        # Already on a feature branch or other non-protected branch - proceed
        return current_branch
    
    # On protected branch - need to remediate
    print(f"\n{'='*70}")
    print(f"🚨 BRANCH SAFETY GUARD TRIGGERED")
    print(f"{'='*70}")
    print(f"❌ Currently on protected branch: {current_branch}")
    print(f"   Implementation changes cannot be applied to protected branches")
    
    # Check for uncommitted changes
    if has_changes(repo_root):
        print(f"\n❌ Uncommitted changes detected on {current_branch}")
        print(f"   Cannot auto-remediate branch with uncommitted changes")
        print(f"\n   To proceed:")
        print(f"   1. Commit or stash your changes:")
        print(f"      cd {repo_root}")
        print(f"      git stash  # or: git commit -am 'WIP: ...'")
        print(f"   2. Manually create/checkout feature branch:")
        print(f"      git checkout -b feature/issue-{issue_number if issue_number else 'XXX'}")
        print(f"   3. Re-run the implementation")
        raise ValueError(
            f"Cannot apply changes on protected branch '{current_branch}' with uncommitted changes. "
            f"Please commit/stash changes and create feature branch manually."
        )
    
    # Auto-remediation: create/checkout feature branch
    if issue_number is None:
        print(f"\n❌ Issue number not provided - cannot auto-create feature branch")
        print(f"\n   To proceed:")
        print(f"   1. Manually create/checkout feature branch:")
        print(f"      cd {repo_root}")
        print(f"      git checkout -b feature/issue-XXX  # Replace XXX with issue number")
        print(f"   2. Re-run the implementation with issue number specified")
        raise ValueError(
            f"Cannot apply changes on protected branch '{current_branch}'. "
            f"Issue number required for auto-remediation. Please create feature branch manually or specify issue number."
        )
    
    # Create/checkout feature branch
    feature_branch = f"feature/issue-{issue_number}"
    print(f"\n🔄 Auto-remediation: Creating/checkout feature branch '{feature_branch}'")
    
    try:
        # Check if feature branch already exists
        result = subprocess.run(
            ['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{feature_branch}'],
            cwd=repo_root, capture_output=True, check=False, timeout=5
        )
        
        if result.returncode == 0:
            # Branch exists - checkout it
            print(f"   Branch '{feature_branch}' already exists, checking out...")
            result = subprocess.run(
                ['git', 'checkout', feature_branch],
                cwd=repo_root, capture_output=True, text=True, check=False, timeout=10
            )
            if result.returncode != 0:
                print(f"❌ Failed to checkout existing branch: {result.stderr}")
                raise ValueError(f"Failed to checkout feature branch '{feature_branch}': {result.stderr}")
        else:
            # Branch doesn't exist - create it
            print(f"   Creating new branch '{feature_branch}' from '{current_branch}'...")
            result = subprocess.run(
                ['git', 'checkout', '-b', feature_branch],
                cwd=repo_root, capture_output=True, text=True, check=False, timeout=10
            )
            if result.returncode != 0:
                print(f"❌ Failed to create branch: {result.stderr}")
                raise ValueError(f"Failed to create feature branch '{feature_branch}': {result.stderr}")
        
        # Verify we're on the feature branch
        new_branch = get_current_branch(repo_root)
        if new_branch != feature_branch:
            raise ValueError(f"Branch checkout failed: expected '{feature_branch}', got '{new_branch}'")
        
        print(f"✅ Successfully switched to feature branch: {feature_branch}")
        print(f"{'='*70}\n")
        return feature_branch
        
    except subprocess.TimeoutExpired:
        raise ValueError(f"Git operation timed out while creating feature branch '{feature_branch}'")
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Error during branch remediation: {str(e)}")


def ensure_base_branch(work_dir: Path):
    """Ensure we're on the base branch (development) before processing issues."""
    if not (work_dir / ".git").exists():
        return
    
    try:
        current_branch = get_current_branch(work_dir)
        if not current_branch:
            return
        
        # Determine base branch (prefer development, fallback to main/master)
        base_branch = None
        result = subprocess.run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/development'],
                              cwd=work_dir, capture_output=True, check=False)
        if result.returncode == 0:
            base_branch = 'development'
        else:
            for branch in ['main', 'master']:
                result = subprocess.run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch}'],
                                      cwd=work_dir, capture_output=True, check=False)
                if result.returncode == 0:
                    base_branch = branch
                    break
        
        if not base_branch:
            print(f"⚠ No development/main/master branch found, staying on {current_branch}")
            return
        
        # Switch to base branch if not already on it
        if current_branch != base_branch:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  cwd=work_dir, capture_output=True, text=True, check=False)
            if result.stdout.strip():
                print(f"⚠ Uncommitted changes detected on {current_branch}")
                print(f"   Switching to {base_branch} will carry these changes over")
            
            print(f"🔄 Switching to base branch: {base_branch}")
            result = subprocess.run(['git', 'checkout', base_branch], 
                                  cwd=work_dir, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                subprocess.run(['git', 'pull', '--ff-only'], 
                             cwd=work_dir, capture_output=True, check=False)
                print(f"✓ On base branch: {base_branch}")
    except Exception as e:
        print(f"⚠ Error ensuring base branch: {e}")


def create_branch_and_commit(issue_number: int, work_dir: Path, repo_name: str = None, 
                            issue_title: str = None, push: bool = False) -> dict:
    """
    Create a git branch, commit changes, and optionally push.
    Returns dict with: did_commit, did_push, branch_name, commit_hash (if successful)
    """
    original_dir = os.getcwd()
    os.chdir(work_dir)
    
    try:
        # Check if git repo exists
        if not (Path(work_dir) / ".git").exists():
            print("⚠ Not a git repository, skipping branch/commit")
            return {"did_commit": False, "did_push": False, "branch_name": None, "commit_hash": None}
        
        # Get current branch
        current_branch = get_current_branch(work_dir)
        
        # Determine base branch
        base_branch = None
        result = subprocess.run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/development'],
                              cwd=work_dir, capture_output=True, check=False)
        if result.returncode == 0:
            base_branch = 'development'
        else:
            for branch in ['main', 'master']:
                result = subprocess.run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch}'],
                                      cwd=work_dir, capture_output=True, check=False)
                if result.returncode == 0:
                    base_branch = branch
                    break
        
        if not base_branch:
            base_branch = current_branch or 'main'
        
        # Switch to base branch if not already on it
        if current_branch != base_branch:
            subprocess.run(['git', 'checkout', base_branch], cwd=work_dir, check=False, capture_output=True)
            subprocess.run(['git', 'pull', '--ff-only'], cwd=work_dir, check=False, capture_output=True)
        
        # Create branch
        branch_name = f"feature/issue-{issue_number}"
        
        if current_branch != branch_name:
            result = subprocess.run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch_name}'],
                                  cwd=work_dir, capture_output=True, check=False)
            if result.returncode == 0:
                result = subprocess.run(['git', 'checkout', branch_name], 
                                      cwd=work_dir, capture_output=True, text=True, check=False)
                if result.returncode != 0:
                    subprocess.run(['git', 'branch', '-D', branch_name], cwd=work_dir, check=False, capture_output=True)
                    result = subprocess.run(['git', 'checkout', '-b', branch_name], 
                                          cwd=work_dir, capture_output=True, text=True, check=False)
                    if result.returncode != 0:
                        return {"did_commit": False, "did_push": False, "branch_name": None, "commit_hash": None}
            else:
                result = subprocess.run(['git', 'checkout', '-b', branch_name], 
                                      cwd=work_dir, capture_output=True, text=True, check=False)
                if result.returncode != 0:
                    return {"did_commit": False, "did_push": False, "branch_name": None, "commit_hash": None}
        
        # Check for changes to commit
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              cwd=work_dir, capture_output=True, text=True, check=True)
        
        status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        files_to_commit = []
        for line in status_lines:
            if line.strip():
                file_path = line[3:].strip()
                if not file_path.endswith('crewai_patch.diff') and not file_path.endswith('_patch.diff'):
                    files_to_commit.append(file_path)
        
        if not files_to_commit:
            print("⚠ No source files to commit (only patch artifacts/plans or no changes)")
            return {"did_commit": False, "did_push": False, "branch_name": branch_name, "commit_hash": None}
        
        # Add files
        for file_path in files_to_commit:
            subprocess.run(['git', 'add', file_path], cwd=work_dir, check=False, capture_output=True)
        
        # Verify staged
        result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                              cwd=work_dir, capture_output=True, text=True, check=True)
        if not result.stdout.strip():
            print("⚠ No files staged for commit")
            return {"did_commit": False, "did_push": False, "branch_name": branch_name, "commit_hash": None}
        
        # Commit
        commit_msg = f"feat: implement solution for issue #{issue_number}\n\nCloses #{issue_number}"
        if issue_title:
            commit_msg = f"feat: implement solution for issue #{issue_number}: {issue_title}\n\nCloses #{issue_number}"
        
        result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                              cwd=work_dir, capture_output=True, text=True, check=False)
        commit_result_dict = {
            "did_commit": False,
            "did_push": False,
            "branch_name": branch_name,
            "commit_hash": None
        }
        if result.returncode != 0:
            print(f"⚠ Failed to commit: {result.stderr}")
            return commit_result_dict
        
        commit_result_dict["did_commit"] = True
        commit_hash = get_head_sha(work_dir, short=False)
        if commit_hash:
            commit_result_dict["commit_hash"] = commit_hash
        print(f"✓ Created branch: {branch_name}")
        print(f"✓ Committed changes")
        
        # Push if requested
        if push:
            try:
                import socket
                try:
                    socket.create_connection(("github.com", 443), timeout=5)
                except (socket.timeout, OSError):
                    print(f"⚠ Network connectivity issue: Cannot reach github.com")
                    return commit_result_dict
                
                push_result = subprocess.run(['git', 'push', '-u', 'origin', branch_name], 
                                      cwd=work_dir, capture_output=True, text=True, check=False, timeout=60)
                if push_result.returncode == 0:
                    commit_result_dict["did_push"] = True
                    print(f"✓ Pushed branch to origin")
                else:
                    error_msg = push_result.stderr or push_result.stdout or "Unknown error"
                    if "timeout" in error_msg.lower() or "could not connect" in error_msg.lower():
                        print(f"⚠ Network connectivity issue: Cannot reach GitHub")
                    else:
                        print(f"⚠ Failed to push branch: {error_msg[:200]}")
            except subprocess.TimeoutExpired:
                print(f"⚠ Push timed out (network issue)")
            except Exception as e:
                print(f"⚠ Failed to push branch: {e}")
        
        return commit_result_dict
    except Exception as e:
        print(f"⚠ Error in git operations: {e}")
        import traceback
        traceback.print_exc()
        return {"did_commit": False, "did_push": False, "branch_name": None, "commit_hash": None}
    finally:
        os.chdir(original_dir)
