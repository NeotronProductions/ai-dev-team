#!/usr/bin/env python3
"""
Main entrypoint for ai-dev-team.

- Ensures .env is configured (GitHub token, repo, optional project ID).
- Lets the user run a simple GitHub issue analysis crew.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from crewai_tools import GithubSearchTool


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def _read_env_lines():
    if not ENV_PATH.exists():
        return []
    content = ENV_PATH.read_text().strip()
    if not content:
        return []
    return content.splitlines()


def _set_env_key(lines, key: str, value: str):
    # remove existing key if present
    filtered = [line for line in lines if not line.startswith(f"{key}=")]
    filtered.append(f"{key}={value}")
    return filtered


def ensure_env():
    """Create/update .env interactively if key settings are missing."""
    if not ENV_PATH.exists():
        ENV_PATH.touch()

    # Load once to check existing values
    load_dotenv(dotenv_path=ENV_PATH, override=False)

    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")
    github_project_id = os.getenv("GITHUB_PROJECT_ID")

    lines = _read_env_lines()

    # Ask for missing token
    if not github_token:
        print("GitHub Personal Access Token is not configured.")
        print("Create one at https://github.com/settings/tokens with scopes: repo, read:org.")
        github_token = input("Enter your GitHub token (leave empty to skip): ").strip()
        if github_token:
            lines = _set_env_key(lines, "GITHUB_TOKEN", github_token)

    # Ask for missing repo
    if not github_repo:
        print("\nGitHub repository is not configured.")
        print("Example format: owner/repo")
        github_repo = input("Enter your GitHub repo (leave empty to skip): ").strip()
        if github_repo:
            lines = _set_env_key(lines, "GITHUB_REPO", github_repo)

    # Ask for optional project ID (GitHub Projects V2)
    if not github_project_id:
        print("\n(Optional) GitHub Project V2 ID is not configured.")
        print("If you use GitHub Projects, you can add an ID like:")
        print("  PVT_xxxxxxx  (from the project URL or via GraphQL)")
        project_input = input("Enter your GitHub Project V2 ID (leave empty to skip): ").strip()
        if project_input:
            lines = _set_env_key(lines, "GITHUB_PROJECT_ID", project_input)

    if lines:
        ENV_PATH.write_text("\n".join(lines) + "\n")

    # Reload after potential updates
    load_dotenv(dotenv_path=ENV_PATH, override=True)


def run_simple_github_crew():
    """Run a simple crew against a user-selected issue."""
    load_dotenv(dotenv_path=ENV_PATH, override=True)

    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")
    github_project_id = os.getenv("GITHUB_PROJECT_ID")  # optional, used only in prompt

    if not github_token:
        print("❌ GITHUB_TOKEN is missing in .env; cannot continue.")
        sys.exit(1)
    if not github_repo:
        print("❌ GITHUB_REPO is missing in .env; cannot continue.")
        sys.exit(1)

    repo_url = f"https://github.com/{github_repo}"
    issue_input = input(
        f"\nEnter an issue number from {repo_url} (or leave empty to analyze open issues): "
    ).strip()
    issue_number = issue_input or None

    print(f"\n🔍 Using repository: {repo_url}")
    if issue_number:
        print(f"   Target issue: #{issue_number}")
    if github_project_id:
        print(f"   Using GitHub Project V2 ID: {github_project_id}")

    github_tool = GithubSearchTool(
        github_repo=repo_url,
        gh_token=github_token,
        content_types=["issue", "code", "pr"],
    )

    # Include project context in the agent's backstory / instructions if available
    project_context = ""
    if github_project_id:
        project_context = (
            f"\nYou should prioritize issues that belong to GitHub Project V2 with ID "
            f"{github_project_id}. When analyzing issues, consider their status and fields "
            f"in that project if available."
        )

    agent = Agent(
        role="GitHub Issue Analyzer",
        goal="Analyze GitHub issues and provide actionable solutions",
        backstory=(
            "You are an expert software engineer who analyzes GitHub issues, "
            "understands the codebase, and proposes clear implementation plans."
            + project_context
        ),
        tools=[github_tool],
        verbose=True,
    )

    if issue_number:
        description = (
            f"Analyze GitHub issue #{issue_number} from {repo_url}.\n\n"
            "Search for the issue, understand its requirements, find relevant code, "
            "and provide a detailed solution plan."
        )
    else:
        description = (
            f"Search and analyze open issues in {repo_url}.\n\n"
            "Find the most important or interesting issues and provide analysis "
            "for the top 3 issues."
        )

    if github_project_id:
        description += (
            f"\n\nThe repository uses GitHub Project V2 with ID {github_project_id}. "
            "When possible, take into account the project's fields (status, priority, etc.) "
            "to decide which issues to focus on and how to plan the work."
        )

    task = Task(
        description=description,
        agent=agent,
        expected_output="Detailed analysis with actionable steps",
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
    )

    print("\n" + "=" * 60)
    print("Starting CrewAI execution...")
    print("=" * 60 + "\n")

    result = crew.kickoff()

    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60 + "\n")
    print(result)


def main():
    print("🚀 AI Dev Team - GitHub Crew Initializer")
    print("========================================\n")

    ensure_env()

    print("\nConfiguration loaded from .env.\n")
    print("1) Run GitHub issue analysis crew")
    print("q) Quit")

    choice = input("\nSelect an option: ").strip().lower()
    if choice == "1":
        run_simple_github_crew()
    else:
        print("Bye!")


if __name__ == "__main__":
    main()

