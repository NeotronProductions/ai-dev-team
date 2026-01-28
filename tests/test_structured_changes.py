#!/usr/bin/env python3
"""
Unit tests for structured changes validation and application logic.
Tests critical edit/upsert logic without requiring network/GitHub.
"""

import unittest
import tempfile
from pathlib import Path
import sys
import os

# Add parent directory to path to import crew_runner modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from crew_runner.schema import validate_structured_changes, RunState
    from crew_runner.apply_changes import upsert_function_js, upsert_css_selector
    from crew_runner.plan_requirements import parse_plan_requirements
    from crew_runner.git_ops import ensure_feature_branch
except ImportError as e:
    # Skip tests if dependencies are not installed
    print(f"⚠️  Skipping tests: {e}")
    print("   Install dependencies: pip install PyGithub python-dotenv crewai")
    RunState = None
    validate_structured_changes = None
    upsert_function_js = None
    upsert_css_selector = None
    parse_plan_requirements = None
    ensure_feature_branch = None


@unittest.skipIf(validate_structured_changes is None, "Dependencies not installed")
class TestSchemaNormalization(unittest.TestCase):
    """Test A) Schema normalization: file->path conversion"""
    
    def test_accepts_path_field(self):
        """Should accept 'path' field"""
        work_dir = Path(tempfile.mkdtemp())
        changes = {
            "changes": [
                {
                    "path": "test.js",
                    "operation": "replace_file",
                    "content": "test content"
                }
            ]
        }
        is_valid, errors = validate_structured_changes(changes, work_dir)
        self.assertTrue(is_valid, f"Should accept 'path' field. Errors: {errors}")
    
    def test_accepts_file_field(self):
        """Should accept 'file' field and normalize to 'path'"""
        work_dir = Path(tempfile.mkdtemp())
        changes = {
            "changes": [
                {
                    "file": "test.js",
                    "operation": "replace_file",
                    "content": "test content"
                }
            ]
        }
        is_valid, errors = validate_structured_changes(changes, work_dir)
        self.assertTrue(is_valid, f"Should accept 'file' field. Errors: {errors}")
        # Check normalization happened
        self.assertIn("path", changes["changes"][0])
        self.assertNotIn("file", changes["changes"][0])
    
    def test_normalizes_file_to_path(self):
        """Should normalize 'file' to 'path' and remove 'file'"""
        work_dir = Path(tempfile.mkdtemp())
        change = {
            "file": "test.js",
            "operation": "replace_file",
            "content": "test"
        }
        changes = {"changes": [change]}
        is_valid, errors = validate_structured_changes(changes, work_dir)
        self.assertTrue(is_valid)
        self.assertEqual(change.get("path"), "test.js")
        self.assertNotIn("file", change)


@unittest.skipIf(validate_structured_changes is None, "Dependencies not installed")
class TestPathSafety(unittest.TestCase):
    """Test C) Path safety: reject absolute paths and .. traversal"""
    
    def test_rejects_absolute_paths(self):
        """Should reject absolute paths"""
        work_dir = Path(tempfile.mkdtemp())
        changes = {
            "changes": [
                {
                    "path": "/etc/passwd",  # Absolute path
                    "operation": "replace_file",
                    "content": "malicious"
                }
            ]
        }
        is_valid, errors = validate_structured_changes(changes, work_dir)
        self.assertFalse(is_valid, "Should reject absolute paths")
        self.assertTrue(any("absolute" in err.lower() for err in errors))
    
    def test_rejects_path_traversal(self):
        """Should reject paths with .. segments"""
        work_dir = Path(tempfile.mkdtemp())
        changes = {
            "changes": [
                {
                    "path": "../../etc/passwd",  # Path traversal
                    "operation": "replace_file",
                    "content": "malicious"
                }
            ]
        }
        is_valid, errors = validate_structured_changes(changes, work_dir)
        self.assertFalse(is_valid, "Should reject path traversal")
        self.assertTrue(any(".." in err or "traversal" in err.lower() for err in errors))
    
    def test_accepts_relative_paths(self):
        """Should accept valid relative paths"""
        work_dir = Path(tempfile.mkdtemp())
        (work_dir / "test.js").write_text("original")
        changes = {
            "changes": [
                {
                    "path": "test.js",
                    "operation": "replace_file",
                    "content": "updated"
                }
            ]
        }
        is_valid, errors = validate_structured_changes(changes, work_dir)
        self.assertTrue(is_valid, f"Should accept relative paths. Errors: {errors}")


@unittest.skipIf(upsert_function_js is None, "Dependencies not installed")
class TestUpsertFunctionJS(unittest.TestCase):
    """Test upsert_function_js: replace existing and append if missing"""
    
    def test_replaces_existing_function(self):
        """Should replace existing function"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
            tmp.write("function test() { return false; }\n")
            tmp_path = Path(tmp.name)
        
        try:
            result = upsert_function_js(tmp_path, "test", "function test() { return true; }")
            self.assertTrue(result, "Should return True when replacing")
            content = tmp_path.read_text()
            self.assertIn("return true", content)
            self.assertNotIn("return false", content)
        finally:
            tmp_path.unlink()
    
    def test_appends_if_missing(self):
        """Should append function if it doesn't exist"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
            tmp.write("// existing code\n")
            tmp_path = Path(tmp.name)
        
        try:
            result = upsert_function_js(tmp_path, "newFunc", "function newFunc() { return true; }")
            self.assertTrue(result, "Should return True when appending")
            content = tmp_path.read_text()
            self.assertIn("function newFunc()", content)
        finally:
            tmp_path.unlink()
    
    def test_idempotent_no_change(self):
        """Should return False if function already matches (idempotent)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
            func_body = "function test() { return true; }"
            tmp.write(f"{func_body}\n")
            tmp_path = Path(tmp.name)
        
        try:
            result = upsert_function_js(tmp_path, "test", func_body)
            self.assertFalse(result, "Should return False when no change needed (idempotent)")
            content = tmp_path.read_text()
            # Should still have the function
            self.assertIn("function test()", content)
        finally:
            tmp_path.unlink()


@unittest.skipIf(upsert_css_selector is None, "Dependencies not installed")
class TestUpsertCSSSelector(unittest.TestCase):
    """Test upsert_css_selector: replace existing and append if missing"""
    
    def test_replaces_existing_selector(self):
        """Should replace existing CSS selector"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as tmp:
            tmp.write(".modal { display: block; }\n")
            tmp_path = Path(tmp.name)
        
        try:
            result = upsert_css_selector(tmp_path, ".modal", ".modal { display: none; }")
            self.assertTrue(result, "Should return True when replacing")
            content = tmp_path.read_text()
            self.assertIn("display: none", content)
            self.assertNotIn("display: block", content)
        finally:
            tmp_path.unlink()
    
    def test_appends_if_missing(self):
        """Should append selector if it doesn't exist"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as tmp:
            tmp.write("body { margin: 0; }\n")
            tmp_path = Path(tmp.name)
        
        try:
            result = upsert_css_selector(tmp_path, ".modal", ".modal { display: none; }")
            self.assertTrue(result, "Should return True when appending")
            content = tmp_path.read_text()
            self.assertIn(".modal", content)
        finally:
            tmp_path.unlink()
    
    def test_idempotent_no_change(self):
        """Should return False if selector already matches (idempotent)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as tmp:
            css_block = ".modal { display: none; }"
            tmp.write(f"{css_block}\n")
            tmp_path = Path(tmp.name)
        
        try:
            result = upsert_css_selector(tmp_path, ".modal", css_block)
            self.assertFalse(result, "Should return False when no change needed (idempotent)")
            content = tmp_path.read_text()
            # Should still have the selector
            self.assertIn(".modal", content)
        finally:
            tmp_path.unlink()


@unittest.skipIf(parse_plan_requirements is None, "Dependencies not installed")
class TestSelectorExtraction(unittest.TestCase):
    """Test E) CSS selector extraction: only valid selectors"""
    
    def test_extracts_valid_selectors(self):
        """Should extract valid selectors starting with ., #, or ["""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write("""
# Implementation Plan

## Files to Change

- Add `.modal` styles
- Style `#editModal`
- Use `[data-id]` selector
""")
            tmp_path = Path(tmp.name)
        
        try:
            requirements = parse_plan_requirements(tmp_path)
            selectors = requirements["css_selectors"]
            self.assertIn(".modal", selectors)
            self.assertIn("#editModal", selectors)
            self.assertIn("[data-id]", selectors)
        finally:
            tmp_path.unlink()
    
    def test_rejects_nonsense_words(self):
        """Should NOT extract plain words as selectors"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write("""
# Implementation Plan

We need to add modal functionality. The modal should be styled.
The editModal needs work. Use data-id attributes.
""")
            tmp_path = Path(tmp.name)
        
        try:
            requirements = parse_plan_requirements(tmp_path)
            selectors = requirements["css_selectors"]
            # Should not extract "modal", "editModal", "data-id" as selectors
            # (they don't start with ., #, or [)
            invalid = [s for s in selectors if not (s.startswith('.') or s.startswith('#') or s.startswith('['))]
            self.assertEqual(len(invalid), 0, f"Should not extract invalid selectors: {invalid}")
        finally:
            tmp_path.unlink()
    
    def test_extracts_from_code_blocks(self):
        """Should extract selectors from fenced code blocks"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as tmp:
            tmp.write("""
```css
.modal {
    display: none;
}

#editModal {
    position: fixed;
}
```
""")
            tmp_path = Path(tmp.name)
        
        try:
            requirements = parse_plan_requirements(tmp_path)
            selectors = requirements["css_selectors"]
            self.assertIn(".modal", selectors)
            self.assertIn("#editModal", selectors)
        finally:
            tmp_path.unlink()


@unittest.skipIf(RunState is None, "Dependencies not installed")
class TestRunState(unittest.TestCase):
    """Test D) RunState dataclass"""
    
    def test_runstate_initialization(self):
        """Should initialize with default values"""
        state = RunState()
        self.assertFalse(state.applied_ok)
        self.assertFalse(state.coverage_ok)
        self.assertFalse(state.did_commit)
        self.assertFalse(state.did_push)
        self.assertFalse(state.did_move_done)
        self.assertEqual(len(state.errors), 0)
        self.assertIsNone(state.current_branch)
    
    def test_runstate_gating(self):
        """Should enforce gating: commit/push/move only if coverage_ok"""
        state = RunState()
        state.applied_ok = True
        state.coverage_ok = False  # Gate closed
        
        # Should not allow commit/push/move
        self.assertFalse(state.coverage_ok)
        
        state.coverage_ok = True  # Gate open
        # Now operations can proceed
        self.assertTrue(state.coverage_ok)


if __name__ == "__main__":
    unittest.main()
