#!/usr/bin/env python3
"""Quick test to verify GitHub token is working"""

import os
from dotenv import load_dotenv
from crewai_tools import GithubSearchTool

load_dotenv()

token = os.getenv("GITHUB_TOKEN")
if not token:
    print("❌ GITHUB_TOKEN not found")
    exit(1)

print("🔍 Testing GitHub connection...")
print(f"Token: {token[:7]}...{token[-4:]}")
print("")

# Test with a public repo
test_repo = "crewAIInc/crewAI"
print(f"Testing with repository: {test_repo}")

try:
    tool = GithubSearchTool(
        github_repo=f"https://github.com/{test_repo}",
        gh_token=token,
        content_types=['issue']
    )
    print("✓ GithubSearchTool initialized successfully")
    print("✓ Your GitHub token is valid and working!")
    print("")
    print("You can now use:")
    print("  python3 example_github_issue.py owner/repo [issue_number]")
    print("  python3 github_crew.py <issue_number> [repo]")
except Exception as e:
    print(f"❌ Error: {e}")
    print("Please check your token has the correct permissions (repo, read:org)")
