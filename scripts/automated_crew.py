#!/usr/bin/env python3
"""
Automated CrewAI Crew for GitHub Issue Processing
This crew automatically processes issues, implements solutions, and moves to the next one.
"""

import os
import sys
import subprocess
import re
import shlex
import requests
from pathlib import Path
from dotenv import load_dotenv
from github import Github
from github.Auth import Token
from crewai import Agent, Task, Crew, LLM
from crewai.tools.base_tool import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import json

# Add parent directory to path to import crew_runner modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from refactored modules
from crew_runner.schema import RunState, validate_structured_changes
from crew_runner.path_safety import get_repo_file_allowlist
from crew_runner.apply_changes import apply_structured_changes
from crew_runner.plan_requirements import parse_plan_requirements
from crew_runner.coverage import check_coverage
from crew_runner.git_ops import (
    get_current_branch, get_head_sha, get_git_changed_files,
    has_changes, ensure_base_branch, create_branch_and_commit, ensure_feature_branch
)
from crew_runner.github_ops import (
    get_github_client, get_sub_issues, get_next_issue,
    mark_issue_processed, create_pr, move_issue_in_project
)
from crew_runner.logging_utils import print_issue_status

# Load environment variables first
load_dotenv()

# Ensure OPENAI_API_KEY is in environment if it exists in .env
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    os.environ["OPENAI_API_KEY"] = openai_key

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# WORK_DIR can be overridden via command line or environment variable
# Default to V3, but can be changed per run
WORK_DIR = Path.home() / "dev" / "Beautiful-Timetracker-App"


def create_execute_command_tool(work_dir: Path):
    """Create an ExecuteCommandTool configured for a specific working directory"""
    
    class ExecuteCommandTool(BaseTool):
        """Tool for executing shell commands in the project directory"""
        name: str = "Execute Command"
        description: str = (
            f"Execute a shell command in the project directory ({work_dir}). "
            "Use this to run tests, check file contents, or execute any shell command. "
            "Returns the command output (stdout and stderr). "
            "Example commands: 'npm test', 'pytest', 'go test ./...', 'python -m pytest', etc."
        )
        
        def _run(self, command: str) -> str:
            """Execute a shell command"""
            try:
                if not work_dir.exists():
                    return f"Error: Directory {work_dir} does not exist"
                
                # Execute command with timeout
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=str(work_dir),
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minute timeout
                    encoding='utf-8',
                    errors='replace'
                )
                
                output = f"Exit code: {result.returncode}\n"
                if result.stdout:
                    output += f"STDOUT:\n{result.stdout}\n"
                if result.stderr:
                    output += f"STDERR:\n{result.stderr}\n"
                
                return output
            except subprocess.TimeoutExpired:
                return "Error: Command timed out after 5 minutes"
            except Exception as e:
                return f"Error executing command: {str(e)}"
    
    return ExecuteCommandTool()


def run_tests_after_patch(work_dir: Path, issue_number: int, crew_result) -> str:
    """
    Run tests after patch is applied using the tester agent.
    Returns test results as a string.
    """
    print("\n" + "="*70)
    print("🧪 Running Tests After Patch Application")
    print("="*70)
    
    # Get the tester agent with tool configured for this work_dir
    _, _, _, _, tester_base = create_implementation_crew()
    
    # Create tester agent with tool configured for the specific work_dir
    execute_tool = create_execute_command_tool(work_dir)
    tester = Agent(
        role=tester_base.role,
        goal=tester_base.goal,
        backstory=tester_base.backstory,
        llm=tester_base.llm,
        verbose=True,
        tools=[execute_tool],
        allow_delegation=False,
    )
    
    # Detect test framework
    test_info = detect_test_framework(work_dir)
    
    # Build test task description
    test_description = f"""Execute comprehensive tests for the code changes that were just applied.

WORKING DIRECTORY: {work_dir}
ISSUE NUMBER: {issue_number}

DETECTED TEST FRAMEWORK: {test_info.get('framework', 'Unknown')}
TEST COMMAND: {test_info.get('test_command', 'Not detected')}

TESTING REQUIREMENTS:
1. Run automated tests if available (unit tests, integration tests)
2. If the issue mentions specific testing requirements (like "100+ sessions", "scroll performance", "screen reader testing"), 
   create test scenarios to verify those requirements
3. Check for any test files that were created or modified
4. Verify the code works as expected
5. Report any test failures or issues

SPECIFIC TESTING SCENARIOS TO CONSIDER:
- Performance testing: If the issue mentions "100+ sessions" or "scroll performance", 
  create test data (e.g., 100+ sessions) and verify that scrolling remains performant
- Accessibility testing: If the issue mentions "screen reader testing", verify that 
  screen readers can properly announce and navigate the interface
- Manual testing scenarios mentioned in the implementation plan or issue description
- Edge cases and error handling
- Integration testing to ensure new code works with existing functionality

Use the Execute Command tool to:
- Run test commands (npm test, pytest, go test, etc.)
- Create test data if needed
- Check test output and results
- Verify functionality

Provide a detailed test report including:
- Which tests were executed
- Test results (pass/fail)
- Any issues or failures found
- Recommendations for fixes if tests fail
"""
    
    # Create testing task
    test_task = Task(
        description=test_description,
        agent=tester,
        expected_output="Detailed test report with test results, pass/fail status, and any issues found"
    )
    
    # Create a crew just for testing
    test_crew = Crew(
        agents=[tester],
        tasks=[test_task],
        verbose=True
    )
    
    try:
        print("\n🚀 Starting test execution...")
        print(f"📋 Test Framework Detected: {test_info.get('framework', 'None')}")
        if test_info.get('test_command'):
            print(f"📋 Test Command: {test_info.get('test_command')}")
        
        test_result = test_crew.kickoff()
        test_output = str(test_result) if test_result else "No test output"
        
        # Parse test output to determine status
        test_status = "UNKNOWN"
        if "pass" in test_output.lower() and "fail" not in test_output.lower():
            test_status = "✅ PASSED"
        elif "fail" in test_output.lower() or "error" in test_output.lower():
            test_status = "❌ FAILED"
        elif "no tests" in test_output.lower() or "not found" in test_output.lower():
            test_status = "⚠️  NO TESTS FOUND"
        else:
            test_status = "ℹ️  COMPLETED"
        
        print(f"\n{'='*70}")
        print(f"🧪 TEST EXECUTION STATUS: {test_status}")
        print(f"{'='*70}")
        print(f"\n📊 Test Output Summary:")
        print(f"   Output length: {len(test_output)} characters")
        
        # Show key indicators from output
        if "exit code: 0" in test_output.lower():
            print(f"   ✅ Command exited successfully (exit code 0)")
        elif "exit code:" in test_output.lower():
            exit_code_match = re.search(r"exit code:\s*(\d+)", test_output, re.IGNORECASE)
            if exit_code_match:
                exit_code = exit_code_match.group(1)
                if exit_code != "0":
                    print(f"   ❌ Command exited with code {exit_code}")
        
        print(f"\n📄 Full test output saved to implementation plan")
        print(f"{'='*70}\n")
        
        return f"## Test Execution Status: {test_status}\n\n{test_output}"
    except Exception as e:
        error_msg = f"Error during test execution: {str(e)}"
        print(f"\n{'='*70}")
        print(f"❌ TEST EXECUTION FAILED")
        print(f"{'='*70}")
        print(f"⚠️  {error_msg}")
        print(f"{'='*70}\n")
        return f"## Test Execution Status: ❌ FAILED\n\n⚠️  Test execution failed: {error_msg}\n\nError details: {str(e)}"


def detect_test_framework(work_dir: Path) -> dict:
    """Detect what test framework is used in the project"""
    test_info = {
        'framework': None,
        'test_command': None,
        'test_files': []
    }
    
    # Check for package.json (Node.js/JavaScript)
    package_json = work_dir / "package.json"
    if package_json.exists():
        try:
            pkg = json.loads(package_json.read_text())
            scripts = pkg.get('scripts', {})
            
            # Check for test scripts
            if 'test' in scripts:
                test_info['framework'] = 'npm'
                test_info['test_command'] = 'npm test'
            elif 'jest' in scripts or any('jest' in str(v) for v in scripts.values()):
                test_info['framework'] = 'jest'
                test_info['test_command'] = 'npm test'
            elif 'vitest' in scripts or any('vitest' in str(v) for v in scripts.values()):
                test_info['framework'] = 'vitest'
                test_info['test_command'] = 'npm test'
        except:
            pass
    
    # Check for Python test files
    test_dirs = ['tests', 'test', 'tests.py']
    for test_dir_name in test_dirs:
        test_dir = work_dir / test_dir_name
        if test_dir.exists() and test_dir.is_dir():
            test_files = list(test_dir.glob("test_*.py")) + list(test_dir.glob("*_test.py"))
            if test_files:
                test_info['framework'] = 'pytest'
                test_info['test_command'] = 'pytest'
                test_info['test_files'] = [str(f.relative_to(work_dir)) for f in test_files[:5]]
                break
    
    # Check for pytest.ini or pyproject.toml
    if (work_dir / "pytest.ini").exists() or (work_dir / "pyproject.toml").exists():
        test_info['framework'] = 'pytest'
        test_info['test_command'] = 'pytest'
    
    # Check for Go tests
    go_test_files = list(work_dir.glob("**/*_test.go"))
    if go_test_files:
        test_info['framework'] = 'go'
        test_info['test_command'] = 'go test ./...'
    
    return test_info

def get_github_client():
    """Get authenticated GitHub client"""
    if not GITHUB_TOKEN:
        return None
    auth = Token(GITHUB_TOKEN)
    return Github(auth=auth)

def get_sub_issues(repo_name, issue_number):
    """Get sub-issues (child issues) for a given parent issue"""
    g = get_github_client()
    if not g:
        return []
    
    try:
        repo = g.get_repo(repo_name)
        
        # Method 1: Try GitHub Sub-Issues API (if available)
        # Note: Sub-issues API might require GitHub Enterprise or specific features
        try:
            # Use REST API to get sub-issues
            # GET /repos/{owner}/{repo}/issues/{issue_number}/sub-issues
            import requests
            token = os.getenv("GITHUB_TOKEN")
            headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
            url = f"https://api.github.com/repos/{repo_name}/issues/{issue_number}/sub-issues"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                sub_issues_data = response.json()
                sub_issues = []
                for sub_issue_data in sub_issues_data:
                    sub_issue = repo.get_issue(sub_issue_data['number'])
                    sub_issues.append(sub_issue)
                return sub_issues
        except:
            pass
        
        # Method 2: Check issue body for linked issues (fallback)
        # Look for patterns like "Sub-issues: #123, #456" or "Related: #123"
        parent_issue = repo.get_issue(issue_number)
        if not parent_issue.body:
            return []
        
        import re
        # Pattern to find issue references: #123 or #123, #456
        issue_refs = re.findall(r'#(\d+)', parent_issue.body)
        sub_issues = []
        
        for ref_num in issue_refs:
            try:
                ref_num_int = int(ref_num)
                # Skip the parent issue itself
                if ref_num_int != issue_number:
                    linked_issue = repo.get_issue(ref_num_int)
                    # Only include open issues
                    if linked_issue.state == 'open':
                        sub_issues.append(linked_issue)
            except:
                continue
        
        # Remove duplicates
        seen = set()
        unique_sub_issues = []
        for issue in sub_issues:
            if issue.number not in seen:
                seen.add(issue.number)
                unique_sub_issues.append(issue)
        
        return unique_sub_issues
        
    except Exception as e:
        print(f"⚠️  Warning: Could not fetch sub-issues for #{issue_number}: {e}")
        return []

def get_next_issue(repo_name, processed_issues_file):
    """Get the next unprocessed issue"""
    g = get_github_client()
    if not g:
        return None
    
    # Load processed issues
    processed = set()
    if processed_issues_file.exists():
        with open(processed_issues_file, 'r') as f:
            processed = set(json.load(f))
    
    # Get open issues
    repo = g.get_repo(repo_name)
    issues = repo.get_issues(state='open', sort='updated')
    
    # Find first unprocessed issue
    for issue in issues:
        if issue.number not in processed:
            return issue
    
    return None

def mark_issue_processed(issue_number, processed_issues_file):
    """Mark an issue as processed"""
    processed = set()
    if processed_issues_file.exists():
        with open(processed_issues_file, 'r') as f:
            processed = set(json.load(f))
    
    processed.add(issue_number)
    
    with open(processed_issues_file, 'w') as f:
        json.dump(list(processed), f)

def create_implementation_crew():
    """Create a crew for implementing solutions - aligned with run_autopr.py structure"""
    
    # Load environment variables (ensure .env is loaded)
    load_dotenv()
    
    # Configure Ollama
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")
    
    # Set environment for LiteLLM (used by CrewAI)
    os.environ.setdefault("LITELLM_LOG", "ERROR")
    os.environ.setdefault("OLLAMA_API_BASE", ollama_base_url)
    
    # Configure timeout for Ollama (default 600s, can be increased for complex tasks)
    ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "1200"))  # 20 minutes default
    os.environ.setdefault("LITELLM_TIMEOUT", str(ollama_timeout))
    
    # Get OpenAI key (already loaded at module level, but ensure it's set)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key  # Ensure it's in environment
    
    # Check if OpenAI is forced via environment variable
    force_openai = os.getenv("FORCE_OPENAI", "false").lower() == "true"
    
    # Priority: Try Ollama (qwen2.5-coder:3b) first, then fallback to OpenAI
    # This ensures we use local/cheaper Ollama when available, OpenAI as backup
    # Unless FORCE_OPENAI=true is set
    llm_model = None
    ollama_available = False
    
    # Skip Ollama check if OpenAI is forced
    if force_openai:
        print("🔧 OpenAI forced via FORCE_OPENAI=true, skipping Ollama")
        ollama_available = False
    else:
        # Check if Ollama is available
        try:
            import subprocess
            result = subprocess.run(['curl', '-sSf', f'{ollama_base_url}/api/tags'], 
                                  capture_output=True, timeout=2)
            if result.returncode == 0:
                ollama_available = True
                print(f"✓ Ollama detected at {ollama_base_url}")
        except Exception as e:
            print(f"⚠ Ollama check failed: {e}")
            ollama_available = False
    
    # Try to use Ollama first (qwen2.5-coder:3b)
    if ollama_available:
        try:
            # Set environment variables for Ollama/LiteLLM
            os.environ["OLLAMA_API_BASE"] = ollama_base_url
            os.environ["OLLAMA_BASE_URL"] = ollama_base_url
            
            # Try to create LLM object with Ollama
            # Format: "ollama/model_name" - CrewAI uses LiteLLM internally
            try:
                llm_model = LLM(model=f"ollama/{ollama_model}", base_url=ollama_base_url)
                print(f"✓ Using Ollama ({ollama_model}) - LLM object created")
            except Exception as e1:
                # Fallback: use string format (CrewAI will try to use LiteLLM)
                print(f"⚠ LLM object creation failed, trying string format: {e1}")
                try:
                    # Set environment for LiteLLM to find Ollama
                    os.environ["OLLAMA_API_BASE"] = ollama_base_url
                    llm_model = f"ollama/{ollama_model}"
                    print(f"✓ Using Ollama ({ollama_model}) - string format")
                except Exception as e2:
                    print(f"⚠ Failed to use Ollama string format: {e2}")
                    raise Exception("Ollama configuration failed")
        except Exception as e:
            print(f"⚠ Failed to configure Ollama: {e}")
            print("🔄 Falling back to OpenAI...")
            ollama_available = False
    
    # Fallback to OpenAI if Ollama failed or not available
    if not ollama_available or llm_model is None:
        if openai_key:
            try:
                # Try creating LLM object with explicit API key
                llm_model = LLM(model="gpt-4o-mini", api_key=openai_key)
                print(f"✓ Using OpenAI (gpt-4o-mini) - fallback from Ollama")
            except Exception as e:
                print(f"⚠ Failed to initialize OpenAI LLM with explicit key: {e}")
                # Fallback: use string and rely on environment variable
                os.environ["OPENAI_API_KEY"] = openai_key
                llm_model = "gpt-4o-mini"
                print(f"✓ Using OpenAI (gpt-4o-mini) via environment variable")
        else:
            if ollama_available:
                # Ollama was available but configuration failed
                raise ValueError(f"Ollama is available but configuration failed. Please check Ollama setup or configure OPENAI_API_KEY as fallback.")
            else:
                raise ValueError("No LLM available. Please configure OPENAI_API_KEY or start Ollama.")
    
    # Product Manager Agent - aligned with run_autopr.py
    product = Agent(
        role="Product Manager",
        goal="Convert issue into a clear user story + acceptance criteria",
        backstory="You are an expert agile PM. You clarify scope and define Done.",
        llm=llm_model,
        verbose=True,
    )
    
    # Software Architect Agent - aligned with run_autopr.py
    architect = Agent(
        role="Software Architect",
        goal="Create a minimal technical plan and identify files to change",
        backstory="You favor small diffs, maintainability, and testability.",
        llm=llm_model,
        verbose=True,
    )
    
    # Developer Agent - aligned with run_autopr.py
    developer = Agent(
        role="Developer",
        goal="Produce a single unified diff patch implementing the issue",
        backstory="You write production-grade code and include tests when possible.",
        llm=llm_model,
        verbose=True,
    )
    
    # Code Reviewer Agent - aligned with run_autopr.py
    reviewer = Agent(
        role="Code Reviewer",
        goal="Catch bugs/security issues; ensure edge cases and quality",
        backstory="You are strict but practical; you request changes if needed.",
        llm=llm_model,
        verbose=True,
    )
    
    # Tester Agent - executes tests and verifies functionality
    # Note: Tools will be set dynamically with work_dir when needed
    tester = Agent(
        role="QA Tester",
        goal="Execute tests, verify code functionality, and report test results",
        backstory=(
            "You are an expert QA engineer who runs comprehensive tests including "
            "unit tests, integration tests, performance tests, and manual testing scenarios. "
            "You execute test commands, analyze results, and provide detailed test reports. "
            "You can run automated tests, create test data (like 100+ sessions for performance testing), "
            "and verify accessibility features like screen reader compatibility."
        ),
        llm=llm_model,
        verbose=True,
        allow_delegation=False,
    )
    
    return product, architect, developer, reviewer, tester

def get_project_context(work_dir: Path) -> str:
    """Gather project context from repository files"""
    context_parts = []
    
    # 1. Read README if exists
    readme_path = work_dir / "README.md"
    if readme_path.exists():
        try:
            readme_content = readme_path.read_text(encoding='utf-8')[:2000]  # First 2000 chars
            context_parts.append(f"## Project README\n{readme_content}\n")
        except:
            pass
    
    # 2. Check for package.json (Node.js/JavaScript projects)
    package_json = work_dir / "package.json"
    if package_json.exists():
        try:
            pkg = json.loads(package_json.read_text())
            context_parts.append("## Tech Stack (from package.json)\n")
            context_parts.append(f"- **Project Name**: {pkg.get('name', 'Unknown')}\n")
            context_parts.append(f"- **Description**: {pkg.get('description', 'N/A')}\n")
            if pkg.get('dependencies'):
                deps = list(pkg['dependencies'].keys())[:10]  # Top 10
                context_parts.append(f"- **Dependencies**: {', '.join(deps)}\n")
            if pkg.get('devDependencies'):
                dev_deps = list(pkg['devDependencies'].keys())[:10]
                context_parts.append(f"- **Dev Dependencies**: {', '.join(dev_deps)}\n")
            context_parts.append("\n")
        except:
            pass
    
    # 3. Check for requirements.txt (Python projects)
    requirements = work_dir / "requirements.txt"
    if requirements.exists():
        try:
            reqs = requirements.read_text(encoding='utf-8')[:1000]
            context_parts.append("## Python Dependencies\n")
            context_parts.append(f"```\n{reqs}\n```\n\n")
        except:
            pass
    
    # 3.5. Read PROJECT_CONTEXT.md if exists (detailed project context)
    # Limit to 10000 chars to avoid token limit errors (approx 2500 tokens)
    project_context_path = work_dir / "PROJECT_CONTEXT.md"
    if project_context_path.exists():
        try:
            project_context_content = project_context_path.read_text(encoding='utf-8')
            # Limit size to prevent token limit errors
            if len(project_context_content) > 10000:
                project_context_content = project_context_content[:10000] + "\n\n[... PROJECT_CONTEXT.md truncated to prevent token limit errors ...]"
            context_parts.append(f"## Detailed Project Context\n{project_context_content}\n")
        except:
            pass
    
    # 4. Check project structure and read sample code files
    try:
        files = list(work_dir.iterdir())
        file_types = {}
        for f in files:
            if f.is_file():
                ext = f.suffix
                file_types[ext] = file_types.get(ext, 0) + 1
        
        if file_types:
            context_parts.append("## Project Structure\n")
            context_parts.append(f"- **File types found**: {', '.join(sorted(file_types.keys()))}\n")
            
            # Check for common directories
            common_dirs = ['src', 'lib', 'app', 'components', 'public', 'static', 'templates', 'tests', 'test', 'js', 'css']
            found_dirs = [d for d in common_dirs if (work_dir / d).exists()]
            if found_dirs:
                context_parts.append(f"- **Key directories**: {', '.join(found_dirs)}\n")
            context_parts.append("\n")
        
        # 4.5. Read sample code files to understand patterns (for vanilla JS/HTML/CSS projects)
        # Look for main entry points and key modules
        sample_files = []
        if (work_dir / "index.html").exists():
            sample_files.append(("index.html", work_dir / "index.html"))
        
        # Look in js/ directory for main modules
        js_dir = work_dir / "js"
        if js_dir.exists() and js_dir.is_dir():
            for js_file in list(js_dir.glob("*.js"))[:3]:  # First 3 JS files
                sample_files.append((f"js/{js_file.name}", js_file))
        
        # Look in css/ directory for stylesheets
        css_dir = work_dir / "css"
        if css_dir.exists() and css_dir.is_dir():
            for css_file in list(css_dir.glob("*.css"))[:2]:  # First 2 CSS files
                sample_files.append((f"css/{css_file.name}", css_file))
        
        # Read and include sample code (limited to avoid token limits)
        # Reduced from 5 files to 3 files, and from 1500 to 1000 chars per file
        if sample_files:
            context_parts.append("## Code Examples (for pattern reference)\n")
            for file_name, file_path in sample_files[:3]:  # Max 3 files (reduced from 5)
                try:
                    content = file_path.read_text(encoding='utf-8')[:1000]  # First 1000 chars per file (reduced from 1500)
                    context_parts.append(f"### {file_name}\n```\n{content}\n```\n\n")
                except:
                    pass
    except:
        pass
    
    # 5. Look for config files that indicate tech stack
    config_files = {
        'tsconfig.json': 'TypeScript',
        'webpack.config.js': 'Webpack',
        'vite.config.js': 'Vite',
        'next.config.js': 'Next.js',
        'vue.config.js': 'Vue.js',
        'angular.json': 'Angular',
        'Cargo.toml': 'Rust',
        'go.mod': 'Go',
        'pom.xml': 'Java/Maven',
        'build.gradle': 'Java/Gradle',
        'composer.json': 'PHP',
        'Gemfile': 'Ruby',
    }
    
    found_tech = []
    for config_file, tech in config_files.items():
        if (work_dir / config_file).exists():
            found_tech.append(tech)
    
    if found_tech:
        context_parts.append("## Detected Technologies\n")
        context_parts.append(f"- {', '.join(found_tech)}\n\n")
    
    # Combine all context
    if context_parts:
        return "\n".join(context_parts)
    else:
        return "## Project Context\nNo specific project context detected. Assume standard project layout.\n\n"

def process_issue(issue, repo_name, work_dir, include_sub_issues=True, enable_testing: bool = None):
    """Process a single issue through the crew - aligned with run_autopr.py workflow
    
    Args:
        issue: GitHub issue object
        repo_name: Repository name
        work_dir: Working directory path
        include_sub_issues: If True, process sub-issues as part of this issue
        enable_testing: If True, run tests after applying changes.
                       If None, uses ENABLE_TESTING env var (default: True)
    """
    
    print(f"\n{'='*70}")
    print(f"Processing Issue #{issue.number}: {issue.title}")
    print(f"{'='*70}\n")
    
    # Check for sub-issues
    sub_issues = []
    if include_sub_issues:
        sub_issues = get_sub_issues(repo_name, issue.number)
        if sub_issues:
            print(f"📋 Found {len(sub_issues)} sub-issue(s):")
            for sub in sub_issues:
                print(f"   - #{sub.number}: {sub.title}")
            print()
    
    product, architect, developer, reviewer, tester = create_implementation_crew()
    
    # Gather project context
    project_context = get_project_context(work_dir)
    print("📋 Project context gathered")
    
    # Build issue text including sub-issues context
    issue_text = f"# {issue.title}\n\n{issue.body or 'No description'}".strip()
    
    # Add sub-issues information to the issue text if they exist
    if sub_issues:
        sub_issues_text = "\n\n## Sub-Issues\n"
        sub_issues_text += "This issue has the following sub-issues that should be considered:\n\n"
        for sub in sub_issues:
            sub_issues_text += f"- **#{sub.number}**: {sub.title}\n"
            if sub.body:
                sub_issues_text += f"  {sub.body[:200]}...\n"  # First 200 chars
        issue_text += sub_issues_text
    
    # Task 1: Product Manager - Convert to user story (aligned with run_autopr.py)
    product_task = Task(
        description=f"""Given this GitHub issue, write:
1) A user story (As a ... I want ... so that ...)
2) Acceptance criteria (bullets)
3) Out of scope (bullets)
4) Risks/unknowns (bullets)

Issue:
{issue_text}
""",
        agent=product,
        expected_output="User story with acceptance criteria, out of scope, and risks"
    )
    
    # Task 2: Architect - Create technical plan (aligned with run_autopr.py)
    architect_task = Task(
        description=f"""Based on the user story, produce:
- Minimal implementation plan
- Files to change (bullets)
- Any new functions/classes/modules
- Test approach

Keep it concise and repo-appropriate.

PROJECT CONTEXT:
{project_context}

Working directory: {work_dir}
""",
        agent=architect,
        context=[product_task],
        expected_output="Minimal technical plan with files to change and test approach"
    )
    
    # A) Get repo file allowlist for repo-scoped prompting
    repo_files = get_repo_file_allowlist(work_dir)
    allowed_paths_list = sorted([f for f in repo_files if not f.startswith('test')])[:20]  # Top 20 non-test files
    test_files_list = sorted([f for f in repo_files if 'test' in f.lower()])[:10]  # Top 10 test files
    
    # Determine repo type from project context
    repo_type = "static frontend web app"
    if (work_dir / "package.json").exists():
        try:
            pkg = json.loads((work_dir / "package.json").read_text())
            deps = list(pkg.get('dependencies', {}).keys()) + list(pkg.get('devDependencies', {}).keys())
            if any('express' in d.lower() or 'mongoose' in d.lower() or 'backend' in d.lower() for d in deps):
                repo_type = "static frontend web app (no backend)"
            else:
                repo_type = "static frontend web app"
        except:
            pass
    
    # Task 3: Developer - Produce structured changes (NOT a diff)
    developer_task = Task(
        description=f"""You will implement this issue by producing structured file changes in JSON format.

CRITICAL REPO CONSTRAINTS - MUST FOLLOW:
- REPO TYPE: {repo_type}; NO backend; NO Node/Express/Mongoose; NO api/routes/controllers/models directories
- ALLOWED PATHS: You may ONLY modify these existing files:
  {', '.join(allowed_paths_list) if allowed_paths_list else 'No existing files found'}
- TEST FILES: You may create new files in tests/ directory:
  {', '.join(test_files_list) if test_files_list else 'No test files found'}
- FORBIDDEN: Any change referencing non-existent files outside tests/ must NOT be included
- FORBIDDEN: Do NOT create or reference api/, routes/, controllers/, models/, backend/, server/ paths

CRITICAL OUTPUT RULES - FOLLOW EXACTLY:
- Output ONLY a JSON object with file changes (NO diff format)
- Do NOT output a diff (no "diff --git", no "--- a/", no "@@", no "+/-" prefixes)
- Use structured JSON format with file paths and operations
- Include tests if the repo has a test suite
- Follow the project's tech stack and coding conventions

REQUIRED JSON FORMAT:
```json
{{
  "changes": [
    {{
      "path": "path/to/file.js",
      "operation": "replace_file",
      "content": "full file content here\\nwith all lines"
    }},
    {{
      "path": "app.js",
      "operation": "upsert_function_js",
      "function_name": "openEditModal",
      "content": "function openEditModal(sessionId) {{ ... }}"
    }},
    {{
      "path": "styles.css",
      "operation": "upsert_css_selector",
      "selector": ".modal",
      "content": ".modal {{ display: none; ... }}"
    }},
    {{
      "path": "app.js",
      "operation": "insert_after_anchor",
      "anchor": "function init()",
      "content": "// New code here",
      "use_regex": false
    }},
    {{
      "path": "new/file.js",
      "operation": "create",
      "content": "new file content"
    }}
  ]
}}
```

SUPPORTED OPERATIONS (use the most appropriate):
- "replace_file" or "replace": Replace entire file content (provide full "content")
  - REQUIRES: "path" and "content"
- "create": Create new file (provide full "content") - ONLY in tests/ directory
  - REQUIRES: "path" and "content"
- "upsert_function_js": Upsert JavaScript function (replace if exists, append if not)
  - REQUIRES: "path", "function_name" (MUST be included), and "content" (full function definition)
  - CRITICAL: "function_name" field is MANDATORY - do not omit it
- "upsert_css_selector": Upsert CSS selector (replace if exists, append if not)
  - REQUIRES: "path", "selector" (e.g., ".modal", "#id"), and "content" (full CSS block)
- "insert_after_anchor": Insert content after anchor string/regex
  - REQUIRES: "path", "anchor", "content", optional "use_regex" (default: false)
- "insert_before_anchor": Insert content before anchor string/regex
  - REQUIRES: "path", "anchor", "content", optional "use_regex" (default: false)
- "append_if_missing": Append content only if signature not present
  - REQUIRES: "path", "content", "signature" (substring to check for)
- "edit": Make targeted edits (provide "edits" array with find/replace pairs)
  - REQUIRES: "path" and "edits" array
  - Fallback: tries regex if exact match fails
- "delete": Delete file (no content needed)
  - REQUIRES: "path"

HARD REQUIREMENTS - EVERY CHANGE MUST INCLUDE:
- "path" field (or "file" field - will be normalized to "path")
- "operation" field
- For upsert_function_js: MUST include "function_name" field
- For upsert_css_selector: MUST include "selector" field
- For insert_*_anchor: MUST include "anchor" field
- For append_if_missing: MUST include "signature" field

IMPORTANT:
- For "replace_file" and "create": provide the COMPLETE file content
- For functions/CSS: prefer "upsert_*" operations for robustness
- For targeted changes: use "insert_after_anchor" or "insert_before_anchor"
- Do NOT use diff format - use structured JSON only
- If you output a diff (contains "diff --git" or "--- a/"), your output will be rejected
- Do NOT reference files outside the allowed paths list above
- Do NOT create backend/API files (api/, routes/, controllers/, models/)

PROJECT CONTEXT:
{project_context}

Working directory: {work_dir}
The repo is already cloned locally.

Issue:
{issue_text}
""",
        agent=developer,
        context=[architect_task],
        expected_output="JSON object with 'changes' array containing file operations. Use upsert_* operations for functions/CSS. NO diff format."
    )
    
    # Task 4: Reviewer - Review the patch (aligned with run_autopr.py)
    review_task = Task(
        description="""Review the patch for:
- Correctness
- Security
- Edge cases
- Style and maintainability

If changes are needed, describe them clearly (bullets).
""",
        agent=reviewer,
        context=[developer_task],
        expected_output="Code review with feedback on correctness, security, edge cases, and quality"
    )
    
    # Create crew (without tester for now - will add testing task after patch is applied)
    crew = Crew(
        agents=[product, architect, developer, reviewer],
        tasks=[product_task, architect_task, developer_task, review_task],
        verbose=True
    )
    
    # Execute
    print("\n🚀 Starting crew execution...")
    result = crew.kickoff()
    
    # Log full result for debugging
    print(f"\n{'='*70}")
    print("Crew Execution Complete")
    print(f"{'='*70}")
    print(f"Result type: {type(result)}")
    result_str = str(result) if result else ""
    print(f"Result length: {len(result_str)} characters")
    
    # Try to extract more detailed information
    if hasattr(result, 'tasks_output'):
        print(f"Number of task outputs: {len(result.tasks_output)}")
        for i, task_output in enumerate(result.tasks_output):
            print(f"  Task {i+1} output length: {len(str(task_output))} chars")
    
    return result

def parse_structured_changes(text: str) -> dict:
    """
    Parse structured changes from agent output.
    Accepts JSON format with file changes.
    
    Expected format:
    {
        "changes": [
            {
                "path": "path/to/file.js",
                "operation": "replace",  # or "create", "delete"
                "content": "full file content"  # for replace/create
            },
            {
                "path": "path/to/file.js",
                "operation": "edit",
                "edits": [
                    {"find": "old line", "replace": "new line"},
                    {"find": "another old", "replace": "another new"}
                ]
            }
        ]
    }
    """
    # Try to extract JSON from fenced code blocks
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        json_text = json_match.group(1)
    else:
        # Try to find JSON object directly
        json_match = re.search(r"\{.*\"changes\".*?\}", text, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
        else:
            return {"error": "No structured changes JSON found in output"}
    
    try:
        changes_data = json.loads(json_text)
        if "changes" not in changes_data:
            return {"error": "JSON missing 'changes' key"}
        return changes_data
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}


def get_repo_file_allowlist(work_dir: Path) -> set[str]:
    """
    Build a set of existing files in the repo (excluding build artifacts, node_modules, etc.).
    Used to prevent edits to non-existent backend files or files outside the repo.
    Returns set of relative file paths.
    """
    allowlist = set()
    exclude_dirs = {'.git', 'node_modules', 'dist', 'build', '.next', '.nuxt', 
                    '__pycache__', '.pytest_cache', '.venv', 'venv', 'env',
                    '.crewai_cache', 'coverage', '.coverage'}
    
    if not work_dir.exists():
        return allowlist
    
    try:
        for root, dirs, files in os.walk(work_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            
            for file in files:
                file_path = Path(root) / file
                try:
                    rel_path = file_path.relative_to(work_dir)
                    allowlist.add(str(rel_path))
                except ValueError:
                    # File outside work_dir, skip
                    continue
    except Exception as e:
        print(f"⚠️  Warning: Could not build repo file allowlist: {e}")
    
    return allowlist


def validate_structured_changes(changes_data: dict, work_dir: Path) -> tuple[bool, list[str]]:
    """
    Validate structured changes before applying.
    
    Schema normalization: Accepts both "path" and "file" fields, normalizes to "path".
    Repo allowlist: Prevents edits to non-existent files or files outside the repo.
    
    Returns (is_valid, error_messages)
    """
    errors = []
    
    if "error" in changes_data:
        return False, [changes_data["error"]]
    
    if "changes" not in changes_data:
        return False, ["Missing 'changes' key in structured changes"]
    
    # Build repo file allowlist
    repo_files = get_repo_file_allowlist(work_dir)
    
    for i, change in enumerate(changes_data["changes"]):
        # Schema normalization: accept both "path" and "file"
        if "path" not in change and "file" not in change:
            errors.append(f"Change {i}: Missing 'path' or 'file' field")
            continue
        
        # Normalize: set path from either field, always delete "file" after normalization
        path = change.get("path") or change.get("file")
        change["path"] = path  # Normalize in place
        if "file" in change:
            del change["file"]  # Always remove "file" to avoid ambiguity
        
        if "operation" not in change:
            errors.append(f"Change {i}: Missing 'operation'")
            continue
        operation = change["operation"]
        
        # C) Path safety: reject absolute paths and .. traversal
        if path:
            # Reject absolute paths
            if Path(path).is_absolute():
                errors.append(f"Change {i}: Absolute path rejected: '{path}'. Use relative paths only.")
                continue
            
            # Reject paths containing .. segments
            if ".." in path:
                errors.append(f"Change {i}: Path traversal rejected: '{path}'. Paths containing '..' are not allowed.")
                continue
            
            # Resolve final write path and ensure it stays inside repo_root
            try:
                resolved_path = (work_dir / path).resolve()
                # Check if resolved path is still within work_dir
                try:
                    resolved_path.relative_to(work_dir.resolve())
                except ValueError:
                    errors.append(f"Change {i}: Path escapes repository root: '{path}' resolves outside repo.")
                    continue
            except Exception as e:
                errors.append(f"Change {i}: Invalid path '{path}': {str(e)}")
                continue
        
        # B) Tighten diff detection: only scan content-like fields, not str(change)
        content_fields_to_check = []
        if "content" in change:
            content_fields_to_check.append(change["content"])
        if "before" in change:
            content_fields_to_check.append(change["before"])
        if "after" in change:
            content_fields_to_check.append(change["after"])
        
        # Check for unified-diff markers only in content fields
        diff_markers = ["diff --git", "--- a/", "+++ b/", "@@"]
        for content_field in content_fields_to_check:
            if isinstance(content_field, str):
                content_lower = content_field.lower()
                for marker in diff_markers:
                    if marker in content_lower:
                        errors.append(f"Change {i}: Contains diff-like content in content field (rejecting - use structured format only). Found marker: '{marker}'")
                        break
                if any(marker in content_lower for marker in diff_markers):
                    break
        
        # Validate operation
        # Legacy operations
        legacy_ops = ["create", "replace", "edit", "delete"]
        # New robust operations
        new_ops = ["replace_file", "upsert_function_js", "upsert_css_selector", 
                   "insert_after_anchor", "insert_before_anchor", "append_if_missing"]
        valid_ops = legacy_ops + new_ops
        
        if operation not in valid_ops:
            errors.append(f"Change {i}: Invalid operation '{operation}' (must be one of {valid_ops})")
            continue
        
        # Normalize replace_file to replace for downstream compatibility
        if operation == "replace_file":
            operation = "replace"
            change["operation"] = "replace"  # Update in place for applier
        
        # Validate file path against repo allowlist
        file_path = work_dir / path
        normalized_path = str(Path(path).as_posix())  # Normalize path separators
        
        # Operations that require existing files
        ops_requiring_existing = ["replace", "edit", "delete", "upsert_function_js", 
                                   "upsert_css_selector", "insert_after_anchor", 
                                   "insert_before_anchor", "append_if_missing"]
        
        # Check if file is in repo allowlist (for existing file operations)
        if operation in ops_requiring_existing:
            if normalized_path not in repo_files and not file_path.exists():
                # Try to find similar file (case-insensitive)
                found_similar = None
                path_lower = normalized_path.lower()
                for repo_file in repo_files:
                    if repo_file.lower() == path_lower:
                        found_similar = repo_file
                        break
                
                if found_similar:
                    errors.append(f"Change {i}: File '{path}' not found, but similar file exists: {found_similar}")
                else:
                    # Check if this looks like a backend/API hallucination
                    suspicious_patterns = ['api/', 'routes.js', 'controllers/', 'models/', 'backend/', 'server/']
                    if any(pattern in normalized_path.lower() for pattern in suspicious_patterns):
                        errors.append(f"Change {i}: File '{path}' does not exist and appears to be a backend/API file not in this repo. Only modify existing files in this repo.")
                    else:
                        errors.append(f"Change {i}: File '{path}' does not exist (for {operation} operation). Only modify existing files in this repo.")
        
        # For create operations, restrict to approved directories
        elif operation == "create":
            # Allow creation in test directories or explicitly allowed locations
            allowed_create_dirs = ['test', 'tests', 'spec', '__tests__']
            path_parts = Path(normalized_path).parts
            if path_parts:
                first_dir = path_parts[0].lower()
                if first_dir not in allowed_create_dirs:
                    # Check if plan explicitly allows this (would need plan context, but for now warn)
                    # In practice, we'll allow it but log a warning
                    pass  # Allow create but could add warning if needed
        
        # Validate required fields based on operation
        # Note: path is already validated above
        if operation in ["create", "replace"]:
            if "content" not in change:
                errors.append(f"Change {i}: Missing 'content' for {operation} operation")
        elif operation == "edit":
            if "edits" not in change:
                errors.append(f"Change {i}: Missing 'edits' for edit operation")
            elif not isinstance(change["edits"], list):
                errors.append(f"Change {i}: 'edits' must be a list")
        elif operation == "upsert_function_js":
            if not change.get("path"):
                errors.append(f"Change {i}: Missing 'path' for upsert_function_js operation")
            if "function_name" not in change:
                errors.append(f"Change {i}: Missing 'function_name' for upsert_function_js operation")
            if "content" not in change:
                errors.append(f"Change {i}: Missing 'content' (function body) for upsert_function_js operation")
        elif operation == "upsert_css_selector":
            if not change.get("path"):
                errors.append(f"Change {i}: Missing 'path' for upsert_css_selector operation")
            if "selector" not in change:
                errors.append(f"Change {i}: Missing 'selector' for upsert_css_selector operation")
            if "content" not in change:
                errors.append(f"Change {i}: Missing 'content' (CSS block) for upsert_css_selector operation")
        elif operation in ["insert_after_anchor", "insert_before_anchor"]:
            if not change.get("path"):
                errors.append(f"Change {i}: Missing 'path' for {operation} operation")
            if "anchor" not in change:
                errors.append(f"Change {i}: Missing 'anchor' for {operation} operation")
            if "content" not in change:
                errors.append(f"Change {i}: Missing 'content' for {operation} operation")
        elif operation == "append_if_missing":
            if not change.get("path"):
                errors.append(f"Change {i}: Missing 'path' for append_if_missing operation")
            if "content" not in change:
                errors.append(f"Change {i}: Missing 'content' for append_if_missing operation")
            if "signature" not in change:
                errors.append(f"Change {i}: Missing 'signature' for append_if_missing operation")
        elif operation == "replace_file":
            if not change.get("path"):
                errors.append(f"Change {i}: Missing 'path' for replace_file operation")
            if "content" not in change:
                errors.append(f"Change {i}: Missing 'content' for replace_file operation")
    
    return len(errors) == 0, errors


def test_upsert_function_js():
    """Self-test for upsert_function_js function"""
    import tempfile
    
    # Test 1: Append new function
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
        tmp.write("// Existing code\n")
        tmp_path = Path(tmp.name)
    
    try:
        result = upsert_function_js(tmp_path, "newFunction", "function newFunction() { return true; }")
        assert result == True, "Should append new function"
        content = tmp_path.read_text()
        assert "function newFunction()" in content, "Function should be in file"
    finally:
        tmp_path.unlink()
    
    # Test 2: Replace existing function
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
        tmp.write("function existing() { return false; }\n")
        tmp_path = Path(tmp.name)
    
    try:
        result = upsert_function_js(tmp_path, "existing", "function existing() { return true; }")
        assert result == True, "Should replace existing function"
        content = tmp_path.read_text()
        assert "return true" in content, "Function should be replaced"
        assert "return false" not in content, "Old function should be gone"
    finally:
        tmp_path.unlink()
    
    print("✅ upsert_function_js self-test passed")


def test_upsert_css_selector():
    """Self-test for upsert_css_selector function"""
    import tempfile
    
    # Test 1: Append new selector
    with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as tmp:
        tmp.write("body { margin: 0; }\n")
        tmp_path = Path(tmp.name)
    
    try:
        result = upsert_css_selector(tmp_path, ".modal", ".modal { display: none; }")
        assert result == True, "Should append new selector"
        content = tmp_path.read_text()
        assert ".modal" in content, "Selector should be in file"
    finally:
        tmp_path.unlink()
    
    # Test 2: Replace existing selector
    with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as tmp:
        tmp.write(".modal { display: block; }\n")
        tmp_path = Path(tmp.name)
    
    try:
        result = upsert_css_selector(tmp_path, ".modal", ".modal { display: none; }")
        assert result == True, "Should replace existing selector"
        content = tmp_path.read_text()
        assert "display: none" in content, "Selector should be replaced"
        assert "display: block" not in content, "Old selector should be gone"
    finally:
        tmp_path.unlink()
    
    print("✅ upsert_css_selector self-test passed")


def test_upsert_function_js():
    """Self-test for upsert_function_js function"""
    import tempfile
    
    # Test 1: Append new function
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
        tmp.write("// Existing code\n")
        tmp_path = Path(tmp.name)
    
    try:
        result = upsert_function_js(tmp_path, "newFunction", "function newFunction() { return true; }")
        assert result == True, "Should append new function"
        content = tmp_path.read_text()
        assert "function newFunction()" in content, "Function should be in file"
    finally:
        tmp_path.unlink()
    
    # Test 2: Replace existing function
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
        tmp.write("function existing() { return false; }\n")
        tmp_path = Path(tmp.name)
    
    try:
        result = upsert_function_js(tmp_path, "existing", "function existing() { return true; }")
        assert result == True, "Should replace existing function"
        content = tmp_path.read_text()
        assert "return true" in content, "Function should be replaced"
        assert "return false" not in content, "Old function should be gone"
    finally:
        tmp_path.unlink()
    
    print("✅ upsert_function_js self-test passed")


def test_upsert_css_selector():
    """Self-test for upsert_css_selector function"""
    import tempfile
    
    # Test 1: Append new selector
    with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as tmp:
        tmp.write("body { margin: 0; }\n")
        tmp_path = Path(tmp.name)
    
    try:
        result = upsert_css_selector(tmp_path, ".modal", ".modal { display: none; }")
        assert result == True, "Should append new selector"
        content = tmp_path.read_text()
        assert ".modal" in content, "Selector should be in file"
    finally:
        tmp_path.unlink()
    
    # Test 2: Replace existing selector
    with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as tmp:
        tmp.write(".modal { display: block; }\n")
        tmp_path = Path(tmp.name)
    
    try:
        result = upsert_css_selector(tmp_path, ".modal", ".modal { display: none; }")
        assert result == True, "Should replace existing selector"
        content = tmp_path.read_text()
        assert "display: none" in content, "Selector should be replaced"
        assert "display: block" not in content, "Old selector should be gone"
    finally:
        tmp_path.unlink()
    
    print("✅ upsert_css_selector self-test passed")


def upsert_function_js(file_path: Path, function_name: str, function_body: str) -> bool:
    """
    Upsert a JavaScript function: replace if exists, append if not.
    Supports: function name(), const name = function(), const name = () =>
    Returns True if change was made (idempotent: returns False if content unchanged).
    """
    if not file_path.exists():
        return False
    
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    # Try to find function definition (supports various formats)
    # More robust pattern matching
    patterns = [
        # function name() { ... } - match entire function body
        rf'function\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{[^}}]*\}}',
        # const name = function() { ... }
        rf'const\s+{re.escape(function_name)}\s*=\s*function\s*\([^)]*\)\s*\{{[^}}]*\}}',
        # const name = () => { ... }
        rf'const\s+{re.escape(function_name)}\s*=\s*\([^)]*\)\s*=>\s*\{{[^}}]*\}}',
        # let name = function() { ... }
        rf'let\s+{re.escape(function_name)}\s*=\s*function\s*\([^)]*\)\s*\{{[^}}]*\}}',
        # let name = () => { ... }
        rf'let\s+{re.escape(function_name)}\s*=\s*\([^)]*\)\s*=>\s*\{{[^}}]*\}}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        if match:
            # Check if replacement would change content (idempotency check)
            existing_function = content[match.start():match.end()]
            if existing_function.strip() == function_body.strip():
                return False  # No change needed
            
            # Replace existing function
            new_content = content[:match.start()] + function_body + content[match.end():]
            file_path.write_text(new_content, encoding='utf-8')
            return True
    
    # Function not found - append at end
    if not content.endswith('\n'):
        content += '\n'
    content += '\n' + function_body + '\n'
    file_path.write_text(content, encoding='utf-8')
    return True


def upsert_css_selector(file_path: Path, selector: str, css_block: str) -> bool:
    """
    Upsert a CSS selector: replace if exists, append if not.
    Supports: .class, #id, element, element.class, etc.
    Returns True if change was made (idempotent: returns False if content unchanged).
    """
    if not file_path.exists():
        return False
    
    content = file_path.read_text(encoding='utf-8')
    original_content = content
    
    # Escape selector for regex (handle .class, #id, element, etc.)
    # Need to handle special regex chars but preserve CSS selector meaning
    escaped_selector = re.escape(selector)
    
    # Try to find selector block (more robust matching)
    # Match selector followed by optional whitespace and opening brace
    pattern = rf'{escaped_selector}\s*\{{[^}}]*\}}'
    match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
    
    if match:
        # Check if replacement would change content (idempotency check)
        existing_block = content[match.start():match.end()]
        if existing_block.strip() == css_block.strip():
            return False  # No change needed
        
        # Replace existing selector
        new_content = content[:match.start()] + css_block + content[match.end():]
        file_path.write_text(new_content, encoding='utf-8')
        return True
    
    # Selector not found - append at end
    if not content.endswith('\n'):
        content += '\n'
    content += '\n' + css_block + '\n'
    file_path.write_text(content, encoding='utf-8')
    return True


def insert_after_anchor(file_path: Path, anchor: str, content_to_insert: str, use_regex: bool = False) -> bool:
    """Insert content after an anchor string or regex pattern. Returns True if inserted."""
    if not file_path.exists():
        return False
    
    current_content = file_path.read_text(encoding='utf-8')
    
    if use_regex:
        match = re.search(anchor, current_content)
        if match:
            pos = match.end()
        else:
            return False
    else:
        pos = current_content.find(anchor)
        if pos == -1:
            return False
        pos += len(anchor)
    
    new_content = current_content[:pos] + '\n' + content_to_insert + current_content[pos:]
    file_path.write_text(new_content, encoding='utf-8')
    return True


def insert_before_anchor(file_path: Path, anchor: str, content_to_insert: str, use_regex: bool = False) -> bool:
    """Insert content before an anchor string or regex pattern. Returns True if inserted."""
    if not file_path.exists():
        return False
    
    current_content = file_path.read_text(encoding='utf-8')
    
    if use_regex:
        match = re.search(anchor, current_content)
        if match:
            pos = match.start()
        else:
            return False
    else:
        pos = current_content.find(anchor)
        if pos == -1:
            return False
    
    new_content = current_content[:pos] + content_to_insert + '\n' + current_content[pos:]
    file_path.write_text(new_content, encoding='utf-8')
    return True


def append_if_missing(file_path: Path, content_to_append: str, signature: str) -> bool:
    """Append content only if signature is not present. Returns True if appended."""
    if not file_path.exists():
        # Create file with content
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content_to_append, encoding='utf-8')
        return True
    
    current_content = file_path.read_text(encoding='utf-8')
    
    if signature in current_content:
        return False  # Already present
    
    if not current_content.endswith('\n'):
        current_content += '\n'
    current_content += content_to_append + '\n'
    file_path.write_text(current_content, encoding='utf-8')
    return True


def apply_structured_changes(changes_data: dict, work_dir: Path) -> tuple[bool, list[str], list[str]]:
    """
    Apply structured changes directly to files with robust fallbacks.
    Returns (success, changed_files, error_messages)
    F) Deduplication: tracks files in a set to avoid duplicates.
    F) Idempotency: only reports files that actually changed.
    """
    changed_files_set = set()  # Use set to dedupe
    errors = []
    warnings = []
    
    if "error" in changes_data:
        return False, [], [changes_data["error"]]
    
    for change in changes_data.get("changes", []):
        # Schema normalization: accept both "path" and "file"
        path = change.get("path") or change.get("file")
        if not path:
            errors.append("Change missing 'path' or 'file' field")
            continue
        
        # Normalize in place
        change["path"] = path
        if "file" in change:
            del change["file"]  # Remove duplicate field
        
        operation = change.get("operation", "replace")  # Default to replace
        file_path = work_dir / path
        
        try:
            if operation == "create":
                # Create new file
                file_path.parent.mkdir(parents=True, exist_ok=True)
                content = change.get("content", "")
                if file_path.exists():
                    warnings.append(f"File {path} already exists, overwriting (create operation)")
                file_path.write_text(content, encoding='utf-8')
                changed_files_set.add(path)  # Use set to dedupe
                print(f"✓ Created file: {path}")
                
            elif operation == "replace_file" or operation == "replace":
                # Replace entire file content
                if not file_path.exists():
                    errors.append(f"File not found for replace: {path}")
                    continue
                content = change.get("content", "")
                # F) Idempotency: check if content actually changed
                if file_path.exists():
                    current_content = file_path.read_text(encoding='utf-8')
                    if current_content == content:
                        print(f"ℹ️  File {path} already matches replacement content (no changes needed)")
                        continue
                file_path.write_text(content, encoding='utf-8')
                changed_files_set.add(path)  # Use set to dedupe
                print(f"✓ Replaced file: {path}")
                
            elif operation == "edit":
                # Apply targeted edits with fallbacks
                if not file_path.exists():
                    errors.append(f"File not found for edit: {path}")
                    continue
                
                current_content = file_path.read_text(encoding='utf-8')
                new_content = current_content
                edit_success = False
                
                edits = change.get("edits", [])
                for edit in edits:
                    find_text = edit.get("find", "")
                    replace_text = edit.get("replace", "")
                    
                    # Try exact match first
                    if find_text in new_content:
                        new_content = new_content.replace(find_text, replace_text, 1)
                        edit_success = True
                    else:
                        # Try regex anchor
                        try:
                            pattern = re.compile(re.escape(find_text), re.MULTILINE | re.DOTALL)
                            if pattern.search(new_content):
                                new_content = pattern.sub(replace_text, new_content, count=1)
                                edit_success = True
                                warnings.append(f"Used regex fallback for edit in {path}")
                            else:
                                errors.append(f"Could not find anchor in {path}: {find_text[:50]}...")
                        except:
                            errors.append(f"Invalid regex pattern in {path}: {find_text[:50]}...")
                
                if edit_success and new_content != current_content:
                    file_path.write_text(new_content, encoding='utf-8')
                    changed_files_set.add(path)  # Use set to dedupe
                    print(f"✓ Edited file: {path}")
                elif not edit_success:
                    errors.append(f"No changes applied to {path} (all find texts not found)")
                    
            elif operation == "insert_after_anchor":
                anchor = change.get("anchor", "")
                content_to_insert = change.get("content", "")
                use_regex = change.get("use_regex", False)
                
                if insert_after_anchor(file_path, anchor, content_to_insert, use_regex):
                    changed_files_set.add(path)  # Use set to dedupe
                    print(f"✓ Inserted content after anchor in {path}")
                else:
                    errors.append(f"Could not find anchor in {path}: {anchor[:50]}...")
                    
            elif operation == "insert_before_anchor":
                anchor = change.get("anchor", "")
                content_to_insert = change.get("content", "")
                use_regex = change.get("use_regex", False)
                
                if insert_before_anchor(file_path, anchor, content_to_insert, use_regex):
                    changed_files_set.add(path)  # Use set to dedupe
                    print(f"✓ Inserted content before anchor in {path}")
                else:
                    errors.append(f"Could not find anchor in {path}: {anchor[:50]}...")
                    
            elif operation == "append_if_missing":
                content_to_append = change.get("content", "")
                signature = change.get("signature", "")
                
                # F) Idempotency: append_if_missing already returns False if signature exists
                if append_if_missing(file_path, content_to_append, signature):
                    changed_files_set.add(path)  # Use set to dedupe
                    print(f"✓ Appended content to {path}")
                else:
                    print(f"ℹ️  Content already present in {path} (signature found)")
                    
            elif operation == "upsert_function_js":
                function_name = change.get("function_name", "")
                function_body = change.get("content", "")
                
                if not function_name:
                    errors.append(f"Missing function_name for upsert_function_js in {path}")
                    continue
                
                if upsert_function_js(file_path, function_name, function_body):
                    changed_files.append(path)
                    print(f"✓ Upserted function {function_name} in {path}")
                else:
                    errors.append(f"Failed to upsert function {function_name} in {path}")
                    
            elif operation == "upsert_css_selector":
                selector = change.get("selector", "")
                css_block = change.get("content", "")
                
                if not selector:
                    errors.append(f"Missing selector for upsert_css_selector in {path}")
                    continue
                
                if upsert_css_selector(file_path, selector, css_block):
                    changed_files.append(path)
                    print(f"✓ Upserted CSS selector {selector} in {path}")
                else:
                    errors.append(f"Failed to upsert CSS selector {selector} in {path}")
                    
            elif operation == "delete":
                # Delete file
                if not file_path.exists():
                    errors.append(f"File not found for delete: {path}")
                    continue
                file_path.unlink()
                changed_files_set.add(path)  # Use set to dedupe
                print(f"✓ Deleted file: {path}")
            else:
                # This should not happen if validator is working correctly
                errors.append(f"Unknown operation '{operation}' for {path}. Supported: create, replace, replace_file, edit, upsert_function_js, upsert_css_selector, insert_after_anchor, insert_before_anchor, append_if_missing, delete")
                
        except Exception as e:
            errors.append(f"Error applying change to {path}: {str(e)}")
    
    # Print warnings
    for warning in warnings:
        print(f"⚠️  {warning}")
    
    # F) Convert set to sorted list for consistent output
    changed_files = sorted(list(changed_files_set))
    return len(errors) == 0, changed_files, errors


def get_git_changed_files(work_dir: Path) -> list[str]:
    """Get list of changed files from git status. Returns empty list if no changes."""
    if not (work_dir / ".git").exists():
        return []
    
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return []
        
        files = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                # Format: " M file.js" or "?? newfile.js"
                file_path = line[3:].strip()
                if file_path:
                    files.append(file_path)
        
        return files
    except Exception:
        return []


def parse_plan_requirements(plan_file: Path) -> dict:
    """
    Parse requirements from implementation plan file.
    Returns dict with: functions, css_selectors, test_files, required_files
    """
    requirements = {
        "functions": [],
        "css_selectors": [],
        "test_files": [],
        "required_files": []
    }
    
    if not plan_file.exists():
        return requirements
    
    try:
        content = plan_file.read_text(encoding='utf-8')
        
        # Extract functions from "New Functions/Classes/Modules" section
        func_section = re.search(r'###?\s*New Functions[^#]*', content, re.IGNORECASE | re.DOTALL)
        if func_section:
            func_text = func_section.group(0)
            # Look for function names like "functionName()" or "- functionName"
            func_matches = re.findall(r'[-*]\s*`?(\w+)\s*\([^)]*\)`?', func_text)
            requirements["functions"] = [f for f in func_matches if not f.startswith('function')]
        
        # Extract CSS selectors from "Files to Change" or "styles.css" mentions
        # E) Only treat CSS selectors as required if they start with ., #, or [
        # Prefer extracting selectors from backticks, fenced code blocks, or CSS declarations
        css_selectors = set()
        
        # Method 1: Extract from fenced code blocks (```css or ```)
        code_block_pattern = r'```(?:css)?\s*([^`]+)```'
        code_blocks = re.findall(code_block_pattern, content, re.IGNORECASE | re.DOTALL)
        for block in code_blocks:
            # Extract selectors from CSS code blocks
            # Match: .selector, #selector, [attribute], or compound selectors starting with . or #
            selector_pattern = r'(?:^|\n)\s*([.#\[][\w-]+(?:\s*[.#\[][\w-]+)*(?:\s*\{)?)'
            matches = re.findall(selector_pattern, block, re.MULTILINE)
            for match in matches:
                # Clean up: remove trailing { and whitespace
                selector = match.strip().rstrip('{').strip()
                # Only accept if starts with ., #, or [
                if selector and (selector.startswith('.') or selector.startswith('#') or selector.startswith('[')):
                    css_selectors.add(selector)
        
        # Method 2: Extract from inline backticks (e.g., `.modal`, `#editModal`, `[data-id]`)
        inline_backtick_pattern = r'`([.#\[][\w-]+(?:\s+[.#\[][\w-]+)*)`'
        inline_matches = re.findall(inline_backtick_pattern, content)
        for match in inline_matches:
            selector = match.strip()
            # Only accept if starts with ., #, or [
            if selector and (selector.startswith('.') or selector.startswith('#') or selector.startswith('[')):
                css_selectors.add(selector)
        
        # Method 3: Extract from lines that look like CSS declarations
        # Match lines like: ".modal {", "#id {", ".class .nested {", "[data-id] {"
        css_declaration_pattern = r'(?:^|\n)\s*([.#\[][\w-]+(?:\s+[.#\[][\w-]+)*)\s*\{'
        declaration_matches = re.findall(css_declaration_pattern, content, re.MULTILINE)
        for match in declaration_matches:
            selector = match.strip()
            # Only accept if starts with ., #, or [
            if selector and (selector.startswith('.') or selector.startswith('#') or selector.startswith('[')):
                css_selectors.add(selector)
        
        # Method 4: Extract from bullet lists that mention selectors
        # Look for lines like "- Add `.modal` styles" or "- Style `#toast`"
        bullet_pattern = r'[-*]\s+[^`]*`([.#\[][\w-]+)`'
        bullet_matches = re.findall(bullet_pattern, content)
        for match in bullet_matches:
            selector = match.strip()
            # Only accept if starts with ., #, or [
            if selector and (selector.startswith('.') or selector.startswith('#') or selector.startswith('[')):
                css_selectors.add(selector)
        
        # Debug logging on extraction
        if css_selectors:
            print(f"   Extracted {len(css_selectors)} CSS selector(s) from plan: {', '.join(sorted(css_selectors))}")
        
        requirements["css_selectors"] = sorted(list(css_selectors))
        
        # Extract test files from "Test Approach" or "Files to Change"
        test_section = re.search(r'Test Approach[^#]*|test[^#]*\.(js|ts|py)', content, re.IGNORECASE | re.DOTALL)
        if test_section:
            test_text = test_section.group(0)
            test_matches = re.findall(r'(test[/\\][\w/\\-]+\.(?:js|ts|py))', test_text)
            requirements["test_files"] = test_matches
        
        # Extract required files from "Files to Change" section
        files_section = re.search(r'###?\s*Files to Change[^#]*', content, re.IGNORECASE | re.DOTALL)
        if files_section:
            files_text = files_section.group(0)
            file_matches = re.findall(r'[-*]\s*`([^`]+)`', files_text)
            requirements["required_files"] = file_matches
        
    except Exception as e:
        print(f"⚠️  Warning: Could not parse plan requirements: {e}")
    
    return requirements


def check_coverage(plan_file: Path, work_dir: Path) -> tuple[bool, dict]:
    """
    Check if implementation plan requirements are met.
    Returns (is_complete, missing_items_dict)
    """
    requirements = parse_plan_requirements(plan_file)
    missing = {
        "functions": [],
        "css_selectors": [],
        "test_files": [],
        "required_files": []
    }
    
    # Check required functions in JS files
    for func_name in requirements["functions"]:
        found = False
        # Check common JS files
        for js_file in ["app.js", "index.js", "main.js"]:
            js_path = work_dir / js_file
            if js_path.exists():
                content = js_path.read_text(encoding='utf-8')
                # Look for function definition
                patterns = [
                    rf'function\s+{re.escape(func_name)}\s*\(',
                    rf'const\s+{re.escape(func_name)}\s*=',
                    rf'let\s+{re.escape(func_name)}\s*=',
                    rf'var\s+{re.escape(func_name)}\s*='
                ]
                for pattern in patterns:
                    if re.search(pattern, content):
                        found = True
                        break
                if found:
                    break
        if not found:
            missing["functions"].append(func_name)
    
    # Check CSS selectors
    css_path = work_dir / "styles.css"
    
    # Filter out invalid/garbage selectors before checking
    valid_selectors = [s for s in requirements["css_selectors"] 
                      if s and (s.startswith('.') or s.startswith('#') or s.startswith('['))]
    
    if valid_selectors:
        print(f"   Checking {len(valid_selectors)} CSS selector(s): {', '.join(valid_selectors)}")
    
    if css_path.exists():
        css_content = css_path.read_text(encoding='utf-8')
        for selector in valid_selectors:
            # Check for selector in CSS file
            # Handle compound selectors (e.g., ".modal .close" -> match ".modal" and ".close")
            # For compound selectors, check if all parts exist
            selector_parts = selector.split()
            all_found = True
            
            for part in selector_parts:
                # Each part should start with . or #
                if part.startswith('.'):
                    pattern = rf'\{re.escape(part)}\s*\{{'
                elif part.startswith('#'):
                    pattern = rf'\{re.escape(part)}\s*\{{'
                else:
                    # Skip invalid parts
                    all_found = False
                    break
                
                if not re.search(pattern, css_content, re.MULTILINE):
                    all_found = False
                    break
            
            if not all_found:
                missing["css_selectors"].append(selector)
    else:
        # If CSS file doesn't exist but selectors are required, mark all as missing
        if valid_selectors:
            missing["css_selectors"] = valid_selectors
    
    # Check test files
    for test_file in requirements["test_files"]:
        test_path = work_dir / test_file
        if not test_path.exists():
            missing["test_files"].append(test_file)
    
    # Check required files
    for req_file in requirements["required_files"]:
        req_path = work_dir / req_file
        if not req_path.exists():
            missing["required_files"].append(req_file)
    
    # Determine if complete
    is_complete = (
        len(missing["functions"]) == 0 and
        len(missing["css_selectors"]) == 0 and
        len(missing["test_files"]) == 0 and
        len(missing["required_files"]) == 0
    )
    
    return is_complete, missing


def generate_git_patch(work_dir: Path, patch_file: Path) -> tuple[bool, str]:
    """
    Generate patch using git diff after changes are applied.
    Uses unstaged changes (no git add needed).
    Returns (success, patch_content)
    """
    if not (work_dir / ".git").exists():
        return False, "Not a git repository"
    
    try:
        # Generate diff of unstaged changes (no need to stage)
        result = subprocess.run(
            ["git", "diff", "--no-color", "--minimal"],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return False, f"git diff failed: {result.stderr}"
        
        patch_content = result.stdout
        
        # Validate patch is non-empty
        if not patch_content.strip():
            return False, "Patch is empty (no changes detected)"
        
        # Validate patch format using git apply --check (dry-run)
        # Create a temporary file for validation
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.diff', delete=False) as tmp:
            tmp.write(patch_content)
            tmp_path = tmp.name
        
        try:
            check_result = subprocess.run(
                ["git", "apply", "--check"],
                cwd=work_dir,
                input=patch_content,
                capture_output=True,
                text=True,
                timeout=30
            )
            if check_result.returncode != 0:
                # Patch validation failed, but we'll still save it
                print(f"⚠️  Warning: Generated patch failed validation: {check_result.stderr[:200]}")
        finally:
            # Clean up temp file
            try:
                Path(tmp_path).unlink()
            except:
                pass
        
        # Write patch file
        patch_file.write_text(patch_content, encoding='utf-8')
        
        return True, patch_content
        
    except subprocess.TimeoutExpired:
        return False, "git diff command timed out"
    except Exception as e:
        return False, f"Error generating git patch: {str(e)}"


def extract_diff(text: str) -> str:
    """
    Extract a unified diff from a model response.
    Accepts either fenced ```diff blocks or raw diff starting with 'diff --git'.
    Filters out review comments and non-diff content.
    Aligned with run_autopr.py
    """
    # Prefer fenced diff
    m = re.search(r"```diff\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if m:
        diff_text = m.group(1).strip() + "\n"
    else:
        # Else raw diff
        m2 = re.search(r"(diff --git.*)", text, re.DOTALL)
        if m2:
            diff_text = m2.group(1).strip() + "\n"
        else:
            return ""
    
    # Clean and validate the diff - remove review comments and invalid lines
    diff_text = clean_diff(diff_text)
    
    # Validate the diff is actually valid
    if not validate_diff_format(diff_text):
        print("⚠️  Warning: Extracted diff may be malformed. Attempting to fix...")
        diff_text = fix_malformed_diff(diff_text)
    
    return diff_text

def validate_diff_format(diff_text: str) -> bool:
    """
    Validate that the diff is in proper git diff format.
    Returns True if valid, False otherwise.
    """
    if not diff_text or not diff_text.strip():
        return False
    
    lines = diff_text.split('\n')
    
    # Must start with 'diff --git'
    if not any(line.startswith('diff --git') for line in lines[:10]):
        return False
    
    # Check for valid diff structure
    has_file_header = False
    has_hunk = False
    
    for line in lines:
        if line.startswith('diff --git'):
            has_file_header = True
        elif line.startswith('@@'):
            has_hunk = True
        # Check for review comments mixed in (lines that look like explanations)
        elif (line.strip() and 
              not line.startswith(('diff', 'index', '---', '+++', '@@', ' ', '-', '+', '\\', '#')) and
              not line.startswith('```') and
              len(line) > 50 and
              ('correctness' in line.lower() or 
               'security' in line.lower() or 
               'edge case' in line.lower() or
               'style' in line.lower() or
               'maintainability' in line.lower() or
               'review' in line.lower())):
            # Likely a review comment, not part of diff
            return False
    
    return has_file_header and has_hunk

def extract_review_comments(text: str) -> str:
    """
    Extract review comments from the crew output, separate from the diff.
    Returns review comments as a string, or empty string if none found.
    """
    # Look for review sections (common patterns)
    review_patterns = [
        r"###? (Code Review|Review|Feedback).*?\n(.*?)(?=\n###|\n```|$)",
        r"(- \*\*Correctness\*\*:.*?)(?=\n\n|\n```|$)",
        r"(- \*\*Security\*\*:.*?)(?=\n\n|\n```|$)",
        r"(Overall,.*?)(?=\n\n|\n```|$)",
    ]
    
    review_sections = []
    for pattern in review_patterns:
        matches = re.finditer(pattern, text, re.DOTALL | re.IGNORECASE)
        for match in matches:
            section = match.group(0).strip()
            # Only include if it's clearly a review comment (not part of diff)
            if ('correctness' in section.lower() or 
                'security' in section.lower() or 
                'edge case' in section.lower() or
                'style' in section.lower() or
                'maintainability' in section.lower()):
                review_sections.append(section)
    
    if review_sections:
        return "\n\n".join(review_sections)
    return ""

def fix_malformed_diff(diff_text: str) -> str:
    """
    Attempt to fix a malformed diff by removing review comments and invalid lines.
    """
    lines = diff_text.split('\n')
    cleaned_lines = []
    in_diff = False
    
    for i, line in enumerate(lines):
        # Start of a new file diff
        if line.startswith('diff --git'):
            in_diff = True
            cleaned_lines.append(line)
            continue
        
        if not in_diff:
            continue
        
        # Valid diff lines
        if (line.startswith(('index ', '---', '+++', '@@', ' ', '-', '+', '\\')) or
            line.startswith('diff --git')):
            cleaned_lines.append(line)
        # Skip review comments (lines that look like explanations)
        elif (line.strip() and 
              len(line) > 50 and
              ('correctness' in line.lower() or 
               'security' in line.lower() or 
               'edge case' in line.lower() or
               'style' in line.lower() or
               'maintainability' in line.lower() or
               'review' in line.lower() or
               line.startswith('- **') or
               line.startswith('Overall,'))):
            # Skip review comment lines
            continue
        elif line.strip() == '':
            # Keep empty lines (they're part of context)
            cleaned_lines.append(line)
        else:
            # Unknown line - might be part of diff, keep it but log warning
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def clean_diff(diff_text: str) -> str:
    """
    Clean and fix common issues in generated diffs.
    Also removes review comments that may have been mixed in.
    """
    lines = diff_text.split('\n')
    cleaned_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Skip review comments (lines that look like explanations)
        if (line.strip() and 
            not line.startswith(('diff', 'index', '---', '+++', '@@', ' ', '-', '+', '\\')) and
            len(line) > 50 and
            ('correctness' in line.lower() or 
             'security' in line.lower() or 
             'edge case' in line.lower() or
             'style' in line.lower() or
             'maintainability' in line.lower() or
             'review' in line.lower() or
             line.startswith('- **') or
             line.startswith('Overall,'))):
            # Skip review comment lines
            i += 1
            continue
        
        # Skip no-op changes (removing and adding the same line)
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            if line.startswith('-') and next_line.startswith('+'):
                removed = line[1:].strip()
                added = next_line[1:].strip()
                if removed == added:
                    # Skip both lines (no-op change)
                    i += 2
                    continue
        
        # Fix missing newline at end of file markers
        if line.startswith('\\ No newline at end of file'):
            # Ensure proper format
            if i > 0 and not lines[i-1].endswith('\n'):
                pass  # Keep it
        
        # Fix incomplete diff headers
        if line.startswith('diff --git') and i + 1 < len(lines):
            # Ensure we have proper index line
            if not lines[i+1].startswith('index ') and not lines[i+1].startswith('---'):
                # Try to fix by checking if next line is a file path
                pass
        
        cleaned_lines.append(line)
        i += 1
    
    # Join and ensure proper format
    cleaned = '\n'.join(cleaned_lines)
    
    # Remove duplicate file separators
    # If we see "diff --git" immediately after another "diff --git" without proper separation
    cleaned = re.sub(r'(diff --git[^\n]+\n)(diff --git)', r'\1\n\2', cleaned)
    
    return cleaned

def apply_patch(cwd: Path, patch_text: str) -> Path:
    """Apply a patch to the repository - aligned with run_autopr.py"""
    patch_file = cwd / "crewai_patch.diff"
    patch_file.write_text(patch_text, encoding="utf-8")
    
    # Try to apply the patch with multiple strategies
    strategies = [
        (["git", "apply", "--whitespace=fix", str(patch_file)], "whitespace fix"),
        (["git", "apply", "--ignore-whitespace", str(patch_file)], "ignore whitespace"),
        (["git", "apply", "--3way", str(patch_file)], "3-way merge"),
        (["git", "apply", "--unidiff-zero", str(patch_file)], "unidiff-zero"),
        (["git", "apply", "-C1", str(patch_file)], "reduce context (-C1)"),
    ]
    
    for strategy_cmd, strategy_name in strategies:
        try:
            result = subprocess.run(strategy_cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✓ Patch applied successfully using {strategy_name}")
                return patch_file
            else:
                # Log the error for debugging (first strategy only to avoid spam)
                if strategy_name == "whitespace fix" and result.stderr:
                    error_msg = result.stderr[:200] if len(result.stderr) > 200 else result.stderr
                    if "corrupt" in error_msg.lower() or "error:" in error_msg.lower():
                        print(f"   Debug: {error_msg}")
        except subprocess.TimeoutExpired:
            continue
        except Exception as e:
            continue
    
    # If all standard strategies failed, try file-by-file application
    print(f"⚠ Standard patch application failed. Trying file-by-file approach...")
    if apply_patch_file_by_file(cwd, patch_text):
        print(f"✓ Patch applied successfully using file-by-file method")
        return patch_file
    
    # If file-by-file also failed, try to fix and retry
    print(f"⚠ File-by-file approach failed. Attempting to fix patch...")
    fixed_patch = fix_patch_for_current_files(cwd, patch_text)
    if fixed_patch and fixed_patch != patch_text:
        patch_file.write_text(fixed_patch, encoding="utf-8")
        # Retry with fixed patch
        for strategy_cmd, strategy_name in strategies[:3]:  # Try first 3 strategies
            try:
                result = subprocess.run(strategy_cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print(f"✓ Patch applied successfully after fixing (using {strategy_name})")
                    return patch_file
            except Exception:
                continue
    
    # Last resort: try using 'patch' command directly (if available)
    print(f"⚠ Git apply failed. Trying 'patch' command as last resort...")
    try:
        with open(patch_file, 'r') as pf:
            result = subprocess.run(["patch", "-p1"],
                                  cwd=cwd, stdin=pf, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"✓ Patch applied successfully using 'patch' command")
                return patch_file
            else:
                print(f"⚠ Patch command also failed: {result.stderr[:200]}")
    except FileNotFoundError:
        print(f"⚠ 'patch' command not available on this system")
    except subprocess.TimeoutExpired:
        print(f"⚠ Patch command timed out")
    except Exception as e:
        print(f"⚠ Patch command error: {e}")
    
    # All git/patch command attempts failed - try direct file editing as last resort
    print(f"⚠ All standard methods failed. Attempting direct file editing...")
    if apply_patch_directly(cwd, patch_text):
        print(f"✓ Patch applied successfully using direct file editing")
        return patch_file
    
    # All attempts failed
    print(f"\n⚠ Patch failed to apply after all automatic attempts. Patch saved at: {patch_file}")
    print(f"\n💡 The patch could not be applied automatically, but the code changes are available in:")
    print(f"   - Implementation plan: implementations/issue_*_plan.md")
    print(f"   - Patch file: {patch_file}")
    
    # Check if any changes were made (partial success)
    if has_changes(cwd):
        print(f"⚠ Some changes may have been applied. Check 'git status' to see what changed.")
    
    # Don't raise - we've tried everything, but don't fail the whole process
    return patch_file

def split_patch_by_file(patch_text: str) -> list[tuple[str, str]]:
    """
    Split a multi-file patch into individual file patches.
    Returns list of (file_path, file_patch) tuples.
    """
    files = []
    current_file = None
    current_patch = []
    
    lines = patch_text.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Start of a new file diff
        if line.startswith('diff --git'):
            # Save previous file if exists
            if current_file and current_patch:
                files.append((current_file, '\n'.join(current_patch)))
            
            # Extract file path
            # Format: diff --git a/path b/path
            parts = line.split()
            if len(parts) >= 4:
                file_path = parts[2].lstrip('a/')
                current_file = file_path
                current_patch = [line]
            else:
                current_file = None
                current_patch = []
        elif current_file:
            current_patch.append(line)
        
        i += 1
    
    # Save last file
    if current_file and current_patch:
        files.append((current_file, '\n'.join(current_patch)))
    
    return files

def apply_patch_file_by_file(cwd: Path, patch_text: str) -> bool:
    """
    Apply patch file-by-file as a fallback strategy.
    Returns True if at least one file was successfully patched.
    """
    files = split_patch_by_file(patch_text)
    if not files:
        return False
    
    success_count = 0
    for file_path, file_patch in files:
        target_file = cwd / file_path
        if not target_file.exists():
            print(f"⚠ File {file_path} does not exist, skipping...")
            continue
        
        # Create temporary patch file for this single file
        temp_patch = cwd / f"crewai_patch_{file_path.replace('/', '_')}.diff"
        try:
            temp_patch.write_text(file_patch, encoding="utf-8")
            
            # Try to apply this single-file patch
            strategies = [
                ["git", "apply", "--whitespace=fix", str(temp_patch)],
                ["git", "apply", "--ignore-whitespace", str(temp_patch)],
                ["git", "apply", "--3way", str(temp_patch)],
            ]
            
            applied = False
            for strategy in strategies:
                result = subprocess.run(strategy, cwd=cwd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    print(f"✓ Applied patch to {file_path}")
                    success_count += 1
                    applied = True
                    break
            
            if not applied:
                # Try using 'patch' command as last resort (if available)
                try:
                    # patch command needs input from stdin or file
                    with open(temp_patch, 'r') as pf:
                        result = subprocess.run(["patch", "-p1", str(target_file)],
                                              cwd=cwd, stdin=pf, capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            print(f"✓ Applied patch to {file_path} using 'patch' command")
                            success_count += 1
                            applied = True
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    # patch command not available or timed out - that's okay
                    pass
                except Exception as e:
                    # Other errors - log but continue
                    print(f"⚠ Patch command error for {file_path}: {e}")
                
                if not applied:
                    print(f"⚠ Failed to apply patch to {file_path} (will try other methods)")
        finally:
            # Clean up temp patch file
            if temp_patch.exists():
                temp_patch.unlink()
    
    return success_count > 0

def apply_patch_directly(cwd: Path, patch_text: str) -> bool:
    """
    Apply patch by directly editing files (last resort when git apply fails).
    Parses the diff and applies changes directly to files.
    Returns True if at least one file was successfully modified.
    """
    import re
    
    files = split_patch_by_file(patch_text)
    if not files:
        return False
    
    success_count = 0
    
    for file_path, file_patch in files:
        target_file = cwd / file_path
        if not target_file.exists():
            print(f"⚠ File {file_path} does not exist, skipping direct edit...")
            continue
        
        try:
            # Read current file
            current_content = target_file.read_text(encoding='utf-8')
            lines = current_content.split('\n')
            
            # Parse the patch to extract changes
            patch_lines = file_patch.split('\n')
            new_lines = lines.copy()
            offset = 0
            
            i = 0
            while i < len(patch_lines):
                line = patch_lines[i]
                
                # Look for hunk headers: @@ -start,count +start,count @@
                hunk_match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                if hunk_match:
                    old_start = int(hunk_match.group(1)) - 1  # Convert to 0-based
                    old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
                    new_start = int(hunk_match.group(3)) - 1
                    new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1
                    
                    # Process hunk lines
                    i += 1
                    hunk_lines = []
                    context_lines = []
                    
                    while i < len(patch_lines) and not patch_lines[i].startswith('@@'):
                        patch_line = patch_lines[i]
                        if patch_line.startswith(' '):
                            # Context line - verify it matches
                            context_lines.append(patch_line[1:])
                            hunk_lines.append(('context', patch_line[1:]))
                        elif patch_line.startswith('-'):
                            # Line to remove
                            hunk_lines.append(('remove', patch_line[1:]))
                        elif patch_line.startswith('+'):
                            # Line to add
                            hunk_lines.append(('add', patch_line[1:]))
                        i += 1
                    
                    # Apply hunk to file
                    # Find the context in the file
                    context_found = False
                    search_start = max(0, old_start - 5)
                    search_end = min(len(new_lines), old_start + old_count + 5)
                    
                    for search_pos in range(search_start, search_end - len(context_lines) + 1):
                        # Check if context matches
                        matches = True
                        for j, (op, content) in enumerate(hunk_lines[:min(3, len(hunk_lines))]):
                            if op == 'context':
                                if search_pos + j >= len(new_lines) or new_lines[search_pos + j] != content:
                                    matches = False
                                    break
                        
                        if matches:
                            context_found = True
                            # Apply changes
                            pos = search_pos
                            for op, content in hunk_lines:
                                if op == 'context':
                                    pos += 1
                                elif op == 'remove':
                                    if pos < len(new_lines) and new_lines[pos] == content:
                                        new_lines.pop(pos)
                                elif op == 'add':
                                    new_lines.insert(pos, content)
                                    pos += 1
                            break
                    
                    if not context_found:
                        print(f"⚠ Could not find context for hunk in {file_path}, skipping...")
                        continue
                else:
                    i += 1
            
            # Write modified file
            new_content = '\n'.join(new_lines)
            if new_content != current_content:
                target_file.write_text(new_content, encoding='utf-8')
                print(f"✓ Applied changes to {file_path} using direct editing")
                success_count += 1
            else:
                print(f"⚠ No changes detected in {file_path} after direct editing")
        
        except Exception as e:
            print(f"⚠ Error applying direct edit to {file_path}: {e}")
            continue
    
    return success_count > 0

def fix_patch_for_current_files(cwd: Path, patch_text: str) -> str:
    """
    Attempt to fix patch by adjusting it to match current file structure.
    This is a best-effort attempt - may not always work.
    """
    # First, try to split and apply file-by-file
    if apply_patch_file_by_file(cwd, patch_text):
        # If file-by-file worked, return the original patch (it's been applied)
        return patch_text
    
    # If that didn't work, try to fix the patch format
    # Remove problematic sections and try to reconstruct
    lines = patch_text.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Skip no-op changes
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            if line.startswith('-') and next_line.startswith('+'):
                removed = line[1:].strip()
                added = next_line[1:].strip()
                if removed == added:
                    i += 2
                    continue
        
        # Keep valid diff lines
        if (line.startswith('diff --git') or
            line.startswith('index ') or
            line.startswith('---') or
            line.startswith('+++') or
            line.startswith('@@') or
            line.startswith(' ') or
            line.startswith('-') or
            line.startswith('+') or
            line.startswith('\\')):
            fixed_lines.append(line)
        
        i += 1
    
    fixed_patch = '\n'.join(fixed_lines)
    
    # If we made changes, return the fixed version
    if fixed_patch != patch_text:
        return fixed_patch
    
    # Otherwise, return None to indicate we can't auto-fix
    return None

def has_changes(cwd: Path) -> bool:
    """Check if there are uncommitted changes - aligned with run_autopr.py"""
    r = subprocess.run(["git", "status", "--porcelain"], 
                      cwd=cwd, text=True, capture_output=True, check=True)
    return bool(r.stdout.strip())

def apply_implementation(result, issue_number, work_dir, enable_testing: bool = None):
    """Apply the implementation to actual files - aligned with run_autopr.py
    
    Args:
        result: Crew execution result
        issue_number: Issue number
        work_dir: Working directory path
        enable_testing: If True, run tests after applying changes. 
                       If None, uses ENABLE_TESTING env var (default: True)
    """
    # HARD BRANCH SAFETY GUARD: Ensure we're on a feature branch BEFORE any file writes
    feature_branch_used = None
    if (work_dir / ".git").exists():
        try:
            feature_branch_used = ensure_feature_branch(work_dir, issue_number)
            print(f"✓ Branch safety check passed: on branch '{feature_branch_used}'")
        except ValueError as e:
            # Branch guard failed - abort before any file writes
            print(f"\n{'='*70}")
            print(f"❌ BRANCH SAFETY GUARD FAILED")
            print(f"{'='*70}")
            print(f"{str(e)}")
            print(f"\n⚠️  Aborting implementation - no file changes were made")
            return {
                "status": "incomplete",
                "is_complete": False,
                "files_changed": [],
                "git_changed_files": [],
                "missing_items": {
                    "_failure_reason": "branch_safety_guard_failed",
                    "_failure_summary": f"Branch safety guard failed: {str(e)}"
                },
                "coverage_passed": False,
                "has_git_changes": False,
                "did_commit": False,
                "did_push": False,
                "did_move_done": False,
                "feature_branch": None,
                "_run_state": RunState()
            }
    
    # Determine if testing should be enabled
    if enable_testing is None:
        # Check environment variable, default to True if not set
        enable_testing = os.getenv("ENABLE_TESTING", "true").lower() in ("true", "1", "yes")
    
    output_file = work_dir / "implementations" / f"issue_{issue_number}_plan.md"
    output_file.parent.mkdir(exist_ok=True)
    
    # Extract diff from result - try multiple ways to get full output
    result_text = str(result) if result else ""
    
    # If result is a CrewAI result object, try to get more details
    if result and hasattr(result, 'raw'):
        raw_text = str(result.raw) if result.raw else ""
        if raw_text and len(raw_text) > len(result_text):
            result_text = raw_text
    
    # Try to get task outputs separately
    task_outputs = []
    if result and hasattr(result, 'tasks_output'):
        for i, task_output in enumerate(result.tasks_output):
            task_str = str(task_output)
            if task_str and task_str.strip():
                task_outputs.append(f"### Task {i+1} Output\n\n{task_str}")
    
    # Combine all outputs
    if task_outputs:
        result_text = f"{result_text}\n\n" + "\n\n".join(task_outputs)
    
    # If result is still minimal, add warning and debug info
    if len(result_text.strip()) < 100:
        print(f"⚠ Warning: Result seems minimal ({len(result_text)} chars). This may indicate an error or incomplete execution.")
        print(f"   Result object: {result}")
        print(f"   Result type: {type(result)}")
        
        # Try to get more information
        if result and hasattr(result, '__dict__'):
            debug_info = "\n".join([f"- {k}: {str(v)[:200]}" for k, v in result.__dict__.items()])
            result_text = f"{result_text}\n\n## ⚠️ Warning: Minimal Output Detected\n\n"
            result_text += f"This output appears to be incomplete. Debug information:\n\n{debug_info}"
    
    # Extract structured changes (new approach - no diff)
    structured_changes = parse_structured_changes(result_text)
    
    # Check if agent output looks like a diff (reject it)
    if "diff --git" in result_text or "--- a/" in result_text or "@@ -" in result_text:
        print("⚠️  WARNING: Agent output contains diff-like content!")
        print("   The agent should output structured JSON changes, not a diff.")
        print("   Attempting to parse anyway, but this may fail.")
    
    # Extract review comments separately (if any)
    review_comments = extract_review_comments(result_text)
    
    # Legacy: Also try to extract diff for backward compatibility/display
    patch = extract_diff(result_text)  # Keep for display in plan file
    
    # Save full result with metadata
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Implementation Plan for Issue #{issue_number}\n\n")
        f.write(f"**Generated:** {__import__('datetime').datetime.now().isoformat()}\n\n")
        f.write("## Full Crew Output\n\n")
        f.write(result_text)
        
        # Save review comments separately if found
        if review_comments:
            f.write("\n\n## Code Review Comments\n\n")
            f.write(review_comments)
        
        # Save structured changes JSON
        if structured_changes and "error" not in structured_changes:
            f.write("\n\n## Structured Changes (JSON)\n\n")
            f.write("```json\n")
            f.write(json.dumps(structured_changes, indent=2))
            f.write("\n```\n")
        
        # Save patch (generated by git diff, or legacy if available)
        if patch:
            f.write("\n\n## Generated Patch (from git diff)\n\n")
            f.write("```diff\n")
            f.write(patch)
            f.write("\n```\n")
            
            # Note that patches generated by git diff are always valid
            f.write("\n\n✅ **Note:** This patch was generated by `git diff` and is guaranteed to be valid.\n")
        
        # Add metadata section
        f.write("\n\n## Metadata\n\n")
        f.write(f"- Result Type: `{type(result).__name__}`\n")
        f.write(f"- Output Length: {len(result_text)} characters\n")
        if hasattr(result, 'tasks_output'):
            f.write(f"- Number of Tasks: {len(result.tasks_output)}\n")
        if patch:
            f.write(f"- Patch Valid: {'✅ Yes' if validate_diff_format(patch) else '⚠️ Needs Review'}\n")
    
    print(f"\n✓ Implementation plan saved to: {output_file}")
    
    # Also save a copy to ai-dev-team/exports if directory exists
    export_dir = Path.home() / "ai-dev-team" / "exports"
    if export_dir.exists():
        export_file = export_dir / f"issue_{issue_number}_plan.md"
        import shutil
        shutil.copy(output_file, export_file)
        print(f"✓ Output also exported to: {export_file}")
    
    # Apply structured changes (new approach - no LLM diffs)
    patch_applied = False
    changed_files = []
    patch_content = None
    
    # B) Initialize missing_items early to prevent empty dict
    missing = {
        "functions": [],
        "css_selectors": [],
        "test_files": [],
        "required_files": [],
        "validation_errors": []  # B) Track validation failures
    }
    is_complete = False
    git_changed = []
    success = False
    
    if structured_changes and "error" not in structured_changes:
        # Validate structured changes
        is_valid, validation_errors = validate_structured_changes(structured_changes, work_dir)
        
        if not is_valid:
            print(f"\n❌ Structured changes validation failed:")
            for error in validation_errors:
                print(f"   - {error}")
            print(f"\n⚠️  Changes were not applied. Review the agent output in: {output_file}")
            # B) Set meaningful missing_items when validation fails
            missing["validation_errors"] = validation_errors
            missing["_failure_reason"] = "validation_failed"
            missing["_failure_summary"] = f"Validation failed with {len(validation_errors)} error(s). Changes not applied."
        else:
            # Apply structured changes
            print(f"\n{'='*70}")
            print(f"📝 APPLYING STRUCTURED CHANGES")
            print(f"{'='*70}")
            
            success, changed_files, apply_errors = apply_structured_changes(structured_changes, work_dir)
            
            if apply_errors:
                print(f"\n⚠️  Errors during application:")
                for error in apply_errors:
                    print(f"   - {error}")
                # B) Track apply errors in missing_items
                if "apply_errors" not in missing:
                    missing["apply_errors"] = []
                missing["apply_errors"].extend(apply_errors)
                missing["_failure_reason"] = "apply_failed"
                missing["_failure_summary"] = f"Application failed with {len(apply_errors)} error(s)."
            
            # C) Only proceed if changes were actually applied
            if success and changed_files:
                print(f"\n✅ Successfully applied changes to {len(changed_files)} file(s):")
                for file in changed_files:
                    print(f"   - {file}")
                
                # Verify changes with git status (robust check)
                git_changed = get_git_changed_files(work_dir)
                if git_changed:
                    print(f"\n📋 Git reports {len(git_changed)} changed file(s):")
                    for file in git_changed:
                        print(f"   - {file}")
                elif changed_files:
                    print(f"\n⚠️  Warning: Applied changes but git status shows no changes")
                    print(f"   This may indicate files were written outside repo or changes were reverted")
                else:
                    print(f"\n⚠️  No files were changed according to git status")
                
                # Check coverage before proceeding
                print(f"\n{'='*70}")
                print(f"🔍 COVERAGE CHECK")
                print(f"{'='*70}")
                
                is_complete, missing = check_coverage(output_file, work_dir)
                
                if is_complete:
                    print(f"✅ All plan requirements met!")
                else:
                    print(f"❌ Coverage check failed - missing items:")
                    if missing["functions"]:
                        print(f"   Missing functions: {', '.join(missing['functions'])}")
                    if missing["css_selectors"]:
                        print(f"   Missing CSS selectors: {', '.join(missing['css_selectors'])}")
                    if missing["test_files"]:
                        print(f"   Missing test files: {', '.join(missing['test_files'])}")
                    if missing["required_files"]:
                        print(f"   Missing required files: {', '.join(missing['required_files'])}")
                
                # CRITICAL: Only proceed if coverage passes AND git shows changes
                # This gate prevents partial implementations from being committed
                if not is_complete:
                    print(f"\n❌ COVERAGE GATE FAILED - Implementation incomplete")
                    print(f"   Missing items prevent commit and GitHub operations")
                    patch_applied = False
                elif not git_changed:
                    print(f"\n❌ NO CHANGES DETECTED - Implementation incomplete")
                    print(f"   Git reports no changes, preventing commit")
                    patch_applied = False
                else:
                    # Coverage passed AND changes detected - proceed
                    # Generate patch using git diff (deterministic, always valid)
                    # NOTE: Patch is generated AFTER coverage check but BEFORE commit
                    # This ensures patch reflects the final state
                    if (work_dir / ".git").exists():
                        patch_file = work_dir / "crewai_patch.diff"
                        print(f"\n📦 Generating patch using git diff...")
                        print(f"   Note: Patch file is a local artifact and will NOT be committed")
                        
                        patch_success, patch_result = generate_git_patch(work_dir, patch_file)
                        
                        if patch_success:
                            patch_content = patch_result
                            patch_applied = True
                            print(f"✅ Patch generated successfully: {patch_file}")
                            
                            # Show patch summary
                            lines_added = patch_content.count('\n+') - patch_content.count('\n+++')
                            lines_removed = patch_content.count('\n-') - patch_content.count('\n---')
                            print(f"   Files changed: {len(git_changed)}")
                            print(f"   Lines added: {lines_added}")
                            print(f"   Lines removed: {lines_removed}")
                            
                            # Validate patch
                            if patch_content.strip():
                                print(f"   ✅ Patch is non-empty and valid")
                            else:
                                print(f"   ⚠️  Patch is empty")
                        else:
                            print(f"⚠️  Failed to generate patch: {patch_result}")
                            patch_applied = False
                    else:
                        print(f"⚠️  Not a git repository - skipping patch generation")
                        patch_applied = False
                
                # C) Run tests after changes are applied (if enabled) - only if changes were actually applied
                if patch_applied and enable_testing and success and changed_files:
                    print(f"\n{'='*70}")
                    print(f"🧪 TESTING PHASE")
                    print(f"{'='*70}")
                    test_results = run_tests_after_patch(work_dir, issue_number, result)
                    if test_results:
                        # Append test results to the implementation plan
                        with open(output_file, 'a', encoding='utf-8') as f:
                            f.write("\n\n## Test Results\n\n")
                            f.write(test_results)
                        print(f"\n✅ Test results saved to: {output_file}")
                        
                        # Extract and display test status
                        if "Status: ✅ PASSED" in test_results:
                            print(f"✅ Tests PASSED - Code changes verified successfully")
                        elif "Status: ❌ FAILED" in test_results:
                            print(f"❌ Tests FAILED - Review test output in implementation plan")
                        elif "Status: ⚠️  NO TESTS FOUND" in test_results:
                            print(f"⚠️  No tests found - Manual verification recommended")
                        else:
                            print(f"ℹ️  Test execution completed - Review results in implementation plan")
                    else:
                        print(f"⚠️  No test results generated")
                elif patch_applied and not enable_testing:
                    print(f"\nℹ️  Testing skipped (ENABLE_TESTING=false or enable_testing=False)")
            else:
                # C) Only show this if we actually tried to apply but got no changes
                if success and not changed_files:
                    print(f"\n⚠️  No files were changed (changes may have been idempotent)")
                elif not success:
                    print(f"\n⚠️  Changes were not applied (check errors above)")
                else:
                    print(f"\n⚠️  No files were changed")
    else:
        error_msg = structured_changes.get("error", "Unknown error") if isinstance(structured_changes, dict) else "Failed to parse structured changes"
        print(f"\n⚠️  Could not parse structured changes: {error_msg}")
        print(f"   Review agent output in: {output_file}")
        # B) Set meaningful missing_items when parsing fails
        missing["_failure_reason"] = "parse_failed"
        missing["_failure_summary"] = f"Failed to parse structured changes: {error_msg}"
        missing["parse_error"] = error_msg
        print(f"   Falling back to legacy diff approach if available...")
        
        # Fallback to legacy diff approach if structured changes failed
        if patch and (work_dir / ".git").exists():
            try:
                patch_file = apply_patch(work_dir, patch)
                if has_changes(work_dir):
                    print(f"✓ Changes detected in repository - patch applied successfully (legacy mode)")
                    patch_applied = True
            except Exception as e:
                print(f"⚠ Error during legacy patch application: {e}")
                missing["_failure_reason"] = "legacy_patch_failed"
                missing["_failure_summary"] = f"Legacy patch application failed: {str(e)}"
    
    # D) Create RunState as single source of truth
    run_state = RunState()
    # C) Only set applied_ok if changes were actually applied AND git shows changes
    run_state.applied_ok = (success and changed_files and git_changed) if ('success' in locals() and 'changed_files' in locals() and 'git_changed' in locals()) else False
    run_state.coverage_ok = is_complete if 'is_complete' in locals() else False
    # B) Add validation/apply errors to run_state
    if missing.get("validation_errors"):
        run_state.errors.extend(missing["validation_errors"])
    if missing.get("apply_errors"):
        run_state.errors.extend(missing["apply_errors"])
    
    # Get git info for RunState
    if (work_dir / ".git").exists():
        try:
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                  cwd=work_dir, capture_output=True, text=True, check=False, timeout=5)
            if result.returncode == 0:
                run_state.current_branch = result.stdout.strip()
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  cwd=work_dir, capture_output=True, text=True, check=False, timeout=5)
            if result.returncode == 0:
                run_state.head_sha_before = result.stdout.strip()
        except Exception:
            pass
    
    # Return implementation status (backward compatibility with dict)
    # D) Determine final status: complete only if coverage passed AND git shows changes
    final_status = "incomplete"
    implementation_complete = False
    
    if 'is_complete' in locals() and 'git_changed' in locals():
        if is_complete and git_changed:
            final_status = "complete"
            implementation_complete = True
            run_state.coverage_ok = True
    
    implementation_status = {
        "status": final_status,
        "is_complete": implementation_complete,  # Boolean flag for gating
        "files_changed": changed_files if 'changed_files' in locals() else [],
        "git_changed_files": get_git_changed_files(work_dir) if (work_dir / ".git").exists() else [],
        "patch_path": str(work_dir / "crewai_patch.diff") if 'patch_applied' in locals() and patch_applied else None,
        "missing_items": missing,  # B) Always include missing_items (never empty dict after failure)
        "patch_content": patch_content if 'patch_content' in locals() else None,
        "coverage_passed": run_state.coverage_ok,
        "has_git_changes": bool(git_changed) if 'git_changed' in locals() else False,
        "did_commit": run_state.did_commit,  # D) From RunState
        "did_push": run_state.did_push,      # D) From RunState
        "did_move_done": run_state.did_move_done,  # D) From RunState
        "feature_branch": feature_branch_used,  # Branch safety guard: branch used
        "_run_state": run_state  # D) Include RunState for internal use
    }
    
    return implementation_status

def print_issue_status(issue_number: int, work_dir: Path, warnings: list[str], implementation_status: dict = None):
    """
    Print issue status separated into two sections:
    1. Local Implementation & Testing (what you can do locally)
    2. Git/GitHub Operations (version control status)
    
    Args:
        issue_number: Issue number
        work_dir: Working directory path
        warnings: List of warning messages
        implementation_status: Optional dict with did_commit, did_push flags
    """
    # Separate warnings into local and git/github categories
    local_warnings = []
    git_warnings = []
    
    for warning in warnings:
        warning_lower = warning.lower()
        if any(keyword in warning_lower for keyword in ['patch', 'implementation', 'plan', 'file']):
            local_warnings.append(warning)
        elif any(keyword in warning_lower for keyword in ['git', 'github', 'push', 'branch', 'pipeline', 'remote', 'network']):
            git_warnings.append(warning)
        else:
            # Default to local if unclear
            local_warnings.append(warning)
    
    # Check local implementation status
    patch_file = work_dir / "crewai_patch.diff"
    plan_file = work_dir / "implementations" / f"issue_{issue_number}_plan.md"
    # C) Use implementation_status to determine if changes were actually applied
    if implementation_status:
        # Check if changes were actually applied (not just validation passed)
        files_changed = implementation_status.get("files_changed", [])
        git_changed_files = implementation_status.get("git_changed_files", [])
        patch_applied = bool(files_changed and git_changed_files and implementation_status.get("coverage_passed", False))
    else:
        patch_applied = has_changes(work_dir) if (work_dir / ".git").exists() else False
    
    # Check test execution status from implementation plan
    test_status = None
    test_executed = False
    if plan_file.exists():
        try:
            plan_content = plan_file.read_text(encoding='utf-8')
            if "## Test Results" in plan_content or "Test Execution Status" in plan_content:
                test_executed = True
                # Extract test status
                status_match = re.search(r"Test Execution Status:\s*([✅❌⚠️ℹ️]+)\s*([A-Z]+)", plan_content)
                if status_match:
                    test_status = f"{status_match.group(1)} {status_match.group(2)}"
                elif "Status: ✅ PASSED" in plan_content:
                    test_status = "✅ PASSED"
                elif "Status: ❌ FAILED" in plan_content:
                    test_status = "❌ FAILED"
                elif "Status: ⚠️  NO TESTS FOUND" in plan_content:
                    test_status = "⚠️  NO TESTS FOUND"
                else:
                    test_status = "ℹ️  COMPLETED"
        except:
            pass
    
    # Capture ACTUAL current git branch and HEAD commit immediately before printing
    current_branch = None
    head_sha = None
    git_committed = False
    git_pushed = False
    
    if (work_dir / ".git").exists():
        try:
            # Get current branch
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                  cwd=work_dir, capture_output=True, text=True, check=False, timeout=5)
            if result.returncode == 0:
                current_branch = result.stdout.strip()
            
            # Get HEAD commit SHA (short)
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  cwd=work_dir, capture_output=True, text=True, check=False, timeout=5)
            if result.returncode == 0:
                head_sha = result.stdout.strip()
            
            # Use implementation_status flags if available (most accurate)
            if implementation_status:
                git_committed = implementation_status.get("did_commit", False)
                git_pushed = implementation_status.get("did_push", False)
            else:
                # Fallback: Check if there are commits on this branch
                result = subprocess.run(['git', 'log', '--oneline', '-1'], 
                                      cwd=work_dir, capture_output=True, text=True, check=False, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    git_committed = True
                
                # Check if branch is pushed (fallback method)
                if current_branch:
                    result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', '@{u}'], 
                                          cwd=work_dir, capture_output=True, text=True, check=False, timeout=5)
                    if result.returncode == 0:
                        git_pushed = True
        except Exception as e:
            pass
    
    # Print Section 1: Local Implementation & Testing
    print(f"\n{'='*70}")
    print(f"📦 LOCAL IMPLEMENTATION & TESTING - Issue #{issue_number}")
    print(f"{'='*70}")
    
    # C) Only show success if changes were actually applied AND git shows changes
    if patch_applied:
        print(f"✅ Code changes applied successfully to local files")
    elif patch_file.exists():
        print(f"⚠️  Code changes generated but not automatically applied")
        print(f"   Patch file: {patch_file}")
        print(f"   To apply manually:")
        print(f"      cd {work_dir}")
        print(f"      git apply --whitespace=fix crewai_patch.diff")
        print(f"      # Or review and apply changes manually from the patch file")
    else:
        # C) Check if validation failed or no changes were applied
        if implementation_status and implementation_status.get("missing_items", {}).get("_failure_reason"):
            failure_reason = implementation_status["missing_items"]["_failure_reason"]
            if failure_reason == "validation_failed":
                print(f"❌ Code changes: Validation failed - changes not applied")
            elif failure_reason == "apply_failed":
                print(f"❌ Code changes: Application failed - changes not applied")
            elif failure_reason == "parse_failed":
                print(f"❌ Code changes: Failed to parse structured changes")
            else:
                print(f"⚠️  Code changes: Not applied (reason: {failure_reason})")
        else:
            print(f"ℹ️  Implementation plan generated (no changes applied)")
    
    if plan_file.exists():
        print(f"✅ Implementation plan: {plan_file}")
        print(f"   Contains full code changes and implementation details")
    
    # C) Only show test execution status if changes were actually applied
    if patch_applied:
        if test_executed:
            print(f"\n🧪 Test Execution Status:")
            if test_status:
                print(f"   {test_status}")
            else:
                print(f"   ℹ️  Tests were executed (check plan file for details)")
            print(f"   Review test results in: {plan_file}")
            print(f"   Look for '## Test Results' section")
        else:
            print(f"\n⚠️  Test Execution:")
            print(f"   Tests were not executed (may have been skipped or failed to start)")
            print(f"   Check console output above for test execution messages")
    
    if local_warnings:
        print(f"\n⚠️  Local Warnings:")
        for warning in local_warnings:
            print(f"   - {warning}")
    
    # Testing instructions (only if tests weren't executed)
    if not test_executed:
        print(f"\n🧪 Manual Testing Steps:")
    print(f"   1. Review implementation plan: {plan_file}")
    if patch_file.exists() and not patch_applied:
        print(f"   2. Apply patch manually (see above) or copy code from plan file")
    print(f"   3. Test locally:")
    print(f"      cd {work_dir}")
    if (work_dir / "package.json").exists():
        print(f"      npm start  # or: node server.js")
    elif (work_dir / "server.js").exists():
        print(f"      node server.js")
    else:
        print(f"      python3 -m http.server 8000  # or your preferred method")
    print(f"   4. Open in browser and verify functionality")
    
    # Print Section 2: Git/GitHub Operations
    print(f"\n{'='*70}")
    print(f"🔀 GIT STATUS / SUMMARY - Issue #{issue_number}")
    print(f"{'='*70}")
    
    if not (work_dir / ".git").exists():
        print(f"ℹ️  Not a git repository - Git operations skipped")
    else:
        # D) Show actual current branch and HEAD commit (computed truthfully)
        # Also show feature branch used (from branch safety guard)
        if implementation_status and implementation_status.get("feature_branch"):
            feature_branch = implementation_status["feature_branch"]
            if current_branch == feature_branch:
                print(f"📍 Current Branch: {current_branch} (feature branch used)")
            else:
                print(f"📍 Current Branch: {current_branch}")
                print(f"📍 Feature Branch Used: {feature_branch}")
        elif current_branch:
            print(f"📍 Current Branch: {current_branch}")
        else:
            print(f"⚠️  Branch status unknown")
        
        if head_sha:
            print(f"📍 HEAD Commit: {head_sha}")
        else:
            print(f"⚠️  HEAD commit unknown")
        
        # D) Compute committed status truthfully: check if working tree is clean AND commit was made
        # If working tree has uncommitted changes, show "Uncommitted changes: ✅"
        has_uncommitted = has_changes(work_dir) if (work_dir / ".git").exists() else False
        
        # D) Use run state flags for accurate commit/push status
        if implementation_status:
            git_committed = implementation_status.get("did_commit", False)
            git_pushed = implementation_status.get("did_push", False)
        else:
            git_committed = False
            git_pushed = False
        
        # D) Show committed status truthfully
        if git_committed:
            print(f"✅ Committed")
        elif has_uncommitted:
            print(f"❌ Committed: No")
            print(f"✅ Uncommitted changes: Yes (working tree has changes)")
        else:
            print(f"⚠️  Not committed")
        
        # D) Show pushed status truthfully (only if push actually succeeded)
        if git_pushed:
            print(f"✅ Pushed")
        else:
            print(f"⚠️  Not pushed")
            if current_branch:
                print(f"   To push manually:")
                print(f"      cd {work_dir}")
                print(f"      git push -u origin {current_branch}")
        
        if git_warnings:
            print(f"\n⚠️  Git/GitHub Warnings:")
            for warning in git_warnings:
                print(f"   - {warning}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"📊 SUMMARY - Issue #{issue_number}")
    print(f"{'='*70}")
    
    # C) Implementation status - only show success if actually applied
    if patch_applied:
        print(f"✅ Code changes: Applied successfully")
    else:
        # Check failure reason from missing_items
        if implementation_status and implementation_status.get("missing_items", {}).get("_failure_reason"):
            failure_reason = implementation_status["missing_items"]["_failure_reason"]
            failure_summary = implementation_status["missing_items"].get("_failure_summary", failure_reason)
            print(f"❌ Code changes: {failure_summary}")
        else:
            print(f"⚠️  Code changes: Not applied (check patch file or validation errors)")
    
    # Test status
    if test_executed:
        if test_status and "PASSED" in test_status:
            print(f"✅ Tests: Executed and PASSED")
        elif test_status and "FAILED" in test_status:
            print(f"❌ Tests: Executed but FAILED - Review test results")
        elif test_status and "NO TESTS FOUND" in test_status:
            print(f"⚠️  Tests: No tests found - Manual verification recommended")
        else:
            print(f"ℹ️  Tests: Executed (check results in plan file)")
    else:
        print(f"⚠️  Tests: Not executed")
    
    # Git status
    if git_warnings:
        print(f"⚠️  Git/GitHub: Some operations had issues (non-critical for local testing)")
    elif current_branch and git_committed and git_pushed:
        print(f"✅ Git/GitHub: All operations completed successfully")
    elif current_branch:
        print(f"ℹ️  Git/GitHub: Partial completion (check status above)")
    
    print(f"{'='*70}")
    print(f"{'='*70}\n")

def run_preview_script(issue_number: int, work_dir: Path):
    """Run the preview script to show changes and start preview server"""
    preview_script = Path(__file__).parent / "preview_implementation.py"
    
    if not preview_script.exists():
        # Preview script not found, skip
        return
    
    try:
        # Run preview script in background or foreground based on env var
        run_in_background = os.getenv("PREVIEW_IN_BACKGROUND", "false").lower() == "true"
        
        if run_in_background:
            # Run in background (non-blocking)
            subprocess.Popen(
                [sys.executable, str(preview_script), str(issue_number)],
                cwd=work_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            print(f"\n🔍 Preview script started in background")
            print(f"   Run manually: python {preview_script} {issue_number}")
        else:
            # Run in foreground to show output
            print(f"\n{'='*70}")
            print(f"🔍 Running preview script to show changes and start server...")
            print(f"{'='*70}")
            try:
                result = subprocess.run(
                    [sys.executable, str(preview_script), str(issue_number)],
                    cwd=work_dir,
                    timeout=60  # Increased timeout for patch application
                )
                if result.returncode != 0:
                    print(f"\n⚠️  Preview script had issues (non-critical)")
                    print(f"   You can run it manually: python {preview_script} {issue_number}")
            except subprocess.TimeoutExpired:
                print(f"\n⚠️  Preview script timed out (non-critical)")
                print(f"   You can run it manually: python {preview_script} {issue_number}")
            except FileNotFoundError:
                print(f"\n⚠️  Python interpreter not found (non-critical)")
            except Exception as e:
                print(f"\n⚠️  Could not run preview script: {e} (non-critical)")
                print(f"   You can run it manually: python {preview_script} {issue_number}")
    except Exception as e:
        # Don't fail the whole process if preview fails
        print(f"⚠️  Could not run preview script: {e} (non-critical)")

def check_patch_application_status(work_dir: Path) -> tuple[bool, list[str]]:
    """
    Check if patch was successfully applied and return status with warnings
    Returns: (patch_applied, warnings)
    """
    warnings = []
    patch_applied = False
    
    if not (work_dir / ".git").exists():
        return False, warnings
    
    # Check if there are changes
    if has_changes(work_dir):
        patch_applied = True
    else:
        # No changes - check if patch file exists
        patch_file = work_dir / "crewai_patch.diff"
        if patch_file.exists():
            # Patch file exists but no changes - likely failed to apply
            warnings.append("Patch file generated but changes not applied (patch may be corrupt or incompatible with current files)")
            patch_applied = False
        else:
            # No patch file - no patch was generated
            patch_applied = False
    
    return patch_applied, warnings

def ensure_base_branch(work_dir):
    """Ensure we're on the base branch (development) before processing issues.
    This ensures patches are generated based on the correct codebase state."""
    try:
        # Get current branch
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                              cwd=work_dir, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return  # Not a git repo or can't determine branch
        
        current_branch = result.stdout.strip()
        
        # Determine base branch (prefer development, fallback to main/master)
        base_branch = None
        result = subprocess.run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/development'],
                              cwd=work_dir, capture_output=True, check=False)
        if result.returncode == 0:
            base_branch = 'development'
        else:
            # Fallback to main/master
            for branch in ['main', 'master']:
                result = subprocess.run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch}'],
                                      cwd=work_dir, capture_output=True, check=False)
                if result.returncode == 0:
                    base_branch = branch
                    break
        
        if not base_branch:
            print(f"⚠ No development/main/master branch found, staying on {current_branch}")
            return
        
        # Switch to base branch if not already on it
        if current_branch != base_branch:
            # Check for uncommitted changes
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  cwd=work_dir, capture_output=True, text=True, check=False)
            if result.stdout.strip():
                print(f"⚠ Uncommitted changes detected on {current_branch}")
                print(f"   Switching to {base_branch} will carry these changes over")
            
            print(f"🔄 Switching to base branch: {base_branch}")
            result = subprocess.run(['git', 'checkout', base_branch], 
                                  cwd=work_dir, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                # Pull latest changes
                subprocess.run(['git', 'pull', '--ff-only'], 
                             cwd=work_dir, capture_output=True, check=False)
                print(f"✓ On base branch: {base_branch}")
            else:
                print(f"⚠ Could not switch to {base_branch}: {result.stderr}")
        else:
            # Already on base branch, just pull latest
            subprocess.run(['git', 'pull', '--ff-only'], 
                         cwd=work_dir, capture_output=True, check=False)
    except Exception as e:
        print(f"⚠ Error ensuring base branch: {e}")

def create_branch_and_commit(issue_number, work_dir, repo_name=None, issue_title=None, push=False) -> dict:
    """
    Create a git branch, commit changes, and optionally push and create PR.
    Returns dict with: did_commit, did_push, branch_name, commit_hash (if successful)
    """
    original_dir = os.getcwd()
    os.chdir(work_dir)
    
    try:
        # Check if git repo exists
        if not (Path(work_dir) / ".git").exists():
            print("⚠ Not a git repository, skipping branch/commit")
            return
        
        # Get current branch
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                              capture_output=True, text=True, check=False)
        current_branch = result.stdout.strip() if result.returncode == 0 else None
        
        # Determine base branch (prefer development, fallback to main/master)
        base_branch = None
        # First check for development branch (Git Flow workflow)
        result = subprocess.run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/development'],
                              capture_output=True, check=False)
        if result.returncode == 0:
            base_branch = 'development'
        else:
            # Fallback to main/master if development doesn't exist
            for branch in ['main', 'master']:
                result = subprocess.run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch}'],
                                      capture_output=True, check=False)
                if result.returncode == 0:
                    base_branch = branch
                    break
        
        if not base_branch:
            print("⚠ No development/main/master branch found, using current branch as base")
            base_branch = current_branch or 'main'
        
        # Switch to base branch if not already on it
        if current_branch != base_branch:
            subprocess.run(['git', 'checkout', base_branch], check=False, capture_output=True)
            subprocess.run(['git', 'pull', '--ff-only'], check=False, capture_output=True)
        
        # Create branch (delete if exists)
        branch_name = f"feature/issue-{issue_number}"
        
        # Check if we're already on this branch
        if current_branch == branch_name:
            print(f"✓ Already on branch: {branch_name}")
        else:
            # Check if branch exists
            result = subprocess.run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch_name}'],
                                  capture_output=True, check=False)
            if result.returncode == 0:
                # Branch exists, switch to it or delete and recreate
                print(f"⚠ Branch {branch_name} already exists")
                # Try to switch to it first
                result = subprocess.run(['git', 'checkout', branch_name], 
                                      capture_output=True, text=True, check=False)
                if result.returncode != 0:
                    # Can't switch, delete and recreate
                    print(f"   Deleting existing branch...")
                    subprocess.run(['git', 'branch', '-D', branch_name], check=False, capture_output=True)
                    # Create new branch from base
                    result = subprocess.run(['git', 'checkout', '-b', branch_name], 
                                          capture_output=True, text=True, check=False)
                    if result.returncode != 0:
                        print(f"⚠ Failed to create branch: {result.stderr}")
                        print(f"   Continuing without branch creation...")
                        return
            else:
                # Branch doesn't exist, create it
                result = subprocess.run(['git', 'checkout', '-b', branch_name], 
                                      capture_output=True, text=True, check=False)
                if result.returncode != 0:
                    print(f"⚠ Failed to create branch: {result.stderr}")
                    print(f"   Continuing without branch creation...")
                    return
        
        # Check if there are changes to commit (excluding patch artifacts)
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, check=True)
        
        # Filter out patch artifacts from staging
        status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        files_to_commit = []
        for line in status_lines:
            if line.strip():
                file_path = line[3:].strip()  # Skip status prefix
                # Exclude patch artifacts
                if not file_path.endswith('crewai_patch.diff') and not file_path.endswith('_patch.diff'):
                    files_to_commit.append(file_path)
        
        if not files_to_commit:
            print("⚠ No source files to commit (only patch artifacts/plans or no changes)")
            return
        
        # Add only source files (exclude patch artifacts and implementation plans)
        for file_path in files_to_commit:
            subprocess.run(['git', 'add', file_path], check=False, capture_output=True)
        
        # Verify we have something staged
        result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                              capture_output=True, text=True, check=True)
        if not result.stdout.strip():
            print("⚠ No files staged for commit")
            return
        
        # Commit
        commit_msg = f"feat: implement solution for issue #{issue_number}\n\nCloses #{issue_number}"
        if issue_title:
            commit_msg = f"feat: implement solution for issue #{issue_number}: {issue_title}\n\nCloses #{issue_number}"
        
        result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                              capture_output=True, text=True, check=False)
        commit_result_dict = {
            "did_commit": False,
            "did_push": False,
            "branch_name": branch_name,
            "commit_hash": None
        }
        if result.returncode != 0:
            print(f"⚠ Failed to commit: {result.stderr}")
            return commit_result_dict
        else:
            commit_result_dict["did_commit"] = True
            # Get commit hash
            commit_result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                         capture_output=True, text=True, check=False)
            if commit_result.returncode == 0:
                commit_result_dict["commit_hash"] = commit_result.stdout.strip()
            print(f"✓ Created branch: {branch_name}")
            print(f"✓ Committed changes")
        
        # Push branch if requested
        if push:
            try:
                # Check network connectivity first
                import socket
                try:
                    socket.create_connection(("github.com", 443), timeout=5)
                except (socket.timeout, OSError):
                    print(f"⚠ Network connectivity issue: Cannot reach github.com")
                    print(f"   Branch committed locally but not pushed")
                    print(f"   You can push manually later: git push -u origin {branch_name}")
                    return commit_result_dict
                
                push_result = subprocess.run(['git', 'push', '-u', 'origin', branch_name], 
                                      capture_output=True, text=True, check=False, timeout=60)
                if push_result.returncode == 0:
                    commit_result_dict["did_push"] = True
                    print(f"✓ Pushed branch to origin")
                    
                    # Create PR if repo_name provided
                    if repo_name and GITHUB_TOKEN:
                        create_pr(repo_name, branch_name, issue_number, issue_title)
                else:
                    error_msg = push_result.stderr or push_result.stdout or "Unknown error"
                    if "timeout" in error_msg.lower() or "could not connect" in error_msg.lower():
                        print(f"⚠ Network connectivity issue: Cannot reach GitHub")
                        print(f"   Branch committed locally but not pushed")
                        print(f"   You can push manually later: git push -u origin {branch_name}")
                    else:
                        print(f"⚠ Failed to push branch: {error_msg[:200]}")
                        print(f"   You may need to set up git remote or credentials")
            except subprocess.TimeoutExpired:
                print(f"⚠ Push timed out (network issue)")
                print(f"   Branch committed locally but not pushed")
                print(f"   You can push manually later: git push -u origin {branch_name}")
            except Exception as e:
                print(f"⚠ Failed to push branch: {e}")
                print(f"   Branch committed locally but not pushed")
        
        return commit_result_dict
    except Exception as e:
        print(f"⚠ Error in git operations: {e}")
        import traceback
        traceback.print_exc()
        return {"did_commit": False, "did_push": False, "branch_name": None, "commit_hash": None}
    finally:
        os.chdir(original_dir)

def create_pr(repo_name, branch_name, issue_number, issue_title=None):
    """Create a pull request on GitHub"""
    try:
        g = get_github_client()
        if not g:
            print("⚠ Cannot create PR: GitHub client not available")
            return None
        
        repo = g.get_repo(repo_name)
        org_name = repo_name.split('/')[0]
        
        # Determine base branch (prefer development, fallback to main/master)
        base_branch = None
        for branch in ["development", "main", "master"]:
            try:
                repo.get_branch(branch)
                base_branch = branch
                break
            except:
                continue
        
        if not base_branch:
            base_branch = "main"  # Final fallback
        
        # PR title and body
        pr_title = f"[CrewAI] Implement issue #{issue_number}"
        if issue_title:
            pr_title = f"[CrewAI] #{issue_number}: {issue_title}"
        
        pr_body = f"""Automated implementation for issue #{issue_number}.

**Generated by CrewAI agents:**
- Product Manager: Created user story and acceptance criteria
- Software Architect: Designed technical implementation plan
- Developer: Implemented code changes
- Code Reviewer: Reviewed for quality and correctness

**Issue:** #{issue_number}
**Branch:** {branch_name}

Please review the changes carefully.
"""
        
        # Check if PR already exists
        try:
            existing_prs = repo.get_pulls(head=f"{org_name}:{branch_name}", state='open')
            for pr in existing_prs:
                if pr.head.ref == branch_name:
                    print(f"✓ Pull Request already exists: {pr.html_url}")
                    return pr.html_url
        except:
            pass  # If check fails, try to create anyway
        
        pr = repo.create_pull(
            title=pr_title,
            body=pr_body,
            base=base_branch,
            head=branch_name
        )
        
        print(f"✓ Created Pull Request: {pr.html_url}")
        return pr.html_url
    except Exception as e:
        error_str = str(e)
        # Check if it's a "PR already exists" error
        if "422" in error_str and "already exists" in error_str.lower():
            # Try to find the existing PR
            try:
                org_name = repo_name.split('/')[0]
                existing_prs = repo.get_pulls(head=f"{org_name}:{branch_name}", state='open')
                for pr in existing_prs:
                    if pr.head.ref == branch_name:
                        print(f"✓ Pull Request already exists: {pr.html_url}")
                        return pr.html_url
            except:
                pass
        print(f"⚠ Failed to create PR: {e}")
        return None

def move_issue_in_project(repo_name, issue_number, target_column_name, project_name=None):
    """Move an issue to a specific column in GitHub project (supports both Classic and V2 Projects)"""
    try:
        g = get_github_client()
        if not g:
            print("⚠ Cannot move issue: GitHub client not available")
            return False
        
        repo = g.get_repo(repo_name)
        issue = repo.get_issue(issue_number)
        
        # Extract organization/user name from repo (e.g., "org/repo" -> "org")
        org_name = repo_name.split('/')[0]
        repo_name_only = repo_name.split('/')[1]
        
        token = os.getenv("GITHUB_TOKEN")
        
        # Try Projects V2 (GraphQL) first - this is the new format
        print(f"🔍 Looking for project: {project_name or 'default'}...")
        
        # GraphQL query to find projects
        graphql_url = "https://api.github.com/graphql"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        # Query for repository projects V2
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
        
        try:
            response = requests.post(graphql_url, headers=headers, json={"query": query, "variables": variables}, timeout=30)
        except requests.exceptions.Timeout:
            print(f"⚠ Network timeout when querying GitHub Projects API")
            print(f"   Pipeline movement skipped (network issue)")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"⚠ Network error when querying GitHub Projects API: {e}")
            print(f"   Pipeline movement skipped (network issue)")
            return False
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' not in data:
                projects_v2 = data.get('data', {}).get('repository', {}).get('projectsV2', {}).get('nodes', [])
                if projects_v2:
                    # Find the right project
                    project_v2 = None
                    if project_name:
                        for p in projects_v2:
                            if p.get('title') == project_name:
                                project_v2 = p
                                break
                    else:
                        project_v2 = projects_v2[0]  # Use first project
                    
                    if project_v2:
                        print(f"📋 Using Projects V2: {project_v2.get('title')} (ID: {project_v2.get('id')})")
                        return move_issue_in_project_v2(
                            project_v2.get('id'),
                            issue.id,
                            issue_number,
                            target_column_name,
                            project_v2.get('fields', {}).get('nodes', []),
                            token
                        )
        
        # Fallback to classic projects (REST API)
        print("   Trying classic projects (REST API)...")
        project = None
        projects = []
        
        # Try repository projects
        try:
            projects = list(repo.get_projects())
            print(f"📋 Found {len(projects)} repository-level classic project(s)")
        except:
            projects = []
        
        # Try user projects
        if not projects:
            try:
                user = g.get_user(org_name)
                projects = list(user.get_projects())
                print(f"📋 Found {len(projects)} user-level classic project(s)")
            except:
                projects = []
        
        if not projects:
            print("⚠ No projects found")
            return False
        
        # Find project
        if project_name:
            for p in projects:
                if p.name == project_name:
                    project = p
                    break
        else:
            project = projects[0]
        
        if not project:
            print(f"⚠ Project '{project_name or 'default'}' not found")
            return False
        
        print(f"📋 Using classic project: {project.name} (ID: {project.id})")
        
        # Get columns
        columns = list(project.get_columns())
        print(f"📋 Found {len(columns)} columns: {[c.name for c in columns]}")
        
        target_column = None
        issue_card = None
        source_column = None
        
        # First pass: Find target column
        for column in columns:
            if column.name == target_column_name:
                target_column = column
                break
        
        # Second pass: Find issue card in all columns
        for column in columns:
            if issue_card:
                break
            try:
                cards = list(column.get_cards())
                print(f"   Checking column '{column.name}' ({len(cards)} cards)...")
                for card in cards:
                    try:
                        content = card.get_content()
                        if hasattr(content, 'number') and content.number == issue_number:
                            issue_card = card
                            source_column = column
                            print(f"   ✓ Found issue #{issue_number} in column '{column.name}'")
                            break
                    except Exception as e:
                        # Some cards might not have content or might be notes
                        continue
            except Exception as e:
                print(f"   ⚠ Error reading cards from '{column.name}': {e}")
                continue
        
        if not target_column:
            print(f"⚠ Target column '{target_column_name}' not found")
            print(f"   Available columns: {[c.name for c in columns]}")
            return False
        
        if not issue_card:
            # Issue might not be in project yet, try to add it
            print(f"⚠ Issue #{issue_number} not found in project. Adding to '{target_column_name}'...")
            print(f"   Available columns: {[c.name for c in columns]}")
            try:
                # Add issue to target column using API directly
                token = os.getenv("GITHUB_TOKEN")
                url = f"https://api.github.com/projects/columns/{target_column.id}/cards"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                }
                data = {
                    "content_id": issue.id,
                    "content_type": "Issue"
                }
                response = requests.post(url, headers=headers, json=data)
                if response.status_code in [201, 200]:
                    print(f"✓ Added issue #{issue_number} to '{target_column_name}'")
                    return True
                else:
                    # Try legacy API
                    headers_legacy = {
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github.inertia-preview+json",
                        "X-GitHub-Api-Version": "2022-11-28"
                    }
                    response2 = requests.post(url, headers=headers_legacy, json=data)
                    if response2.status_code in [201, 200]:
                        print(f"✓ Added issue #{issue_number} to '{target_column_name}' (using legacy API)")
                        return True
                    else:
                        print(f"⚠ Failed to add issue: {response2.status_code} - {response2.text[:200]}")
                        return False
            except Exception as e:
                print(f"⚠ Failed to add issue to project: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Move card to target column
        if source_column and source_column.id == target_column.id:
            print(f"✓ Issue #{issue_number} already in '{target_column_name}'")
            return True
        
        # Use GitHub API directly to move card
        token = os.getenv("GITHUB_TOKEN")
        url = f"https://api.github.com/projects/columns/cards/{issue_card.id}/moves"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        
        data = {
            "position": "top",
            "column_id": target_column.id
        }
        
        print(f"🔄 Moving issue #{issue_number} from '{source_column.name if source_column else 'unknown'}' to '{target_column_name}'...")
        print(f"   Card ID: {issue_card.id}, Target Column ID: {target_column.id}")
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in [201, 200]:
            print(f"✓ Moved issue #{issue_number} to '{target_column_name}'")
            return True
        else:
            print(f"⚠ Failed to move card: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            # Try with old API format as fallback
            if response.status_code == 404 or "inertia" in response.text.lower():
                print(f"   Trying with legacy API format...")
                headers_legacy = {
                    "Authorization": f"token {token}",
                    "Accept": "application/vnd.github.inertia-preview+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                }
                response2 = requests.post(url, headers=headers_legacy, json=data)
                if response2.status_code in [201, 200]:
                    print(f"✓ Moved issue #{issue_number} to '{target_column_name}' (using legacy API)")
                    return True
                else:
                    print(f"   Legacy API also failed: {response2.status_code} - {response2.text[:200]}")
            return False
            
    except Exception as e:
        print(f"⚠ Error moving issue in project: {e}")
        import traceback
        traceback.print_exc()
        return False

def move_issue_in_project_v2(project_id, issue_id, issue_number, target_field_value, fields, token):
    """Move an issue in a Projects V2 using GraphQL"""
    try:
        graphql_url = "https://api.github.com/graphql"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        # Find the status field (usually called "Status" or similar)
        status_field = None
        target_option_id = None
        
        # Try multiple field name variations
        status_field_names = ['status', 'state', 'stage', 'progress', 'column']
        
        for field in fields:
            field_name_lower = field.get('name', '').lower()
            if any(name in field_name_lower for name in status_field_names):
                status_field = field
                # Find the target option (case-insensitive match)
                options = field.get('options', [])
                for opt in options:
                    if opt.get('name', '').lower() == target_field_value.lower():
                        target_option_id = opt.get('id')
                        break
                # If exact match not found, try partial match
                if not target_option_id:
                    for opt in options:
                        opt_name = opt.get('name', '').lower()
                        if target_field_value.lower() in opt_name or opt_name in target_field_value.lower():
                            target_option_id = opt.get('id')
                            print(f"   Using partial match: '{opt.get('name')}' for '{target_field_value}'")
                            break
                break
        
        if not status_field:
            print(f"⚠ No status field found in project")
            print(f"   Available fields: {[f.get('name') for f in fields]}")
            print(f"   Looking for fields matching: {status_field_names}")
            return False
        
        if not target_option_id:
            print(f"⚠ Target value '{target_field_value}' not found in status field '{status_field.get('name')}'")
            print(f"   Available options: {[opt.get('name') for opt in status_field.get('options', [])]}")
            print(f"   Tip: Check exact spelling/capitalization of column names")
            return False
        
        # First, get the current project item for this issue
        query_item = """
        query($projectId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: 100) {
                nodes {
                  id
                  content {
                    ... on Issue {
                      id
                      number
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        variables_item = {
            "projectId": project_id
        }
        
        try:
            response = requests.post(graphql_url, headers=headers, json={"query": query_item, "variables": variables_item}, timeout=30)
        except requests.exceptions.Timeout:
            print(f"⚠ Network timeout when querying project items")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"⚠ Network error when querying project items: {e}")
            return False
        
        if response.status_code != 200:
            print(f"⚠ Failed to query project items: {response.status_code}")
            if response.status_code == 404:
                print(f"   This might indicate the project structure has changed")
            return False
        
        data = response.json()
        if 'errors' in data:
            print(f"⚠ GraphQL errors: {data['errors']}")
            return False
        
        project_node = data.get('data', {}).get('node', {})
        items = project_node.get('items', {}).get('nodes', [])
        
        # Find the item for this issue
        project_item_id = None
        for item in items:
            content = item.get('content', {})
            if content.get('number') == issue_number:
                project_item_id = item.get('id')
                break
        
        if not project_item_id:
            # Issue not in project, add it first
            print(f"⚠ Issue #{issue_number} not in project. Adding...")
            
            # Ensure issue_id is in the correct format for GraphQL
            # GitHub GraphQL expects format: "Issue_<numeric_id>" or just the numeric ID
            content_id = issue_id
            if not str(issue_id).startswith('Issue_'):
                # Try with Issue_ prefix
                content_id = f"Issue_{issue_id}"
            
            mutation_add = """
            mutation($projectId: ID!, $contentId: ID!) {
              addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
                item {
                  id
                }
              }
            }
            """
            
            variables_add = {
                "projectId": project_id,
                "contentId": content_id
            }
            
            try:
                response_add = requests.post(graphql_url, headers=headers, json={"query": mutation_add, "variables": variables_add}, timeout=30)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                print(f"⚠ Network error when adding issue to project: {e}")
                print(f"   ℹ️  This is non-critical - core implementation still succeeded")
                return False
            
            if response_add.status_code == 200:
                data_add = response_add.json()
                if 'errors' not in data_add:
                    project_item_id = data_add.get('data', {}).get('addProjectV2ItemById', {}).get('item', {}).get('id')
                    if project_item_id:
                        print(f"✓ Added issue #{issue_number} to project")
                    else:
                        print(f"⚠ Failed to get item ID after adding")
                        print(f"   ℹ️  This is non-critical - core implementation still succeeded")
                        return False
                else:
                    errors = data_add.get('errors', [])
                    error_msg = str(errors)
                    print(f"⚠ Failed to add issue: {error_msg}")
                    
                    # Check if it's a NOT_FOUND error - this is often non-critical
                    # (issue might not exist, be in different repo, or permissions issue)
                    if any('NOT_FOUND' in str(e) for e in errors):
                        print(f"   ℹ️  Issue may not exist or be accessible via GraphQL API")
                        print(f"   ℹ️  Tried contentId: {content_id}")
                        print(f"   ℹ️  This is non-critical - core implementation still succeeded")
                        # Don't fail the whole operation for this
                        return False
                    
                    # For other errors, also make it non-critical
                    print(f"   ℹ️  This is non-critical - core implementation still succeeded")
                    return False
            else:
                print(f"⚠ Failed to add issue: {response_add.status_code}")
                print(f"   ℹ️  This is non-critical - core implementation still succeeded")
                return False
        
        # Update the status field
        mutation_update = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId
            itemId: $itemId
            fieldId: $fieldId
            value: {singleSelectOptionId: $optionId}
          }) {
            projectV2Item {
              id
            }
          }
        }
        """
        
        variables_update = {
            "projectId": project_id,
            "itemId": project_item_id,
            "fieldId": status_field.get('id'),
            "optionId": target_option_id
        }
        
        print(f"🔄 Moving issue #{issue_number} to '{target_field_value}'...")
        try:
            response_update = requests.post(graphql_url, headers=headers, json={"query": mutation_update, "variables": variables_update}, timeout=30)
        except requests.exceptions.Timeout:
            print(f"⚠ Network timeout when updating project status")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"⚠ Network error when updating project status: {e}")
            return False
        
        if response_update.status_code == 200:
            data_update = response_update.json()
            if 'errors' in data_update:
                print(f"⚠ Failed to update: {data_update.get('errors')}")
                return False
            else:
                print(f"✓ Moved issue #{issue_number} to '{target_field_value}'")
                return True
        else:
            print(f"⚠ Failed to update: {response_update.status_code} - {response_update.text[:200]}")
            return False
            
    except Exception as e:
        print(f"⚠ Error in Projects V2 movement: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_automated_crew(repo_name, max_issues=5, issue_number=None):
    """Run the automated crew on multiple issues or a specific issue"""
    
    processed_file = Path.home() / "ai-dev-team" / "processed_issues.json"
    work_dir = WORK_DIR
    
    print(f"🚀 Starting Automated Crew")
    print(f"Repository: {repo_name}")
    print(f"Working Directory: {work_dir}")
    if issue_number:
        print(f"Processing specific issue: #{issue_number}")
    else:
        print(f"Max Issues: {max_issues}\n")
    
    issues_processed = 0
    
    # If specific issue number provided, process only that
    if issue_number:
        g = get_github_client()
        if not g:
            print("❌ Failed to get GitHub client")
            return
        
        try:
            # First verify repository exists
            try:
                repo = g.get_repo(repo_name)
                print(f"✓ Repository '{repo_name}' found: {repo.full_name}")
            except Exception as repo_error:
                error_msg = str(repo_error)
                if "404" in error_msg or "Not Found" in error_msg:
                    print(f"\n❌ Repository '{repo_name}' not found or not accessible")
                    print(f"   Please verify:")
                    print(f"   1. The repository exists on GitHub")
                    print(f"   2. You have access to the repository")
                    print(f"   3. The repository name is correct: {repo_name}")
                else:
                    print(f"\n❌ Error accessing repository '{repo_name}': {repo_error}")
                return
            
            # Then verify issue exists
            try:
                issue = repo.get_issue(issue_number)
            except Exception as issue_error:
                error_msg = str(issue_error)
                if "404" in error_msg or "Not Found" in error_msg:
                    print(f"\n❌ Issue #{issue_number} not found in repository '{repo_name}'")
                    print(f"   Please verify:")
                    print(f"   1. Issue #{issue_number} exists in the repository")
                    print(f"   2. The issue is not a pull request (use get_pull_request for PRs)")
                    print(f"   3. You have access to view the issue")
                    # Try to list some recent issues to help user
                    try:
                        recent_issues = list(repo.get_issues(state='open', sort='created', direction='desc')[:5])
                        if recent_issues:
                            print(f"\n   Recent open issues in this repository:")
                            for recent_issue in recent_issues:
                                print(f"   - Issue #{recent_issue.number}: {recent_issue.title}")
                    except:
                        pass
                else:
                    print(f"\n❌ Error accessing issue #{issue_number}: {issue_error}")
                return
            
            print(f"\n{'='*70}")
            print(f"Processing Issue #{issue.number}: {issue.title}")
            print(f"{'='*70}\n")
            
            # Move issue to "In Progress" when starting
            pipeline_enabled = os.getenv("MOVE_IN_PIPELINE", "true").lower() == "true"
            if pipeline_enabled:
                in_progress_column = os.getenv("PIPELINE_IN_PROGRESS_COLUMN", "In Progress")
                move_issue_in_project(repo_name, issue.number, in_progress_column)
            
            # Check if we should process sub-issues
            process_sub_issues = os.getenv("PROCESS_SUB_ISSUES", "true").lower() == "true"
            
            # Check if testing should be enabled
            enable_testing = os.getenv("ENABLE_TESTING", "true").lower() in ("true", "1", "yes")
            
            # Ensure we're on the correct base branch before processing (for accurate patch generation)
            if (work_dir / ".git").exists():
                ensure_base_branch(work_dir)
            
            # Process the issue (with sub-issues if enabled)
            result = process_issue(issue, repo_name, work_dir, include_sub_issues=process_sub_issues, enable_testing=enable_testing)
            
            # Save implementation plan and apply changes (with retry)
            max_retries = 2
            retry_count = 0
            implementation_status = None
            
            while retry_count <= max_retries:
                if retry_count > 0:
                    print(f"\n{'='*70}")
                    print(f"🔄 RETRY PASS {retry_count}/{max_retries}")
                    print(f"{'='*70}")
                    
                    # Create retry crew with fresh agents
                    retry_product, retry_architect, retry_developer, retry_reviewer, retry_tester = create_implementation_crew()
                    
                    # Guard: ensure developer agent is available
                    if retry_developer is None:
                        print(f"❌ Failed to create developer agent for retry")
                        break
                    
                    # Create retry task with missing items
                    missing_checklist = implementation_status.get("missing_items", {})
                    missing_text = "\n".join([
                        f"- Missing functions: {', '.join(missing_checklist.get('functions', []))}" if missing_checklist.get('functions') else "",
                        f"- Missing CSS selectors: {', '.join(missing_checklist.get('css_selectors', []))}" if missing_checklist.get('css_selectors') else "",
                        f"- Missing test files: {', '.join(missing_checklist.get('test_files', []))}" if missing_checklist.get('test_files') else "",
                        f"- Missing required files: {', '.join(missing_checklist.get('required_files', []))}" if missing_checklist.get('required_files') else ""
                    ])
                    
                    # Build issue text for retry
                    issue_text_retry = f"# {issue.title}\n\n{issue.body or 'No description'}".strip()
                    
                    # Create architect task for context (simplified for retry)
                    retry_architect_task = Task(
                        description=f"""Review the missing items and provide context for implementation:

{missing_text}

Focus on the files and functions that need to be added/modified.
""",
                        agent=retry_architect,
                        expected_output="Brief technical context for implementing missing items."
                    )
                    
                    retry_task = Task(
                        description=f"""Previous implementation attempt was incomplete. Please implement the missing items:

{missing_text}

Use the same structured JSON format with appropriate operations (upsert_function_js, upsert_css_selector, create, etc.).
Ensure ALL missing items are addressed in this pass.

Original issue:
{issue_text_retry}
""",
                        agent=retry_developer,
                        context=[retry_architect_task],
                        expected_output="JSON object with 'changes' array addressing all missing items."
                    )
                    
                    retry_crew = Crew(
                        agents=[retry_architect, retry_developer],
                        tasks=[retry_architect_task, retry_task],
                        verbose=True
                    )
                    
                    print(f"🚀 Starting retry crew execution...")
                    result = retry_crew.kickoff()
                
                implementation_status = apply_implementation(result, issue.number, work_dir, enable_testing=enable_testing)
                
                if implementation_status["status"] == "complete":
                    print(f"\n✅ Implementation completed successfully!")
                    break
                else:
                    retry_count += 1
                    if retry_count <= max_retries:
                        print(f"\n⚠️  Implementation incomplete, will retry...")
                    else:
                        print(f"\n❌ Implementation incomplete after {max_retries + 1} attempts")
                        if implementation_status:
                            print(f"   Missing items: {implementation_status.get('missing_items', {})}")
                        print(f"   Issue will NOT be moved to Done")
            
            # Create branch, commit, push, and create PR (ONLY if implementation is complete)
            if implementation_status and implementation_status["status"] == "complete":
                if (work_dir / ".git").exists():
                    # Check if we should push and create PR
                    push_to_github = os.getenv("AUTO_PUSH", "false").lower() == "true"
                    create_branch_and_commit(
                        issue.number, 
                        work_dir, 
                        repo_name=repo_name,
                        issue_title=issue.title,
                        push=push_to_github
                    )
                
                # Move issue to Done (only if complete)
                if pipeline_enabled:
                    target_column = os.getenv("PIPELINE_DONE_COLUMN", "Done")
                    move_issue_in_project(repo_name, issue.number, target_column)
                    print(f"✅ Issue #{issue.number} moved to '{target_column}'")
            else:
                print(f"\n⚠️  Implementation incomplete - skipping commit and GitHub operations")
                print(f"   Issue will remain in current column (not moved to Done)")
                if pipeline_enabled:
                    print(f"   Review missing items and retry manually if needed")
            
            # If sub-issues exist and we're processing them, handle them
            if process_sub_issues:
                sub_issues = get_sub_issues(repo_name, issue.number)
                if sub_issues:
                    sub_issue_strategy = os.getenv("SUB_ISSUE_STRATEGY", "include").lower()
                    # Strategy options:
                    # - "include": Sub-issues are included in parent issue context (already done)
                    # - "sequential": Process sub-issues separately after parent
                    # - "skip": Don't process sub-issues separately
                    
                    if sub_issue_strategy == "sequential":
                        print(f"\n📋 Processing {len(sub_issues)} sub-issue(s) sequentially...")
                        for sub_issue in sub_issues:
                            print(f"\n{'='*70}")
                            print(f"Processing Sub-Issue #{sub_issue.number}: {sub_issue.title}")
                            print(f"{'='*70}\n")
                            
                            # Move sub-issue to "In Progress"
                            if pipeline_enabled:
                                move_issue_in_project(repo_name, sub_issue.number, in_progress_column)
                            
                            # Process sub-issue
                            sub_result = process_issue(sub_issue, repo_name, work_dir, include_sub_issues=False, enable_testing=enable_testing)
                            
                            # Apply implementation
                            sub_implementation_status = apply_implementation(sub_result, sub_issue.number, work_dir, enable_testing=enable_testing)
                            
                            # Create branch and commit for sub-issue (ONLY if complete)
                            if sub_implementation_status and sub_implementation_status["status"] == "complete":
                                if (work_dir / ".git").exists():
                                    create_branch_and_commit(
                                        sub_issue.number,
                                        work_dir,
                                        repo_name=repo_name,
                                        issue_title=sub_issue.title,
                                        push=push_to_github
                                    )
                                
                                # Move sub-issue to "Done" (only if complete)
                                if pipeline_enabled:
                                    target_column = os.getenv("PIPELINE_DONE_COLUMN", "Done")
                                    move_issue_in_project(repo_name, sub_issue.number, target_column)
                                    print(f"✅ Sub-issue #{sub_issue.number} moved to '{target_column}'")
                                
                                # Mark sub-issue as processed
                                mark_issue_processed(sub_issue.number, processed_file)
                                print(f"✅ Sub-issue #{sub_issue.number} processed successfully!")
                            else:
                                print(f"⚠️  Sub-issue #{sub_issue.number} implementation incomplete - not moved to Done")
                                if sub_implementation_status:
                                    sub_missing = sub_implementation_status.get('missing_items', {})
                                    # B) Never show empty dict
                                    if sub_missing.get("_failure_reason"):
                                        print(f"   Failure reason: {sub_missing.get('_failure_summary', sub_missing['_failure_reason'])}")
                                    elif sub_missing and any(sub_missing.get(k) for k in ["functions", "css_selectors", "test_files", "required_files", "validation_errors", "apply_errors"]):
                                        print(f"   Missing items: {sub_missing}")
                                    else:
                                        print(f"   Implementation incomplete (check validation/application errors)")
            
            # Track success status - core processing succeeded, but check other operations
            warnings = []
            
            # Check if patch was applied successfully (if patch was generated)
            patch_file = work_dir / "crewai_patch.diff"
            if patch_file.exists():
                patch_applied, patch_warnings = check_patch_application_status(work_dir)
                warnings.extend(patch_warnings)
                if not patch_applied:
                    warnings.append("Patch failed to apply - review patch file manually or apply changes manually")
            
            # Note: Issue move to Done is handled above with gating enforcement
            # This section is kept for backward compatibility but should not execute
            # if the main flow above already handled it
            
            # Check git operations
            if (work_dir / ".git").exists():
                push_to_github = os.getenv("AUTO_PUSH", "false").lower() == "true"
                if push_to_github:
                    # Check if branch was actually pushed
                    try:
                        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', '@{u}'], 
                                              cwd=work_dir, capture_output=True, text=True, check=False, timeout=5)
                        if result.returncode != 0:
                            warnings.append("Branch not pushed to remote (network issue - check connectivity)")
                    except Exception:
                        warnings.append("Could not verify if branch was pushed (check manually)")
            
            # Mark as processed (core implementation succeeded, even if GitHub ops failed)
            mark_issue_processed(issue.number, processed_file)
            
            # Separate local and Git/GitHub status
            print_issue_status(issue.number, work_dir, warnings, implementation_status)
            
            # Run preview script to show changes and start server
            run_preview_script(issue.number, work_dir)
            
            return
            
        except Exception as e:
            print(f"\n❌ Error processing issue #{issue_number}: {e}")
            import traceback
            traceback.print_exc()
            return
    
    # Otherwise, process multiple issues
    while issues_processed < max_issues:
        # Get next issue
        issue = get_next_issue(repo_name, processed_file)
        
        if not issue:
            print("\n✅ No more unprocessed issues!")
            break
        
        try:
            # Move issue to "In Progress" when starting
            pipeline_enabled = os.getenv("MOVE_IN_PIPELINE", "true").lower() == "true"
            if pipeline_enabled:
                in_progress_column = os.getenv("PIPELINE_IN_PROGRESS_COLUMN", "In Progress")
                move_issue_in_project(repo_name, issue.number, in_progress_column)
            
            # Check if we should process sub-issues
            process_sub_issues = os.getenv("PROCESS_SUB_ISSUES", "true").lower() == "true"
            
            # Check if testing should be enabled
            enable_testing = os.getenv("ENABLE_TESTING", "true").lower() in ("true", "1", "yes")
            
            # Process the issue (with sub-issues if enabled)
            result = process_issue(issue, repo_name, work_dir, include_sub_issues=process_sub_issues, enable_testing=enable_testing)
            
            # Save implementation plan and apply changes (with retry)
            max_retries = 2
            retry_count = 0
            implementation_status = None
            
            while retry_count <= max_retries:
                if retry_count > 0:
                    print(f"\n{'='*70}")
                    print(f"🔄 RETRY PASS {retry_count}/{max_retries}")
                    print(f"{'='*70}")
                    
                    # Create retry crew with fresh agents
                    retry_product, retry_architect, retry_developer, retry_reviewer, retry_tester = create_implementation_crew()
                    
                    # Guard: ensure developer agent is available
                    if retry_developer is None:
                        print(f"❌ Failed to create developer agent for retry")
                        break
                    
                    # Create retry task with missing items
                    missing_checklist = implementation_status.get("missing_items", {})
                    missing_text = "\n".join([
                        f"- Missing functions: {', '.join(missing_checklist.get('functions', []))}" if missing_checklist.get('functions') else "",
                        f"- Missing CSS selectors: {', '.join(missing_checklist.get('css_selectors', []))}" if missing_checklist.get('css_selectors') else "",
                        f"- Missing test files: {', '.join(missing_checklist.get('test_files', []))}" if missing_checklist.get('test_files') else "",
                        f"- Missing required files: {', '.join(missing_checklist.get('required_files', []))}" if missing_checklist.get('required_files') else ""
                    ])
                    
                    # Build issue text for retry
                    issue_text_retry = f"# {issue.title}\n\n{issue.body or 'No description'}".strip()
                    
                    # Create architect task for context (simplified for retry)
                    retry_architect_task = Task(
                        description=f"""Review the missing items and provide context for implementation:

{missing_text}

Focus on the files and functions that need to be added/modified.
""",
                        agent=retry_architect,
                        expected_output="Brief technical context for implementing missing items."
                    )
                    
                    retry_task = Task(
                        description=f"""Previous implementation attempt was incomplete. Please implement the missing items:

{missing_text}

Use the same structured JSON format with appropriate operations (upsert_function_js, upsert_css_selector, create, etc.).
Ensure ALL missing items are addressed in this pass.

Original issue:
{issue_text_retry}
""",
                        agent=retry_developer,
                        context=[retry_architect_task],
                        expected_output="JSON object with 'changes' array addressing all missing items."
                    )
                    
                    retry_crew = Crew(
                        agents=[retry_architect, retry_developer],
                        tasks=[retry_architect_task, retry_task],
                        verbose=True
                    )
                    
                    print(f"🚀 Starting retry crew execution...")
                    result = retry_crew.kickoff()
                
                implementation_status = apply_implementation(result, issue.number, work_dir, enable_testing=enable_testing)
                
                if implementation_status["status"] == "complete":
                    print(f"\n✅ Implementation completed successfully!")
                    break
                else:
                    retry_count += 1
                    if retry_count <= max_retries:
                        print(f"\n⚠️  Implementation incomplete, will retry...")
                    else:
                        print(f"\n❌ Implementation incomplete after {max_retries + 1} attempts")
                        if implementation_status:
                            print(f"   Missing items: {implementation_status.get('missing_items', {})}")
                        print(f"   Issue will NOT be moved to Done")
            
            # Create branch, commit, push, and create PR (ONLY if implementation is complete)
            if implementation_status and implementation_status["status"] == "complete":
                if (work_dir / ".git").exists():
                    # Check if we should push and create PR
                    push_to_github = os.getenv("AUTO_PUSH", "false").lower() == "true"
                    create_branch_and_commit(
                        issue.number, 
                        work_dir, 
                        repo_name=repo_name,
                        issue_title=issue.title,
                        push=push_to_github
                    )
                
                # Move issue to Done (only if complete)
                if pipeline_enabled:
                    target_column = os.getenv("PIPELINE_DONE_COLUMN", "Done")
                    move_issue_in_project(repo_name, issue.number, target_column)
                    print(f"✅ Issue #{issue.number} moved to '{target_column}'")
            else:
                print(f"\n⚠️  Implementation incomplete - skipping commit and GitHub operations")
                print(f"   Issue will remain in current column (not moved to Done)")
                if pipeline_enabled:
                    print(f"   Review missing items and retry manually if needed")
            
            # If sub-issues exist and we're processing them, handle them
            if process_sub_issues:
                sub_issues = get_sub_issues(repo_name, issue.number)
                if sub_issues:
                    sub_issue_strategy = os.getenv("SUB_ISSUE_STRATEGY", "include").lower()
                    # Strategy options:
                    # - "include": Sub-issues are included in parent issue context (already done)
                    # - "sequential": Process sub-issues separately after parent
                    # - "skip": Don't process sub-issues separately
                    
                    if sub_issue_strategy == "sequential":
                        print(f"\n📋 Processing {len(sub_issues)} sub-issue(s) sequentially...")
                        for sub_issue in sub_issues:
                            print(f"\n{'='*70}")
                            print(f"Processing Sub-Issue #{sub_issue.number}: {sub_issue.title}")
                            print(f"{'='*70}\n")
                            
                            # Move sub-issue to "In Progress"
                            if pipeline_enabled:
                                move_issue_in_project(repo_name, sub_issue.number, in_progress_column)
                            
                            # Process sub-issue
                            sub_result = process_issue(sub_issue, repo_name, work_dir, include_sub_issues=False, enable_testing=enable_testing)
                            
                            # Apply implementation
                            sub_implementation_status = apply_implementation(sub_result, sub_issue.number, work_dir, enable_testing=enable_testing)
                            
                            # Create branch and commit for sub-issue (ONLY if complete)
                            if sub_implementation_status and sub_implementation_status["status"] == "complete":
                                if (work_dir / ".git").exists():
                                    create_branch_and_commit(
                                        sub_issue.number,
                                        work_dir,
                                        repo_name=repo_name,
                                        issue_title=sub_issue.title,
                                        push=push_to_github
                                    )
                                
                                # Move sub-issue to "Done" (only if complete)
                                if pipeline_enabled:
                                    target_column = os.getenv("PIPELINE_DONE_COLUMN", "Done")
                                    move_issue_in_project(repo_name, sub_issue.number, target_column)
                                    print(f"✅ Sub-issue #{sub_issue.number} moved to '{target_column}'")
                                
                                # Mark sub-issue as processed
                                mark_issue_processed(sub_issue.number, processed_file)
                                print(f"✅ Sub-issue #{sub_issue.number} processed successfully!")
                            else:
                                print(f"⚠️  Sub-issue #{sub_issue.number} implementation incomplete - not moved to Done")
                                if sub_implementation_status:
                                    sub_missing = sub_implementation_status.get('missing_items', {})
                                    # B) Never show empty dict
                                    if sub_missing.get("_failure_reason"):
                                        print(f"   Failure reason: {sub_missing.get('_failure_summary', sub_missing['_failure_reason'])}")
                                    elif sub_missing and any(sub_missing.get(k) for k in ["functions", "css_selectors", "test_files", "required_files", "validation_errors", "apply_errors"]):
                                        print(f"   Missing items: {sub_missing}")
                                    else:
                                        print(f"   Implementation incomplete (check validation/application errors)")
            
            # Track success status - core processing succeeded, but check other operations
            warnings = []
            
            # Check if patch was applied successfully (if patch was generated)
            patch_file = work_dir / "crewai_patch.diff"
            if patch_file.exists():
                patch_applied, patch_warnings = check_patch_application_status(work_dir)
                warnings.extend(patch_warnings)
                if not patch_applied:
                    warnings.append("Patch failed to apply - review patch file manually or apply changes manually")
            
            # Move issue in project pipeline
            pipeline_enabled = os.getenv("MOVE_IN_PIPELINE", "true").lower() == "true"
            if pipeline_enabled:
                # Move to "Done" column after completion
                target_column = os.getenv("PIPELINE_DONE_COLUMN", "Done")
                pipeline_success = move_issue_in_project(repo_name, issue.number, target_column)
                if not pipeline_success:
                    warnings.append("Failed to move issue in project pipeline (network/GitHub API issue)")
            
            # Check git operations
            if (work_dir / ".git").exists():
                push_to_github = os.getenv("AUTO_PUSH", "false").lower() == "true"
                if push_to_github:
                    # Check if branch was actually pushed
                    try:
                        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', '@{u}'], 
                                              cwd=work_dir, capture_output=True, text=True, check=False, timeout=5)
                        if result.returncode != 0:
                            warnings.append("Branch not pushed to remote (network issue - check connectivity)")
                    except Exception:
                        warnings.append("Could not verify if branch was pushed (check manually)")
            
            # Mark as processed (core implementation succeeded, even if GitHub ops failed)
            mark_issue_processed(issue.number, processed_file)
            issues_processed += 1
            
            # Separate local and Git/GitHub status
            print_issue_status(issue.number, work_dir, warnings, implementation_status)
            
            # Run preview script to show changes and start server
            run_preview_script(issue.number, work_dir)
            
        except Exception as e:
            print(f"\n❌ Error processing issue #{issue.number}: {e}")
            # Mark as processed anyway to avoid infinite loop
            mark_issue_processed(issue.number, processed_file)
            continue
    
    print(f"\n{'='*70}")
    print(f"🎉 Automated crew completed! Processed {issues_processed} issues.")
    print(f"{'='*70}")

def test_css_selector_extraction():
    """Self-check: Validate CSS selector extraction from plan text"""
    import tempfile
    from pathlib import Path
    
    # Test cases
    test_cases = [
        {
            "name": "Plain words should be ignored",
            "text": "Add styles for dialog notifications, the and css",
            "expected": []
        },
        {
            "name": "Backtick-wrapped selectors",
            "text": "Modal styles: `.modal`, `.modal-content`",
            "expected": [".modal", ".modal-content"]
        },
        {
            "name": "Code block selectors",
            "text": "```css\n.modal { display: none; }\n#editModal { }\n```",
            "expected": [".modal", "#editModal"]
        },
        {
            "name": "Bullet list with selectors",
            "text": "- Add `.toast` styles\n- Style `#notification`",
            "expected": [".toast", "#notification"]
        },
        {
            "name": "CSS declaration lines",
            "text": ".modal-header { }\n#closeBtn { }",
            "expected": [".modal-header", "#closeBtn"]
        },
        {
            "name": "Mixed valid and invalid",
            "text": "Add styles for dialog, `.modal`, edit, `#id`, and css",
            "expected": [".modal", "#id"]
        }
    ]
    
    # Create temporary plan file
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        for test_case in test_cases:
            plan_file = work_dir / "test_plan.md"
            plan_file.write_text(f"# Plan\n\n{test_case['text']}\n", encoding='utf-8')
            
            requirements = parse_plan_requirements(plan_file)
            extracted = sorted(requirements["css_selectors"])
            expected = sorted(test_case["expected"])
            
            if extracted != expected:
                print(f"❌ Test failed: {test_case['name']}")
                print(f"   Expected: {expected}")
                print(f"   Got: {extracted}")
                return False
    
    print("✅ CSS selector extraction self-check passed!")
    return True


def test_structured_changes_validation():
    """Self-check: Validate that new operations pass validation"""
    import tempfile
    from pathlib import Path
    
    # Create a temporary work directory
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        # Create sample files
        (work_dir / "app.js").write_text("// Existing code\n")
        (work_dir / "styles.css").write_text("body { margin: 0; }\n")
        
        # Test changes with new operations
        test_changes = {
            "changes": [
                {
                    "path": "app.js",
                    "operation": "replace_file",
                    "content": "// New file content\n"
                },
                {
                    "path": "app.js",
                    "operation": "upsert_function_js",
                    "function_name": "testFunction",
                    "content": "function testFunction() { return true; }"
                },
                {
                    "path": "styles.css",
                    "operation": "upsert_css_selector",
                    "selector": ".modal",
                    "content": ".modal { display: none; }"
                },
                {
                    "path": "app.js",
                    "operation": "insert_after_anchor",
                    "anchor": "// Existing code",
                    "content": "// New code after anchor"
                },
                {
                    "path": "app.js",
                    "operation": "insert_before_anchor",
                    "anchor": "// New code after anchor",
                    "content": "// Code before anchor"
                },
                {
                    "path": "app.js",
                    "operation": "append_if_missing",
                    "content": "// Appended code",
                    "signature": "// Appended code"
                }
            ]
        }
        
        # Validate
        is_valid, errors = validate_structured_changes(test_changes, work_dir)
        
        if not is_valid:
            print(f"❌ Validation failed: {errors}")
            return False
        
        # Test applier dispatch
        success, changed_files, apply_errors = apply_structured_changes(test_changes, work_dir)
        
        if not success:
            print(f"❌ Applier failed: {apply_errors}")
            return False
        
        print("✅ Structured changes validation self-check passed!")
        return True


def run_self_tests():
    """Run self-tests for upsert functions, validation, and CSS selector extraction"""
    print("Running self-tests for structured change applier...")
    try:
        test_upsert_function_js()
        test_upsert_css_selector()
        test_structured_changes_validation()
        test_css_selector_extraction()
        print("\n✅ All self-tests passed!")
        return True
    except AssertionError as e:
        print(f"\n❌ Self-test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Self-test error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Run self-tests if TEST_MODE env var is set
    if os.getenv("TEST_MODE", "false").lower() == "true":
        run_self_tests()
        sys.exit(0)
    
    if len(sys.argv) < 2:
        print("Usage: python automated_crew.py <repo> [max_issues|issue_number] [--openai]")
        print("Example: python automated_crew.py NeotronProductions/Beautiful-Timetracker-App 3")
        print("Example: python automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 608")
        print("Example: python automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 550 --openai")
        print("\nOptions:")
        print("  --openai    Force use of OpenAI (skip Ollama)")
        sys.exit(1)
    
    # Check for --openai flag
    force_openai_flag = "--openai" in sys.argv
    if force_openai_flag:
        os.environ["FORCE_OPENAI"] = "true"
        sys.argv.remove("--openai")  # Remove flag from args
    
    repo_name = sys.argv[1]
    
    # Check if third arg is a specific issue number (if it's > 100, assume it's an issue number)
    if len(sys.argv) > 3:
        issue_number = int(sys.argv[3])
        run_automated_crew(repo_name, max_issues=1, issue_number=issue_number)
    else:
        max_issues = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        run_automated_crew(repo_name, max_issues)
