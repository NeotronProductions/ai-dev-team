"""
Path safety: normalization, traversal prevention, and repo_root containment checks.
"""

import os
from pathlib import Path


def get_repo_file_allowlist(work_dir: Path) -> set[str]:
    """
    Build a set of existing files in the repo (excluding build artifacts, node_modules, etc.).
    Used to prevent edits to non-existent backend files or files outside the repo.
    Returns set of relative file paths.
    """
    allowlist = set()
    exclude_dirs = {'.git', 'node_modules', 'dist', 'build', '.next', '.nuxt', 
                    '__pycache__', '.pytest_cache', '.venv', 'venv', 'env',
                    '.crewai_cache', 'coverage', '.coverage'}
    
    if not work_dir.exists():
        return allowlist
    
    try:
        for root, dirs, files in os.walk(work_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for file in files:
                file_path = Path(root) / file
                try:
                    rel_path = file_path.relative_to(work_dir)
                    allowlist.add(str(rel_path))
                except ValueError:
                    # File outside work_dir, skip
                    continue
    except Exception as e:
        print(f"⚠️  Warning: Could not build repo file allowlist: {e}")
    
    return allowlist


def validate_path_safety(path: str, work_dir: Path, change_index: int) -> list[str]:
    """
    Validate path safety: reject absolute paths, .. traversal, ensure within repo_root.
    Returns list of errors (empty if valid).
    """
    errors = []
    
    # Reject absolute paths
    if Path(path).is_absolute():
        errors.append(f"Change {change_index}: Absolute path rejected: '{path}'. Use relative paths only.")
        return errors
    
    # Reject paths containing .. segments
    if ".." in path:
        errors.append(f"Change {change_index}: Path traversal rejected: '{path}'. Paths containing '..' are not allowed.")
        return errors
    
    # Resolve final write path and ensure it stays inside repo_root
    try:
        resolved_path = (work_dir / path).resolve()
        # Check if resolved path is still within work_dir
        try:
            resolved_path.relative_to(work_dir.resolve())
        except ValueError:
            errors.append(f"Change {change_index}: Path escapes repository root: '{path}' resolves outside repo.")
            return errors
    except Exception as e:
        errors.append(f"Change {change_index}: Invalid path '{path}': {str(e)}")
        return errors
    
    return errors
