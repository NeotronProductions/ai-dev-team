#!/usr/bin/env python3
"""
Simple example: Execute a GitHub issue with CrewAI
"""

import os
import sys
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from crewai_tools import GithubSearchTool

# Load environment variables
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN not found in .env file")
    print("   Run: ./scripts/setup_github_integration.sh")
    sys.exit(1)

# Get repository from command line or environment
if len(sys.argv) < 2:
    print("Usage: python example_github_issue.py <repo> [issue_number]")
    print("Example: python example_github_issue.py owner/repo 123")
    sys.exit(1)

repo = sys.argv[1]
repo_url = f"https://github.com/{repo}"

# Optional issue number
issue_number = sys.argv[2] if len(sys.argv) > 2 else None

print(f"🔍 Setting up GitHub integration for: {repo_url}")
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
