#!/usr/bin/env python3
"""Test script to check project access at different levels"""

import os
import sys
from dotenv import load_dotenv
from github import Github
from github.Auth import Token

load_dotenv()

def test_project_access(repo_name):
    """Test accessing projects at different levels"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN not set")
        return
    
    g = Github(auth=Token(token))
    repo = g.get_repo(repo_name)
    org_name = repo_name.split('/')[0]
    
    print(f"🔍 Testing project access for: {repo_name}")
    print(f"   Organization/User: {org_name}")
    print()
    
    # Test repository projects
    print("1️⃣ Repository-level projects:")
    try:
        projects = list(repo.get_projects())
        print(f"   ✅ Found {len(projects)} project(s)")
        for p in projects:
            print(f"      - {p.name} (ID: {p.id}, URL: {p.html_url})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Test organization projects
    print("2️⃣ Organization-level projects:")
    try:
        org = g.get_organization(org_name)
        projects = list(org.get_projects())
        print(f"   ✅ Found {len(projects)} project(s)")
        for p in projects:
            print(f"      - {p.name} (ID: {p.id}, URL: {p.html_url})")
            # Check if this project contains the repo
            try:
                columns = list(p.get_columns())
                print(f"         Columns: {[c.name for c in columns]}")
            except:
                pass
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print()
    
    # Test user projects
    print("3️⃣ User-level projects:")
    try:
        user = g.get_user(org_name)
        projects = list(user.get_projects())
        print(f"   ✅ Found {len(projects)} project(s)")
        for p in projects:
            print(f"      - {p.name} (ID: {p.id}, URL: {p.html_url})")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_project_access.py <repo_name>")
        print("Example: python3 test_project_access.py NeotronProductions/Beautiful-Timetracker-App")
        sys.exit(1)
    
    test_project_access(sys.argv[1])
