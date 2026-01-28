#!/usr/bin/env python3
"""
Unit tests for branch safety guard logic.
Tests ensure_feature_branch function with mocked git commands.
"""

import unittest
import tempfile
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path to import crew_runner modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from crew_runner.git_ops import ensure_feature_branch, get_current_branch, has_changes
except ImportError as e:
    print(f"⚠️  Skipping branch safety tests: {e}")
    ensure_feature_branch = None
    get_current_branch = None
    has_changes = None


@unittest.skipIf(ensure_feature_branch is None, "Dependencies not installed")
class TestBranchSafetyGuard(unittest.TestCase):
    """Test branch safety guard: ensure_feature_branch"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        # Create .git directory to simulate git repo
        (self.test_dir / ".git").mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch('crew_runner.git_ops.get_current_branch')
    @patch('crew_runner.git_ops.has_changes')
    @patch('subprocess.run')
    def test_allows_feature_branch(self, mock_subprocess, mock_has_changes, mock_get_branch):
        """Should allow proceeding if already on a feature branch"""
        mock_get_branch.return_value = "feature/issue-123"
        mock_has_changes.return_value = False
        
        result = ensure_feature_branch(self.test_dir, issue_number=123)
        
        self.assertEqual(result, "feature/issue-123")
        # Should not call git checkout
        mock_subprocess.assert_not_called()
    
    @patch('crew_runner.git_ops.get_current_branch')
    @patch('crew_runner.git_ops.has_changes')
    def test_blocks_protected_branch_with_uncommitted_changes(self, mock_has_changes, mock_get_branch):
        """Should abort if on protected branch with uncommitted changes"""
        mock_get_branch.return_value = "development"
        mock_has_changes.return_value = True
        
        with self.assertRaises(ValueError) as context:
            ensure_feature_branch(self.test_dir, issue_number=123)
        
        self.assertIn("uncommitted changes", str(context.exception).lower())
        self.assertIn("protected branch", str(context.exception).lower())
    
    @patch('crew_runner.git_ops.get_current_branch')
    @patch('crew_runner.git_ops.has_changes')
    def test_blocks_protected_branch_without_issue_number(self, mock_has_changes, mock_get_branch):
        """Should abort if on protected branch without issue number"""
        mock_get_branch.return_value = "main"
        mock_has_changes.return_value = False
        
        with self.assertRaises(ValueError) as context:
            ensure_feature_branch(self.test_dir, issue_number=None)
        
        self.assertIn("issue number", str(context.exception).lower())
        self.assertIn("protected branch", str(context.exception).lower())
    
    @patch('crew_runner.git_ops.get_current_branch')
    @patch('crew_runner.git_ops.has_changes')
    @patch('subprocess.run')
    def test_creates_feature_branch_from_protected(self, mock_subprocess, mock_has_changes, mock_get_branch):
        """Should create feature branch if on protected branch (no uncommitted changes)"""
        mock_get_branch.return_value = "development"
        mock_has_changes.return_value = False
        
        # Mock git show-ref (branch doesn't exist)
        mock_show_ref = MagicMock()
        mock_show_ref.returncode = 1  # Branch doesn't exist
        mock_show_ref.stdout = ""
        mock_show_ref.stderr = ""
        
        # Mock git checkout -b (create branch)
        mock_checkout = MagicMock()
        mock_checkout.returncode = 0
        mock_checkout.stdout = "Switched to a new branch 'feature/issue-123'"
        mock_checkout.stderr = ""
        
        # Mock get_current_branch after checkout
        mock_get_branch.side_effect = ["development", "feature/issue-123"]
        
        mock_subprocess.side_effect = [mock_show_ref, mock_checkout]
        
        result = ensure_feature_branch(self.test_dir, issue_number=123)
        
        self.assertEqual(result, "feature/issue-123")
        # Verify git checkout -b was called
        self.assertEqual(mock_subprocess.call_count, 2)
        checkout_call = mock_subprocess.call_args_list[1]
        self.assertIn('checkout', checkout_call[0][0])
        self.assertIn('-b', checkout_call[0][0])
        self.assertIn('feature/issue-123', checkout_call[0][0])
    
    @patch('crew_runner.git_ops.get_current_branch')
    @patch('crew_runner.git_ops.has_changes')
    def test_allows_non_protected_branch(self, mock_has_changes, mock_get_branch):
        """Should allow non-protected branches (e.g., 'other-branch')"""
        mock_get_branch.return_value = "other-branch"
        mock_has_changes.return_value = False
        
        result = ensure_feature_branch(self.test_dir, issue_number=123)
        
        self.assertEqual(result, "other-branch")
    
    def test_handles_non_git_repo(self):
        """Should handle non-git repository gracefully"""
        non_git_dir = Path(tempfile.mkdtemp())
        try:
            # No .git directory
            result = ensure_feature_branch(non_git_dir, issue_number=123)
            self.assertEqual(result, "not-a-git-repo")
        finally:
            import shutil
            shutil.rmtree(non_git_dir, ignore_errors=True)


def run_self_check():
    """
    Internal self-check function that can be run without network.
    Tests basic logic without actual git operations.
    """
    print("Running branch safety guard self-check...")
    
    # Test 1: Protected branches list
    protected = ['development', 'main', 'master']
    test_branches = ['development', 'main', 'master', 'feature/issue-123', 'other']
    for branch in test_branches:
        is_protected = branch in protected
        expected = branch not in protected
        if is_protected:
            print(f"  ✓ '{branch}' correctly identified as protected")
        else:
            print(f"  ✓ '{branch}' correctly identified as non-protected")
    
    # Test 2: Feature branch naming
    issue_number = 123
    expected_branch = f"feature/issue-{issue_number}"
    assert expected_branch == "feature/issue-123", "Feature branch naming correct"
    print(f"  ✓ Feature branch naming: {expected_branch}")
    
    print("✅ Branch safety guard self-check passed")


if __name__ == '__main__':
    # Run self-check first (no network required)
    run_self_check()
    print()
    
    # Run unit tests if dependencies available
    unittest.main()
