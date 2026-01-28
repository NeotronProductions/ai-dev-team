#!/usr/bin/env python3
"""
Simple example: Execute a GitHub issue with CrewAI.

Usage:
  With args:    python example_github_issue.py <repo> [issue_number]
  Interactive:  python example_github_issue.py
                (uses GITHUB_REPO from .env if set, then prompts for issue number)
"""

import os
import sys
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from crewai_tools import GithubSearchTool

# Load environment variables
load_dotenv()

# Disable CrewAI telemetry to avoid connection timeouts to telemetry.crewai.com
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN not found in .env file")
    print("   Run: ./scripts/setup_github_integration.sh")
    sys.exit(1)

# Repository: from CLI, then .env, then prompt
if len(sys.argv) >= 2:
    repo = sys.argv[1]
else:
    repo = os.getenv("GITHUB_REPO")
    if not repo:
        print("Repository not set. Enter your GitHub repo (format: owner/repo), or set GITHUB_REPO in .env")
        repo = input("GitHub repo (owner/repo): ").strip()
        if not repo:
            print("❌ Repository required.")
            sys.exit(1)

repo_url = f"https://github.com/{repo}"

# Issue number: from CLI, then interactive prompt
if len(sys.argv) >= 3:
    issue_number = sys.argv[2].strip() or None
else:
    issue_input = input(
        f"Enter an issue number from {repo_url} (or leave empty to analyze open issues): "
    ).strip()
    issue_number = issue_input if issue_input else None

print(f"🔍 Setting up GitHub integration for: {repo_url}")
if issue_number:
    print(f"   Target issue: #{issue_number}")
else:
    print("   Mode: analyze open issues (top 3)")
print("")

# Setup GitHub search tool
github_tool = GithubSearchTool(
    github_repo=repo_url,
    gh_token=GITHUB_TOKEN,
    content_types=['issue', 'code', 'pr']
)

# Create a simple agent
agent = Agent(
    role='GitHub Issue Analyzer',
    goal='Analyze GitHub issues and provide actionable solutions',
    backstory="""You are an expert software engineer who specializes in 
    analyzing GitHub issues. You can search repositories, understand code 
    context, and provide clear implementation guidance.""",
    tools=[github_tool],
    verbose=True
)

# Create task
if issue_number:
    task_description = f"""Analyze GitHub issue #{issue_number} from {repo_url}.
    
    Search for the issue, understand its requirements, find relevant code, 
    and provide a detailed solution plan."""
else:
    task_description = f"""Search and analyze open issues in {repo_url}.
    
    Find the most important or interesting issues and provide analysis 
    for the top 3 issues."""

task = Task(
    description=task_description,
    agent=agent,
    expected_output="Detailed analysis with actionable steps"
)

# Create crew and execute
crew = Crew(
    agents=[agent],
    tasks=[task],
    verbose=True
)

print(f"\n{'='*60}")
print("Starting CrewAI execution...")
print(f"{'='*60}\n")

result = crew.kickoff()

print(f"\n{'='*60}")
print("Results:")
print(f"{'='*60}\n")
print(result)
