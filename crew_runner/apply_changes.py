"""
File operation helpers: pure, testable functions for applying structured changes.
"""

import re
from pathlib import Path
from typing import Tuple


def upsert_function_js(file_path: Path, function_name: str, function_body: str) -> bool:
    """
    Upsert a JavaScript function: replace if exists, append if not.
    Supports: function name(), const name = function(), const name = () =>
    Returns True if change was made (idempotent: returns False if content unchanged).
    """
    if not file_path.exists():
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # Try to find function definition (supports various formats)
    patterns = [
        # function name() { ... } - match entire function body
        rf'function\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{[^}}]*\}}',
        # const name = function() { ... }
        rf'const\s+{re.escape(function_name)}\s*=\s*function\s*\([^)]*\)\s*\{{[^}}]*\}}',
        # const name = () => { ... }
        rf'const\s+{re.escape(function_name)}\s*=\s*\([^)]*\)\s*=>\s*\{{[^}}]*\}}',
        # let name = function() { ... }
        rf'let\s+{re.escape(function_name)}\s*=\s*function\s*\([^)]*\)\s*\{{[^}}]*\}}',
        # let name = () => { ... }
        rf'let\s+{re.escape(function_name)}\s*=\s*\([^)]*\)\s*=>\s*\{{[^}}]*\}}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        if match:
            # Check if replacement would change content (idempotency check)
            existing_function = content[match.start():match.end()]
            if existing_function.strip() == function_body.strip():
                return False  # No change needed
            
            # Replace existing function
            new_content = content[:match.start()] + function_body + content[match.end():]
            file_path.write_text(new_content, encoding='utf-8')
            return True
    
    # Function not found - append at end
    if not content.endswith('\n'):
        content += '\n'
    content += '\n' + function_body + '\n'
    file_path.write_text(content, encoding='utf-8')
    return True


def upsert_css_selector(file_path: Path, selector: str, css_block: str) -> bool:
    """
    Upsert a CSS selector: replace if exists, append if not.
    Supports: .class, #id, element, element.class, etc.
    Returns True if change was made (idempotent: returns False if content unchanged).
    """
    if not file_path.exists():
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # Escape selector for regex (handle .class, #id, element, etc.)
    escaped_selector = re.escape(selector)
    
    # Try to find selector block (more robust matching)
    pattern = rf'{escaped_selector}\s*\{{[^}}]*\}}'
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
    
    if match:
        # Check if replacement would change content (idempotency check)
        existing_block = content[match.start():match.end()]
        if existing_block.strip() == css_block.strip():
            return False  # No change needed
        
        # Replace existing selector
        new_content = content[:match.start()] + css_block + content[match.end():]
        file_path.write_text(new_content, encoding='utf-8')
        return True
    
    # Selector not found - append at end
    if not content.endswith('\n'):
        content += '\n'
    content += '\n' + css_block + '\n'
    file_path.write_text(content, encoding='utf-8')
    return True


def insert_after_anchor(file_path: Path, anchor: str, content_to_insert: str, use_regex: bool = False) -> bool:
    """Insert content after an anchor string or regex pattern. Returns True if inserted."""
    if not file_path.exists():
        return False
    
    current_content = file_path.read_text(encoding='utf-8')
    
    if use_regex:
        match = re.search(anchor, current_content)
        if match:
            pos = match.end()
        else:
            return False
    else:
        pos = current_content.find(anchor)
        if pos == -1:
            return False
        pos += len(anchor)
    
    new_content = current_content[:pos] + '\n' + content_to_insert + current_content[pos:]
    file_path.write_text(new_content, encoding='utf-8')
    return True


def insert_before_anchor(file_path: Path, anchor: str, content_to_insert: str, use_regex: bool = False) -> bool:
    """Insert content before an anchor string or regex pattern. Returns True if inserted."""
    if not file_path.exists():
        return False
    
    current_content = file_path.read_text(encoding='utf-8')
    
    if use_regex:
        match = re.search(anchor, current_content)
        if match:
            pos = match.start()
        else:
            return False
    else:
        pos = current_content.find(anchor)
        if pos == -1:
            return False
    
    new_content = current_content[:pos] + content_to_insert + '\n' + current_content[pos:]
    file_path.write_text(new_content, encoding='utf-8')
    return True


def append_if_missing(file_path: Path, content_to_append: str, signature: str) -> bool:
    """Append content only if signature is not present. Returns True if appended."""
    if not file_path.exists():
        # Create file with content
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content_to_append, encoding='utf-8')
        return True
    
    current_content = file_path.read_text(encoding='utf-8')
    
    if signature in current_content:
        return False  # Already present
    
    if not current_content.endswith('\n'):
        current_content += '\n'
    current_content += content_to_append + '\n'
    file_path.write_text(current_content, encoding='utf-8')
    return True


def apply_structured_changes(changes_data: dict, work_dir: Path) -> Tuple[bool, list[str], list[str]]:
    """
    Apply structured changes directly to files with robust fallbacks.
    Returns (success, changed_files, error_messages)
    Deduplication: tracks files in a set to avoid duplicates.
    Idempotency: only reports files that actually changed.
    """
    changed_files_set = set()  # Use set to dedupe
    errors = []
    warnings = []
    
    if "error" in changes_data:
        return False, [], [changes_data["error"]]
    
    for change in changes_data.get("changes", []):
        # Schema normalization: accept both "path" and "file"
        path = change.get("path") or change.get("file")
        if not path:
            errors.append("Change missing 'path' or 'file' field")
            continue
        
        # Normalize in place
        change["path"] = path
        if "file" in change:
            del change["file"]  # Remove duplicate field
        
        operation = change.get("operation", "replace")  # Default to replace
        file_path = work_dir / path
        
        try:
            if operation == "create":
                # Create new file
                file_path.parent.mkdir(parents=True, exist_ok=True)
                content = change.get("content", "")
                if file_path.exists():
                    warnings.append(f"File {path} already exists, overwriting (create operation)")
                file_path.write_text(content, encoding='utf-8')
                changed_files_set.add(path)  # Use set to dedupe
                print(f"✓ Created file: {path}")
                
            elif operation == "replace_file" or operation == "replace":
                # Replace entire file content
                if not file_path.exists():
                    errors.append(f"File not found for replace: {path}")
                    continue
                content = change.get("content", "")
                # Idempotency: check if content actually changed
                if file_path.exists():
                    current_content = file_path.read_text(encoding='utf-8')
                    if current_content == content:
                        print(f"ℹ️  File {path} already matches replacement content (no changes needed)")
                        continue
                file_path.write_text(content, encoding='utf-8')
                changed_files_set.add(path)  # Use set to dedupe
                print(f"✓ Replaced file: {path}")
                
            elif operation == "edit":
                # Apply targeted edits with fallbacks
                if not file_path.exists():
                    errors.append(f"File not found for edit: {path}")
                    continue
                
                current_content = file_path.read_text(encoding='utf-8')
                new_content = current_content
                edit_success = False
                
                edits = change.get("edits", [])
                for edit in edits:
                    find_text = edit.get("find", "")
                    replace_text = edit.get("replace", "")
                    
                    # Try exact match first
                    if find_text in new_content:
                        new_content = new_content.replace(find_text, replace_text, 1)
                        edit_success = True
                    else:
                        # Try regex anchor
                        try:
                            pattern = re.compile(re.escape(find_text), re.MULTILINE | re.DOTALL)
                            if pattern.search(new_content):
                                new_content = pattern.sub(replace_text, new_content, count=1)
                                edit_success = True
                                warnings.append(f"Used regex fallback for edit in {path}")
                            else:
                                errors.append(f"Could not find anchor in {path}: {find_text[:50]}...")
                        except:
                            errors.append(f"Invalid regex pattern in {path}: {find_text[:50]}...")
                
                if edit_success and new_content != current_content:
                    file_path.write_text(new_content, encoding='utf-8')
                    changed_files_set.add(path)  # Use set to dedupe
                    print(f"✓ Edited file: {path}")
                elif not edit_success:
                    errors.append(f"No changes applied to {path} (all find texts not found)")
                    
            elif operation == "insert_after_anchor":
                anchor = change.get("anchor", "")
                content_to_insert = change.get("content", "")
                use_regex = change.get("use_regex", False)
                
                if insert_after_anchor(file_path, anchor, content_to_insert, use_regex):
                    changed_files_set.add(path)  # Use set to dedupe
                    print(f"✓ Inserted content after anchor in {path}")
                else:
                    errors.append(f"Could not find anchor in {path}: {anchor[:50]}...")
                    
            elif operation == "insert_before_anchor":
                anchor = change.get("anchor", "")
                content_to_insert = change.get("content", "")
                use_regex = change.get("use_regex", False)
                
                if insert_before_anchor(file_path, anchor, content_to_insert, use_regex):
                    changed_files_set.add(path)  # Use set to dedupe
                    print(f"✓ Inserted content before anchor in {path}")
                else:
                    errors.append(f"Could not find anchor in {path}: {anchor[:50]}...")
                    
            elif operation == "append_if_missing":
                content_to_append = change.get("content", "")
                signature = change.get("signature", "")
                
                # Idempotency: append_if_missing already returns False if signature exists
                if append_if_missing(file_path, content_to_append, signature):
                    changed_files_set.add(path)  # Use set to dedupe
                    print(f"✓ Appended content to {path}")
                else:
                    print(f"ℹ️  Content already present in {path} (signature found)")
                    
            elif operation == "upsert_function_js":
                function_name = change.get("function_name", "")
                function_body = change.get("content", "")
                
                if not function_name:
                    errors.append(f"Missing function_name for upsert_function_js in {path}")
                    continue
                
                # Idempotency: only add to changed_files if content actually changed
                if upsert_function_js(file_path, function_name, function_body):
                    changed_files_set.add(path)  # Use set to dedupe
                    print(f"✓ Upserted function {function_name} in {path}")
                else:
                    print(f"ℹ️  Function {function_name} in {path} already up-to-date (no changes needed)")
                    
            elif operation == "upsert_css_selector":
                selector = change.get("selector", "")
                css_block = change.get("content", "")
                
                if not selector:
                    errors.append(f"Missing selector for upsert_css_selector in {path}")
                    continue
                
                # Idempotency: only add to changed_files if content actually changed
                if upsert_css_selector(file_path, selector, css_block):
                    changed_files_set.add(path)  # Use set to dedupe
                    print(f"✓ Upserted CSS selector {selector} in {path}")
                else:
                    print(f"ℹ️  CSS selector {selector} in {path} already up-to-date (no changes needed)")
                    
            elif operation == "delete":
                # Delete file
                if not file_path.exists():
                    errors.append(f"File not found for delete: {path}")
                    continue
                file_path.unlink()
                changed_files_set.add(path)  # Use set to dedupe
                print(f"✓ Deleted file: {path}")
            else:
                # This should not happen if validator is working correctly
                errors.append(f"Unknown operation '{operation}' for {path}. Supported: create, replace, replace_file, edit, upsert_function_js, upsert_css_selector, insert_after_anchor, insert_before_anchor, append_if_missing, delete")
                
        except Exception as e:
            errors.append(f"Error applying change to {path}: {str(e)}")
    
    # Print warnings
    for warning in warnings:
        print(f"⚠️  {warning}")
    
    # Convert set to sorted list for consistent output
    changed_files = sorted(list(changed_files_set))
    return len(errors) == 0, changed_files, errors
