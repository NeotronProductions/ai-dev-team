"""
Coverage checking: verify implementation plan requirements are met.
"""

import re
from pathlib import Path
from .plan_requirements import parse_plan_requirements


def check_coverage(plan_file: Path, work_dir: Path) -> tuple[bool, dict]:
    """
    Check if implementation plan requirements are met.
    Returns (is_complete, missing_items_dict)
    """
    requirements = parse_plan_requirements(plan_file)
    missing = {
        "functions": [],
        "css_selectors": [],
        "test_files": [],
        "required_files": []
    }
    
    # Check required functions in JS files
    for func_name in requirements["functions"]:
        found = False
        # Check common JS files
        for js_file in ["app.js", "index.js", "main.js"]:
            js_path = work_dir / js_file
            if js_path.exists():
                content = js_path.read_text(encoding='utf-8')
                # Look for function definition
                patterns = [
                    rf'function\s+{re.escape(func_name)}\s*\(',
                    rf'const\s+{re.escape(func_name)}\s*=',
                    rf'let\s+{re.escape(func_name)}\s*=',
                    rf'var\s+{re.escape(func_name)}\s*='
                ]
                for pattern in patterns:
                    if re.search(pattern, content):
                        found = True
                        break
                if found:
                    break
        if not found:
            missing["functions"].append(func_name)
    
    # Check CSS selectors
    css_path = work_dir / "styles.css"
    
    # Filter out invalid/garbage selectors before checking
    valid_selectors = [s for s in requirements["css_selectors"] 
                      if s and (s.startswith('.') or s.startswith('#') or s.startswith('['))]
    
    if valid_selectors:
        print(f"   Checking {len(valid_selectors)} CSS selector(s): {', '.join(valid_selectors)}")
    
    if css_path.exists():
        css_content = css_path.read_text(encoding='utf-8')
        for selector in valid_selectors:
            # Check for selector in CSS file
            # Handle compound selectors (e.g., ".modal .close" -> match ".modal" and ".close")
            selector_parts = selector.split()
            all_found = True
            
            for part in selector_parts:
                # Each part should start with . or #
                if part.startswith('.'):
                    pattern = rf'\{re.escape(part)}\s*\{{'
                elif part.startswith('#'):
                    pattern = rf'\{re.escape(part)}\s*\{{'
                else:
                    # Skip invalid parts
                    all_found = False
                    break
                
                if not re.search(pattern, css_content, re.MULTILINE):
                    all_found = False
                    break
            
            if not all_found:
                missing["css_selectors"].append(selector)
    else:
        # If CSS file doesn't exist but selectors are required, mark all as missing
        if valid_selectors:
            missing["css_selectors"] = valid_selectors
    
    # Check test files
    for test_file in requirements["test_files"]:
        test_path = work_dir / test_file
        if not test_path.exists():
            missing["test_files"].append(test_file)
    
    # Check required files
    for req_file in requirements["required_files"]:
        req_path = work_dir / req_file
        if not req_path.exists():
            missing["required_files"].append(req_file)
    
    # Determine if complete
    is_complete = (
        len(missing["functions"]) == 0 and
        len(missing["css_selectors"]) == 0 and
        len(missing["test_files"]) == 0 and
        len(missing["required_files"]) == 0
    )
    
    return is_complete, missing
