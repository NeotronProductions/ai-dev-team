#!/usr/bin/env python3
"""Test script to check project field options"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def check_project_fields(repo_name):
    """Check what fields and options exist in the project"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ GITHUB_TOKEN not set")
        return
    
    org_name = repo_name.split('/')[0]
    repo_name_only = repo_name.split('/')[1]
    
    graphql_url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    # Query for repository projects V2 with fields
    query = """
    query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        projectsV2(first: 10) {
          nodes {
            id
            title
            number
            fields(first: 20) {
              nodes {
                ... on ProjectV2SingleSelectField {
                  id
                  name
                  options {
                    id
                    name
                  }
                }
                ... on ProjectV2Field {
                  id
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    
    variables = {
        "owner": org_name,
        "repo": repo_name_only
    }
    
    response = requests.post(graphql_url, headers=headers, json={"query": query, "variables": variables})
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"❌ GraphQL Errors: {data['errors']}")
            return
        
        projects_v2 = data.get('data', {}).get('repository', {}).get('projectsV2', {}).get('nodes', [])
        if projects_v2:
            project = projects_v2[0]
            print(f"📋 Project: {project.get('title')} (ID: {project.get('id')})")
            print(f"\n📊 Fields:")
            
            fields = project.get('fields', {}).get('nodes', [])
            for field in fields:
                field_name = field.get('name', 'Unknown')
                field_id = field.get('id', 'Unknown')
                print(f"\n  Field: {field_name} (ID: {field_id})")
                
                if 'options' in field:
                    options = field.get('options', [])
                    print(f"    Type: Single Select")
                    print(f"    Options ({len(options)}):")
                    for opt in options:
                        print(f"      - {opt.get('name')} (ID: {opt.get('id')})")
                else:
                    print(f"    Type: {type(field).__name__}")
        else:
            print("❌ No projects found")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(response.text[:500])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_project_fields.py <repo_name>")
        print("Example: python3 test_project_fields.py NeotronProductions/Beautiful-Timetracker-App")
        sys.exit(1)
    
    check_project_fields(sys.argv[1])
