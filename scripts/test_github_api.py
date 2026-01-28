#!/usr/bin/env python3
"""Test GitHub API access directly"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

def test_api_access(repo_name):
    """Test GitHub API access"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN not set")
        return
    
    org_name = repo_name.split('/')[0]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    print(f"🔍 Testing API access for: {repo_name}")
    print(f"   Organization/User: {org_name}")
    print()
    
    # Test 1: Repository info
    print("1️⃣ Repository info:")
    url = f"https://api.github.com/repos/{repo_name}"
    r = requests.get(url, headers=headers)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Repo: {data.get('full_name')}")
        print(f"   Owner: {data.get('owner', {}).get('login')} (type: {data.get('owner', {}).get('type')})")
    else:
        print(f"   ❌ Error: {r.text[:200]}")
    print()
    
    # Test 2: Organization projects (classic)
    print("2️⃣ Organization projects (classic):")
    url = f"https://api.github.com/orgs/{org_name}/projects"
    r = requests.get(url, headers=headers)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        projects = r.json()
        print(f"   ✅ Found {len(projects)} project(s)")
        for p in projects[:5]:  # Show first 5
            print(f"      - {p.get('name')} (ID: {p.get('id')}, State: {p.get('state')})")
    else:
        print(f"   ❌ Error: {r.text[:200]}")
    print()
    
    # Test 3: User projects (classic)
    print("3️⃣ User projects (classic):")
    url = f"https://api.github.com/users/{org_name}/projects"
    r = requests.get(url, headers=headers)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        projects = r.json()
        print(f"   ✅ Found {len(projects)} project(s)")
        for p in projects[:5]:
            print(f"      - {p.get('name')} (ID: {p.get('id')}, State: {p.get('state')})")
    else:
        print(f"   ❌ Error: {r.text[:200]}")
    print()
    
    # Test 4: Repository projects (classic)
    print("4️⃣ Repository projects (classic):")
    url = f"https://api.github.com/repos/{repo_name}/projects"
    r = requests.get(url, headers=headers)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        projects = r.json()
        print(f"   ✅ Found {len(projects)} project(s)")
        for p in projects[:5]:
            print(f"      - {p.get('name')} (ID: {p.get('id')}, State: {p.get('state')})")
    else:
        print(f"   ❌ Error: {r.text[:200]}")
    print()
    
    # Test 5: Check token scopes
    print("5️⃣ Token scopes:")
    url = "https://api.github.com/user"
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        # Check rate limit to see scopes
        rate_limit = r.headers.get('X-RateLimit-Limit', 'unknown')
        print(f"   Rate limit: {rate_limit}")
    # Check what scopes we have
    scopes = r.headers.get('X-OAuth-Scopes', '')
    print(f"   Scopes: {scopes if scopes else 'Not shown in headers'}")
    print()
    
    # Test 6: Try with legacy API format
    print("6️⃣ Organization projects (legacy API format):")
    headers_legacy = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.inertia-preview+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    url = f"https://api.github.com/orgs/{org_name}/projects"
    r = requests.get(url, headers=headers_legacy)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        projects = r.json()
        print(f"   ✅ Found {len(projects)} project(s)")
        for p in projects[:5]:
            print(f"      - {p.get('name')} (ID: {p.get('id')})")
    else:
        print(f"   ❌ Error: {r.text[:200]}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_github_api.py <repo_name>")
        sys.exit(1)
    
    test_api_access(sys.argv[1])
