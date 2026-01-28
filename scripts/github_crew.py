#!/usr/bin/env python3
"""
CrewAI GitHub Integration - Execute GitHub Issues
This script sets up CrewAI agents to work with GitHub issues.
"""

import os
from crewai import Agent, Task, Crew, Process
from crewai_tools import GithubSearchTool, ComposioTool
from composio_core import Action, App

# Load GitHub token from environment
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("⚠️  Warning: GITHUB_TOKEN not set. Please set it in your environment.")
    print("   You can create a .env file or export it:")
    print("   export GITHUB_TOKEN='your_token_here'")

# GitHub repository configuration
GITHUB_REPO = os.getenv("GITHUB_REPO", "owner/repo")  # Change to your repo
GITHUB_REPO_URL = f"https://github.com/{GITHUB_REPO}"

def setup_github_tools():
    """Setup GitHub tools for CrewAI agents."""
    tools = []
    
    # GitHub Search Tool - for searching issues, PRs, code
    if GITHUB_TOKEN:
        github_search = GithubSearchTool(
            github_repo=GITHUB_REPO_URL,
            gh_token=GITHUB_TOKEN,
            content_types=['issue', 'pr', 'code']  # Search issues, PRs, and code
        )
        tools.append(github_search)
        print(f"✓ GitHub Search Tool configured for {GITHUB_REPO_URL}")
    
    # Composio Tool for GitHub actions (if available)
    try:
        github_actions = ComposioTool.from_app(
            App.GITHUB,
            tags=["issue", "pull_request"]
        )
        tools.append(github_actions)
        print("✓ Composio GitHub Tool configured")
    except Exception as e:
        print(f"⚠️  Composio Tool not available: {e}")
        print("   Install with: pip install composio-core composio-openai")
    
    return tools

def create_github_issue_agent(tools):
    """Create an agent specialized in handling GitHub issues."""
    return Agent(
        role='GitHub Issue Manager',
        goal='Analyze, understand, and execute GitHub issues efficiently',
        backstory="""You are an expert GitHub issue manager with deep knowledge of 
        software development workflows. You can read issues, understand requirements, 
        search codebases, and help execute solutions. You're skilled at breaking down 
        complex issues into actionable tasks.""",
        tools=tools,
        verbose=True,
        allow_delegation=False
    )

def create_code_analyst_agent(tools):
    """Create an agent specialized in code analysis."""
    return Agent(
        role='Code Analyst',
        goal='Analyze code, understand context, and provide implementation guidance',
        backstory="""You are a senior software engineer with expertise in code analysis. 
        You can search through codebases, understand code structure, identify patterns, 
        and suggest implementations. You work closely with issue managers to understand 
        requirements and provide technical solutions.""",
        tools=tools,
        verbose=True,
        allow_delegation=False
    )

def create_github_crew():
    """Create a Crew for executing GitHub issues."""
    tools = setup_github_tools()
    
    # Create agents
    issue_manager = create_github_issue_agent(tools)
    code_analyst = create_code_analyst_agent(tools)
    
    # Create tasks
    analyze_issue_task = Task(
        description="""Analyze the GitHub issue. Search the repository for relevant 
        code, understand the context, and break down the issue into actionable steps. 
        Provide a clear summary of what needs to be done.""",
        agent=issue_manager,
        expected_output="A detailed analysis of the issue with actionable steps"
    )
    
    provide_solution_task = Task(
        description="""Based on the issue analysis, search the codebase for relevant 
        files and patterns. Provide a detailed implementation plan with code examples 
        and file locations that need to be modified.""",
        agent=code_analyst,
        expected_output="A detailed implementation plan with code examples"
    )
    
    # Create crew
    crew = Crew(
        agents=[issue_manager, code_analyst],
        tasks=[analyze_issue_task, provide_solution_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew

def execute_issue(issue_number: int, repo: str = None):
    """Execute a specific GitHub issue."""
    if repo:
        global GITHUB_REPO, GITHUB_REPO_URL
        GITHUB_REPO = repo
        GITHUB_REPO_URL = f"https://github.com/{repo}"
    
    print(f"\n{'='*60}")
    print(f"Executing GitHub Issue #{issue_number}")
    print(f"Repository: {GITHUB_REPO_URL}")
    print(f"{'='*60}\n")
    
    crew = create_github_crew()
    
    # Create a task to execute the specific issue
    issue_task = Task(
        description=f"""Execute GitHub issue #{issue_number} from {GITHUB_REPO_URL}.
        
        Steps:
        1. Search for and read issue #{issue_number}
        2. Understand the requirements and context
        3. Search the codebase for relevant files
        4. Analyze the current implementation
        5. Provide a detailed solution with code examples
        6. Create an implementation plan
        
        Be thorough and provide actionable steps.""",
        agent=crew.agents[0],
        expected_output="Complete analysis and implementation plan for the issue"
    )
    
    # Execute
    result = crew.kickoff(inputs={"issue_number": issue_number})
    
    print(f"\n{'='*60}")
    print("Execution Complete")
    print(f"{'='*60}\n")
    
    return result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python github_crew.py <issue_number> [repo]")
        print("Example: python github_crew.py 123 owner/repo")
        print("\nOr set environment variables:")
        print("  export GITHUB_TOKEN='your_token'")
        print("  export GITHUB_REPO='owner/repo'")
        sys.exit(1)
    
    issue_number = int(sys.argv[1])
    repo = sys.argv[2] if len(sys.argv) > 2 else None
    
    result = execute_issue(issue_number, repo)
    print(result)
