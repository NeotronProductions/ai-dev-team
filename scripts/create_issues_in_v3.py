#!/usr/bin/env python3
"""
Script to create issues in Beautiful-Timetracker-App-V3 repository
by copying them from the original Beautiful-Timetracker-App repository
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from github import Github
from github.Auth import Token

# Load environment variables
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ GITHUB_TOKEN not found in environment")
    sys.exit(1)

# Repository names
SOURCE_REPO = "NeotronProductions/Beautiful-Timetracker-App"
TARGET_REPO = "NeotronProductions/Beautiful-Timetracker-App-V3"

def get_github_client():
    """Get GitHub client"""
    try:
        auth = Token(GITHUB_TOKEN)
        g = Github(auth=auth)
        return g
    except Exception as e:
        print(f"❌ Failed to create GitHub client: {e}")
        return None

def copy_issue(source_repo, target_repo, issue_number):
    """Copy an issue from source repo to target repo"""
    try:
        # Get the source issue
        try:
            source_issue = source_repo.get_issue(issue_number)
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "Not Found" in error_msg:
                print(f"❌ Issue #{issue_number} not found in {source_repo.full_name}")
            else:
                print(f"❌ Error accessing issue #{issue_number}: {e}")
            return None
        
        print(f"\n📋 Copying Issue #{source_issue.number}: {source_issue.title}")
        print(f"   From: {source_repo.full_name}")
        print(f"   To: {target_repo.full_name}")
        
        # Prepare issue body
        issue_body = f"""Copied from {source_repo.full_name}#{source_issue.number}

{source_issue.body or '(No description)'}

---
Original issue: {source_issue.html_url}
"""
        
        # Get labels
        label_names = [label.name for label in source_issue.labels]
        
        # Get assignees (only if not empty)
        assignee_logins = None
        if source_issue.assignees:
            assignee_logins = [assignee.login for assignee in source_issue.assignees]
        
        # Create issue in target repo
        try:
            # Build create_issue arguments
            create_kwargs = {
                'title': source_issue.title,
                'body': issue_body,
            }
            
            # Only add labels if they exist
            if label_names:
                create_kwargs['labels'] = label_names
            
            # Only add assignees if they exist and are not empty
            if assignee_logins:
                create_kwargs['assignees'] = assignee_logins
            
            new_issue = target_repo.create_issue(**create_kwargs)
            
            print(f"✅ Created Issue #{new_issue.number} in {target_repo.full_name}")
            print(f"   URL: {new_issue.html_url}")
            return new_issue
            
        except Exception as create_error:
            error_msg = str(create_error)
            if "422" in error_msg:
                print(f"❌ Failed to create issue (422): {error_msg}")
                print(f"   This might be due to:")
                print(f"   - Invalid labels (labels must exist in target repo)")
                print(f"   - Invalid assignees (users must have access to target repo)")
            else:
                print(f"❌ Error creating issue: {create_error}")
            import traceback
            traceback.print_exc()
            return None
        
    except Exception as e:
        print(f"❌ Unexpected error copying issue #{issue_number}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python create_issues_in_v3.py <issue_number> [issue_number2] ...")
        print("Example: python create_issues_in_v3.py 324")
        print("Example: python create_issues_in_v3.py 324 575 586 478")
        sys.exit(1)
    
    g = get_github_client()
    if not g:
        sys.exit(1)
    
    # Get repositories
    try:
        source_repo = g.get_repo(SOURCE_REPO)
        print(f"✓ Source repository: {source_repo.full_name}")
    except Exception as e:
        print(f"❌ Failed to access source repository {SOURCE_REPO}: {e}")
        sys.exit(1)
    
    try:
        target_repo = g.get_repo(TARGET_REPO)
        print(f"✓ Target repository: {target_repo.full_name}")
    except Exception as e:
        print(f"❌ Failed to access target repository {TARGET_REPO}: {e}")
        print(f"   Make sure the repository exists and you have write access")
        sys.exit(1)
    
    # Process issue numbers
    issue_numbers = [int(arg) for arg in sys.argv[1:]]
    
    print(f"\n{'='*70}")
    print(f"Copying {len(issue_numbers)} issue(s) from {SOURCE_REPO} to {TARGET_REPO}")
    print(f"{'='*70}\n")
    
    created_issues = []
    for issue_num in issue_numbers:
        new_issue = copy_issue(source_repo, target_repo, issue_num)
        if new_issue:
            created_issues.append(new_issue)
    
    print(f"\n{'='*70}")
    print(f"✅ Successfully created {len(created_issues)} issue(s)")
    print(f"{'='*70}")
    for issue in created_issues:
        print(f"  - Issue #{issue.number}: {issue.title}")
        print(f"    URL: {issue.html_url}")

if __name__ == "__main__":
    main()
