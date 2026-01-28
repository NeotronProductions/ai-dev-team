"""
Parse implementation plan requirements: functions, CSS selectors, test files, etc.
"""

import re
from pathlib import Path


def parse_plan_requirements(plan_file: Path) -> dict:
    """
    Parse requirements from implementation plan file.
    Returns dict with: functions, css_selectors, test_files, required_files
    """
    requirements = {
        "functions": [],
        "css_selectors": [],
        "test_files": [],
        "required_files": []
    }
    
    if not plan_file.exists():
        return requirements
    
    try:
        content = plan_file.read_text(encoding='utf-8')
        
        # Extract functions from "New Functions/Classes/Modules" section
        func_section = re.search(r'###?\s*New Functions[^#]*', content, re.IGNORECASE | re.DOTALL)
        if func_section:
            func_text = func_section.group(0)
            # Look for function names like "functionName()" or "- functionName"
            func_matches = re.findall(r'[-*]\s*`?(\w+)\s*\([^)]*\)`?', func_text)
            requirements["functions"] = [f for f in func_matches if not f.startswith('function')]
        
        # Extract CSS selectors from "Files to Change" or "styles.css" mentions
        # Only treat CSS selectors as required if they start with ., #, or [
        # Prefer extracting selectors from backticks, fenced code blocks, or CSS declarations
        css_selectors = set()
        
        # Method 1: Extract from fenced code blocks (```css or ```)
        code_block_pattern = r'```(?:css)?\s*([^`]+)```'
        code_blocks = re.findall(code_block_pattern, content, re.IGNORECASE | re.DOTALL)
        for block in code_blocks:
            # Extract selectors from CSS code blocks
            selector_pattern = r'(?:^|\n)\s*([.#\[][\w-]+(?:\s*[.#\[][\w-]+)*(?:\s*\{)?)'
            matches = re.findall(selector_pattern, block, re.MULTILINE)
            for match in matches:
                # Clean up: remove trailing { and whitespace
                selector = match.strip().rstrip('{').strip()
                # Only accept if starts with ., #, or [
                if selector and (selector.startswith('.') or selector.startswith('#') or selector.startswith('[')):
                    css_selectors.add(selector)
        
        # Method 2: Extract from inline backticks (e.g., `.modal`, `#editModal`, `[data-id]`)
        # Handle attribute selectors like [data-id], [data-id="value"], etc.
        # Pattern matches: .class, #id, or [attribute] (with optional value)
        inline_backtick_pattern = r'`((?:[.#][\w-]+|\[[^\]]+\]))`'
        inline_matches = re.findall(inline_backtick_pattern, content)
        for match in inline_matches:
            selector = match.strip()
            # Only accept if starts with ., #, or [
            if selector and (selector.startswith('.') or selector.startswith('#') or selector.startswith('[')):
                css_selectors.add(selector)
        
        # Method 3: Extract from lines that look like CSS declarations
        css_declaration_pattern = r'(?:^|\n)\s*([.#\[][\w-]+(?:\s+[.#\[][\w-]+)*)\s*\{'
        declaration_matches = re.findall(css_declaration_pattern, content, re.MULTILINE)
        for match in declaration_matches:
            selector = match.strip()
            # Only accept if starts with ., #, or [
            if selector and (selector.startswith('.') or selector.startswith('#') or selector.startswith('[')):
                css_selectors.add(selector)
        
        # Method 4: Extract from bullet lists that mention selectors
        # Look for lines like "- Add `.modal` styles" or "- Style `#toast`" or "- Use `[data-id]` selector"
        # Pattern matches: .class, #id, or [attribute] (with optional value)
        bullet_pattern = r'[-*]\s+[^`]*`((?:[.#][\w-]+|\[[^\]]+\]))`'
        bullet_matches = re.findall(bullet_pattern, content)
        for match in bullet_matches:
            selector = match.strip()
            # Only accept if starts with ., #, or [
            if selector and (selector.startswith('.') or selector.startswith('#') or selector.startswith('[')):
                css_selectors.add(selector)
        
        # Debug logging on extraction
        if css_selectors:
            print(f"   Extracted {len(css_selectors)} CSS selector(s) from plan: {', '.join(sorted(css_selectors))}")
        
        requirements["css_selectors"] = sorted(list(css_selectors))
        
        # Extract test files from "Test Approach" or "Files to Change"
        test_section = re.search(r'Test Approach[^#]*|test[^#]*\.(js|ts|py)', content, re.IGNORECASE | re.DOTALL)
        if test_section:
            test_text = test_section.group(0)
            test_matches = re.findall(r'(test[/\\][\w/\\-]+\.(?:js|ts|py))', test_text)
            requirements["test_files"] = test_matches
        
        # Extract required files from "Files to Change" section
        files_section = re.search(r'###?\s*Files to Change[^#]*', content, re.IGNORECASE | re.DOTALL)
        if files_section:
            files_text = files_section.group(0)
            file_matches = re.findall(r'[-*]\s*`([^`]+)`', files_text)
            requirements["required_files"] = file_matches
        
    except Exception as e:
        print(f"⚠️  Warning: Could not parse plan requirements: {e}")
    
    return requirements
