#!/usr/bin/env python3
"""
Simple GitHub integration using PyGithub (no OpenAI required)
This version uses direct GitHub API calls without semantic search
"""

import os
import sys
from dotenv import load_dotenv
from github import Github
from crewai import Agent, Task, Crew, LLM

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN not found in .env file")
    sys.exit(1)

def get_issue_info(repo_name, issue_number):
    """Get issue information using GitHub API"""
    from github.Auth import Token
    auth = Token(GITHUB_TOKEN)
    g = Github(auth=auth)
    try:
        repo = g.get_repo(repo_name)
        issue = repo.get_issue(issue_number)
        
        return {
            "title": issue.title,
            "body": issue.body,
            "state": issue.state,
            "labels": [label.name for label in issue.labels],
            "assignee": issue.assignee.login if issue.assignee else None,
            "created_at": str(issue.created_at),
            "url": issue.html_url
        }
    except Exception as e:
        print(f"❌ Error fetching issue: {e}")
        return None

def analyze_issue_with_crew(issue_info):
    """Use CrewAI to analyze the issue"""
    
    # Use Ollama with qwen2.5-coder:3b
    try:
        # Check if Ollama is available
        import subprocess
        result = subprocess.run(['curl', '-sSf', 'http://localhost:11434/api/tags'], 
                              capture_output=True, timeout=2)
        if result.returncode == 0:
            llm = LLM(model="ollama/qwen2.5-coder:3b", base_url="http://localhost:11434")
            print("✓ Using Ollama (qwen2.5-coder:3b)")
        else:
            raise Exception("Ollama not available - service not responding")
    except Exception as e:
        print(f"\n❌ Ollama not available: {e}")
        print("\nTo fix this:")
        print("  1. Make sure Ollama is installed and running")
        print("  2. Run: python3 check_ollama.py")
        print("  3. Or start Ollama manually: ollama serve")
        print("\nAlternatively, set OPENAI_API_KEY in .env for OpenAI")
        raise
    
    # Create a simple agent (no GitHub tools needed, just analysis)
    agent = Agent(
        role='Issue Analyst',
        goal='Analyze GitHub issues and provide actionable solutions',
        backstory="""You are an expert software engineer who specializes in 
        analyzing GitHub issues. You understand requirements, identify 
        technical challenges, and provide clear implementation guidance.""",
        llm=llm,
        verbose=True
    )
    
    task = Task(
        description=f"""Analyze this GitHub issue:
        
        Title: {issue_info['title']}
        Description: {issue_info['body']}
        Labels: {', '.join(issue_info['labels'])}
        State: {issue_info['state']}
        URL: {issue_info['url']}
        
        Provide:
        1. A clear summary of what needs to be done
        2. Technical approach and considerations
        3. Step-by-step implementation plan
        4. Potential challenges and solutions""",
        agent=agent,
        expected_output="Detailed analysis with actionable implementation steps"
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True
    )
    
    return crew.kickoff()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python github_simple.py <owner/repo> <issue_number>")
        print("Example: python github_simple.py owner/repo 123")
        sys.exit(1)
    
    repo_name = sys.argv[1]
    issue_number = int(sys.argv[2])
    
    print(f"\n{'='*60}")
    print(f"Analyzing GitHub Issue #{issue_number}")
    print(f"Repository: {repo_name}")
    print(f"{'='*60}\n")
    
    # Get issue info
    print("📥 Fetching issue from GitHub...")
    issue_info = get_issue_info(repo_name, issue_number)
    
    if not issue_info:
        sys.exit(1)
    
    print(f"✓ Issue found: {issue_info['title']}")
    print(f"  State: {issue_info['state']}")
    print(f"  Labels: {', '.join(issue_info['labels']) if issue_info['labels'] else 'None'}")
    print(f"  URL: {issue_info['url']}\n")
    
    # Analyze with CrewAI
    print("🤖 Analyzing with CrewAI...\n")
    result = analyze_issue_with_crew(issue_info)
    
    print(f"\n{'='*60}")
    print("Analysis Complete")
    print(f"{'='*60}\n")
    print(result)
