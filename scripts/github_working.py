#!/usr/bin/env python3
"""
GitHub Issue Fetcher and Analyzer - Works without LLM
Fetches GitHub issues and provides structured analysis
"""

import os
import sys
from dotenv import load_dotenv
from github import Github
from github.Auth import Token

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN not found in .env file")
    sys.exit(1)

def get_issue_info(repo_name, issue_number):
    """Get comprehensive issue information"""
    auth = Token(GITHUB_TOKEN)
    g = Github(auth=auth)
    
    try:
        repo = g.get_repo(repo_name)
        issue = repo.get_issue(issue_number)
        
        # Get comments
        comments = []
        for comment in issue.get_comments():
            comments.append({
                "author": comment.user.login,
                "body": comment.body,
                "created": str(comment.created_at)
            })
        
        # Get labels
        labels = [label.name for label in issue.labels]
        
        # Get assignees
        assignees = [assignee.login for assignee in issue.assignees]
        
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body or "(No description provided)",
            "state": issue.state,
            "labels": labels,
            "assignees": assignees,
            "created_at": str(issue.created_at),
            "updated_at": str(issue.updated_at),
            "url": issue.html_url,
            "comments": comments,
            "comments_count": len(comments),
            "is_pull_request": issue.pull_request is not None
        }
    except Exception as e:
        print(f"❌ Error fetching issue: {e}")
        return None

def analyze_issue_basic(issue_info):
    """Basic analysis without LLM"""
    analysis = {
        "summary": issue_info['title'],
        "type": "Pull Request" if issue_info['is_pull_request'] else "Issue",
        "status": issue_info['state'].upper(),
        "priority_indicators": [],
        "action_items": []
    }
    
    # Analyze labels for priority
    labels = issue_info['labels']
    if any('bug' in label.lower() for label in labels):
        analysis['priority_indicators'].append("🐛 Bug identified")
    if any('urgent' in label.lower() or 'critical' in label.lower() for label in labels):
        analysis['priority_indicators'].append("⚠️  High priority")
    if any('enhancement' in label.lower() or 'feature' in label.lower() for label in labels):
        analysis['priority_indicators'].append("✨ Feature request")
    
    # Extract action items from description
    body = issue_info['body']
    if body:
        lines = body.split('\n')
        for line in lines:
            if line.strip().startswith('- [ ]') or line.strip().startswith('* [ ]'):
                analysis['action_items'].append(line.strip())
            elif line.strip().startswith('-') or line.strip().startswith('*'):
                if 'todo' in line.lower() or 'fix' in line.lower() or 'implement' in line.lower():
                    analysis['action_items'].append(line.strip())
    
    return analysis

def display_results(issue_info, analysis):
    """Display formatted results"""
    print(f"\n{'='*70}")
    print(f"📋 {analysis['type']} #{issue_info['number']}: {analysis['summary']}")
    print(f"{'='*70}\n")
    
    print(f"🔗 URL: {issue_info['url']}")
    print(f"📊 Status: {analysis['status']}")
    
    if issue_info['labels']:
        print(f"🏷️  Labels: {', '.join(issue_info['labels'])}")
    
    if issue_info['assignees']:
        print(f"👤 Assignees: {', '.join(issue_info['assignees'])}")
    elif issue_info['assignees'] == []:
        print(f"👤 Assignees: (Unassigned)")
    
    print(f"📅 Created: {issue_info['created_at']}")
    print(f"🔄 Updated: {issue_info['updated_at']}")
    print(f"💬 Comments: {issue_info['comments_count']}")
    
    if analysis['priority_indicators']:
        print(f"\n{'─'*70}")
        print("🎯 Priority Indicators:")
        for indicator in analysis['priority_indicators']:
            print(f"   {indicator}")
    
    print(f"\n{'─'*70}")
    print("📝 Description:")
    print(f"{'─'*70}")
    print(issue_info['body'])
    
    if analysis['action_items']:
        print(f"\n{'─'*70}")
        print("✅ Action Items Found:")
        for item in analysis['action_items'][:10]:  # Limit to 10
            print(f"   • {item}")
    
    if issue_info['comments']:
        print(f"\n{'─'*70}")
        print(f"💬 Recent Comments ({issue_info['comments_count']}):")
        print(f"{'─'*70}")
        for i, comment in enumerate(issue_info['comments'][:3], 1):  # Show last 3
            print(f"\n[{i}] {comment['author']} ({comment['created']}):")
            preview = comment['body'][:200] + "..." if len(comment['body']) > 200 else comment['body']
            print(f"    {preview}")
    
    print(f"\n{'='*70}\n")
    
    print("💡 Next Steps:")
    print("   1. Review the issue description and requirements")
    print("   2. Check related code files and dependencies")
    print("   3. Plan your implementation approach")
    print("   4. Create a branch: git checkout -b fix/issue-{issue_info['number']}")
    print("   5. Implement the solution")
    print("   6. Test your changes")
    print("   7. Create a pull request")
    print("")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python github_working.py <owner/repo> <issue_number>")
        print("Example: python github_working.py owner/repo 123")
        sys.exit(1)
    
    repo_name = sys.argv[1]
    issue_number = int(sys.argv[2])
    
    print(f"🔍 Fetching issue #{issue_number} from {repo_name}...")
    
    issue_info = get_issue_info(repo_name, issue_number)
    
    if issue_info:
        print("✓ Issue fetched successfully")
        print("📊 Analyzing...")
        
        analysis = analyze_issue_basic(issue_info)
        display_results(issue_info, analysis)
    else:
        sys.exit(1)
