#!/usr/bin/env python3
"""Test script to verify pipeline movement works"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from automated_crew import move_issue_in_project, get_github_client

def test_pipeline_movement(repo_name, issue_number):
    """Test moving an issue in the project pipeline"""
    print(f"🧪 Testing pipeline movement for issue #{issue_number}")
    print(f"   Repository: {repo_name}")
    print()
    
    # Test moving to "In Progress"
    print("1️⃣ Testing move to 'In Progress'...")
    result1 = move_issue_in_project(repo_name, issue_number, "In Progress")
    print(f"   Result: {'✅ Success' if result1 else '❌ Failed'}")
    print()
    
    # Wait a moment
    import time
    time.sleep(2)
    
    # Test moving to "Done"
    print("2️⃣ Testing move to 'Done'...")
    result2 = move_issue_in_project(repo_name, issue_number, "Done")
    print(f"   Result: {'✅ Success' if result2 else '❌ Failed'}")
    print()
    
    if result1 and result2:
        print("✅ Pipeline movement test PASSED!")
        return True
    else:
        print("❌ Pipeline movement test FAILED!")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 test_pipeline.py <repo_name> <issue_number>")
        print("Example: python3 test_pipeline.py NeotronProductions/Beautiful-Timetracker-App 724")
        sys.exit(1)
    
    repo_name = sys.argv[1]
    issue_number = int(sys.argv[2])
    
    # Check GitHub token
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ GITHUB_TOKEN not set in .env")
        sys.exit(1)
    
    test_pipeline_movement(repo_name, issue_number)
