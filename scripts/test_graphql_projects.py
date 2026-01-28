#!/usr/bin/env python3
"""Test GitHub GraphQL API for projects"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_graphql_projects(repo_name):
    """Test GraphQL API for projects"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN not set")
        return
    
    org_name = repo_name.split('/')[0]
    repo_name_only = repo_name.split('/')[1]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    url = "https://api.github.com/graphql"
    
    print(f"🔍 Testing GraphQL API for: {repo_name}")
    print()
    
    # Query 1: Get repository and its projects
    query1 = """
    query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        name
        projectsV2(first: 10) {
          nodes {
            id
            title
            number
            url
            public
          }
        }
      }
    }
    """
    
    variables1 = {
        "owner": org_name,
        "repo": repo_name_only
    }
    
    print("1️⃣ Repository projects (GraphQL Projects V2):")
    r = requests.post(url, headers=headers, json={"query": query1, "variables": variables1})
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if 'errors' in data:
            print(f"   ❌ GraphQL Errors: {data['errors']}")
        else:
            repo_data = data.get('data', {}).get('repository', {})
            projects = repo_data.get('projectsV2', {}).get('nodes', [])
            print(f"   ✅ Found {len(projects)} project(s)")
            for p in projects:
                print(f"      - {p.get('title')} (ID: {p.get('id')}, Number: {p.get('number')})")
    else:
        print(f"   ❌ Error: {r.text[:300]}")
    print()
    
    # Query 2: Get user's projects
    query2 = """
    query($login: String!) {
      user(login: $login) {
        login
        projectsV2(first: 10) {
          nodes {
            id
            title
            number
            url
            public
          }
        }
      }
    }
    """
    
    variables2 = {
        "login": org_name
    }
    
    print("2️⃣ User projects (GraphQL Projects V2):")
    r = requests.post(url, headers=headers, json={"query": query2, "variables": variables2})
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if 'errors' in data:
            print(f"   ❌ GraphQL Errors: {data['errors']}")
        else:
            user_data = data.get('data', {}).get('user', {})
            if user_data:
                projects = user_data.get('projectsV2', {}).get('nodes', [])
                print(f"   ✅ Found {len(projects)} project(s)")
                for p in projects:
                    print(f"      - {p.get('title')} (ID: {p.get('id')}, Number: {p.get('number')})")
            else:
                print(f"   ⚠ User not found or not accessible")
    else:
        print(f"   ❌ Error: {r.text[:300]}")
    print()
    
    # Query 3: Get organization projects (in case it's actually an org)
    query3 = """
    query($login: String!) {
      organization(login: $login) {
        login
        projectsV2(first: 10) {
          nodes {
            id
            title
            number
            url
            public
          }
        }
      }
    }
    """
    
    print("3️⃣ Organization projects (GraphQL Projects V2):")
    r = requests.post(url, headers=headers, json={"query": query3, "variables": variables2})
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if 'errors' in data:
            errors = data.get('errors', [])
            if any('Could not resolve' in str(e) for e in errors):
                print(f"   ℹ️  Not an organization (this is expected if it's a user account)")
            else:
                print(f"   ❌ GraphQL Errors: {errors}")
        else:
            org_data = data.get('data', {}).get('organization', {})
            if org_data:
                projects = org_data.get('projectsV2', {}).get('nodes', [])
                print(f"   ✅ Found {len(projects)} project(s)")
                for p in projects:
                    print(f"      - {p.get('title')} (ID: {p.get('id')}, Number: {p.get('number')})")
    else:
        print(f"   ❌ Error: {r.text[:300]}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_graphql_projects.py <repo_name>")
        sys.exit(1)
    
    test_graphql_projects(sys.argv[1])
