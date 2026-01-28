"""
Schema types, normalization, and validation for structured changes.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from .path_safety import validate_path_safety, get_repo_file_allowlist


@dataclass
class RunState:
    """
    Single source of truth for run state to prevent fall-through.
    Tracks all critical flags and ensures proper gating.
    """
    applied_ok: bool = False
    coverage_ok: bool = False
    did_commit: bool = False
    did_push: bool = False
    did_move_done: bool = False
    errors: list[str] = field(default_factory=list)
    current_branch: Optional[str] = None
    head_sha_before: Optional[str] = None
    head_sha_after: Optional[str] = None


def normalize_change_schema(change: dict) -> tuple[str, list[str]]:
    """
    Normalize change schema: accept both "path" and "file", normalize to "path".
    Returns (normalized_path, errors)
    """
    errors = []
    
    if "path" not in change and "file" not in change:
        return "", ["Missing 'path' or 'file' field"]
    
    # Normalize: set path from either field, always delete "file" after normalization
    path = change.get("path") or change.get("file")
    change["path"] = path  # Normalize in place
    if "file" in change:
        del change["file"]  # Always remove "file" to avoid ambiguity
    
    return path, errors


def validate_operation(change: dict, operation: str, i: int) -> list[str]:
    """Validate operation type and required fields."""
    errors = []
    
    # Legacy operations
    legacy_ops = ["create", "replace", "edit", "delete"]
    # New robust operations
    new_ops = ["replace_file", "upsert_function_js", "upsert_css_selector", 
               "insert_after_anchor", "insert_before_anchor", "append_if_missing"]
    valid_ops = legacy_ops + new_ops
    
    if operation not in valid_ops:
        errors.append(f"Change {i}: Invalid operation '{operation}' (must be one of {valid_ops})")
        return errors
    
    # Normalize replace_file to replace for downstream compatibility
    if operation == "replace_file":
        operation = "replace"
        change["operation"] = "replace"  # Update in place for applier
    
    # Validate required fields based on operation
    if operation in ["create", "replace"]:
        if "content" not in change:
            errors.append(f"Change {i}: Missing 'content' for {operation} operation")
    elif operation == "edit":
        if "edits" not in change:
            errors.append(f"Change {i}: Missing 'edits' for edit operation")
        elif not isinstance(change["edits"], list):
            errors.append(f"Change {i}: 'edits' must be a list")
    elif operation == "upsert_function_js":
        if not change.get("path"):
            errors.append(f"Change {i}: Missing 'path' for upsert_function_js operation")
        if "function_name" not in change:
            errors.append(f"Change {i}: Missing 'function_name' for upsert_function_js operation")
        if "content" not in change:
            errors.append(f"Change {i}: Missing 'content' (function body) for upsert_function_js operation")
    elif operation == "upsert_css_selector":
        if not change.get("path"):
            errors.append(f"Change {i}: Missing 'path' for upsert_css_selector operation")
        if "selector" not in change:
            errors.append(f"Change {i}: Missing 'selector' for upsert_css_selector operation")
        if "content" not in change:
            errors.append(f"Change {i}: Missing 'content' (CSS block) for upsert_css_selector operation")
    elif operation in ["insert_after_anchor", "insert_before_anchor"]:
        if not change.get("path"):
            errors.append(f"Change {i}: Missing 'path' for {operation} operation")
        if "anchor" not in change:
            errors.append(f"Change {i}: Missing 'anchor' for {operation} operation")
        if "content" not in change:
            errors.append(f"Change {i}: Missing 'content' for {operation} operation")
    elif operation == "append_if_missing":
        if not change.get("path"):
            errors.append(f"Change {i}: Missing 'path' for append_if_missing operation")
        if "content" not in change:
            errors.append(f"Change {i}: Missing 'content' for append_if_missing operation")
        if "signature" not in change:
            errors.append(f"Change {i}: Missing 'signature' for append_if_missing operation")
    elif operation == "replace_file":
        if not change.get("path"):
            errors.append(f"Change {i}: Missing 'path' for replace_file operation")
        if "content" not in change:
            errors.append(f"Change {i}: Missing 'content' for replace_file operation")
    
    return errors


def check_diff_markers(change: dict, i: int) -> list[str]:
    """
    Check for unified-diff markers in content fields only (not str(change)).
    Returns list of errors.
    """
    errors = []
    
    # Only scan content-like fields, not str(change)
    content_fields_to_check = []
    if "content" in change:
        content_fields_to_check.append(change["content"])
    if "before" in change:
        content_fields_to_check.append(change["before"])
    if "after" in change:
        content_fields_to_check.append(change["after"])
    
    # Check for unified-diff markers only in content fields
    diff_markers = ["diff --git", "--- a/", "+++ b/", "@@"]
    for content_field in content_fields_to_check:
        if isinstance(content_field, str):
            content_lower = content_field.lower()
            for marker in diff_markers:
                if marker in content_lower:
                    errors.append(f"Change {i}: Contains diff-like content in content field (rejecting - use structured format only). Found marker: '{marker}'")
                    break
            if any(marker in content_lower for marker in diff_markers):
                break
    
    return errors


def validate_structured_changes(changes_data: dict, work_dir: Path) -> tuple[bool, list[str]]:
    """
    Validate structured changes before applying.
    
    Schema normalization: Accepts both "path" and "file" fields, normalizes to "path".
    Repo allowlist: Prevents edits to non-existent files or files outside the repo.
    
    Returns (is_valid, error_messages)
    """
    errors = []
    
    if "error" in changes_data:
        return False, [changes_data["error"]]
    
    if "changes" not in changes_data:
        return False, ["Missing 'changes' key in structured changes"]
    
    # Build repo file allowlist
    repo_files = get_repo_file_allowlist(work_dir)
    
    for i, change in enumerate(changes_data["changes"]):
        # Schema normalization
        path, norm_errors = normalize_change_schema(change)
        errors.extend(norm_errors)
        if norm_errors:
            continue
        
        if "operation" not in change:
            errors.append(f"Change {i}: Missing 'operation'")
            continue
        operation = change["operation"]
        
        # Path safety validation
        if path:
            path_errors = validate_path_safety(path, work_dir, i)
            errors.extend(path_errors)
            if path_errors:
                continue
        
        # Check for diff markers
        diff_errors = check_diff_markers(change, i)
        errors.extend(diff_errors)
        if diff_errors:
            continue
        
        # Validate operation and required fields
        op_errors = validate_operation(change, operation, i)
        errors.extend(op_errors)
        if op_errors:
            continue
        
        # Validate file path against repo allowlist
        file_path = work_dir / path
        normalized_path = str(Path(path).as_posix())  # Normalize path separators
        
        # Operations that require existing files
        ops_requiring_existing = ["replace", "edit", "delete", "upsert_function_js", 
                                   "upsert_css_selector", "insert_after_anchor", 
                                   "insert_before_anchor", "append_if_missing"]
        
        # Check if file is in repo allowlist (for existing file operations)
        if operation in ops_requiring_existing:
            if normalized_path not in repo_files and not file_path.exists():
                # Try to find similar file (case-insensitive)
                found_similar = None
                path_lower = normalized_path.lower()
                for repo_file in repo_files:
                    if repo_file.lower() == path_lower:
                        found_similar = repo_file
                        break
                
                if found_similar:
                    errors.append(f"Change {i}: File '{path}' not found, but similar file exists: {found_similar}")
                else:
                    # Check if this looks like a backend/API hallucination
                    suspicious_patterns = ['api/', 'routes.js', 'controllers/', 'models/', 'backend/', 'server/']
                    if any(pattern in normalized_path.lower() for pattern in suspicious_patterns):
                        errors.append(f"Change {i}: File '{path}' does not exist and appears to be a backend/API file not in this repo. Only modify existing files in this repo.")
                    else:
                        errors.append(f"Change {i}: File '{path}' does not exist (for {operation} operation). Only modify existing files in this repo.")
        
        # For create operations, restrict to approved directories
        elif operation == "create":
            # Allow creation in test directories or explicitly allowed locations
            allowed_create_dirs = ['test', 'tests', 'spec', '__tests__']
            path_parts = Path(normalized_path).parts
            if path_parts:
                first_dir = path_parts[0].lower()
                if first_dir not in allowed_create_dirs:
                    # Check if plan explicitly allows this (would need plan context, but for now warn)
                    # In practice, we'll allow it but log a warning
                    pass  # Allow create but could add warning if needed
    
    return len(errors) == 0, errors
