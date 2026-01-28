#!/usr/bin/env python3
"""
CrewAI Dashboard with GitHub Integration
Enhanced dashboard for monitoring and managing CrewAI agents with GitHub issue execution.
"""

import streamlit as st
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from github import Github
from github.Auth import Token

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="CrewAI Dashboard",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'github_repo' not in st.session_state:
    st.session_state.github_repo = os.getenv("GITHUB_REPO", "")
if 'issues_loaded' not in st.session_state:
    st.session_state.issues_loaded = False
if 'github_issues' not in st.session_state:
    st.session_state.github_issues = []

def get_github_client():
    """Get authenticated GitHub client"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return None
    try:
        auth = Token(token)
        return Github(auth=auth)
    except Exception as e:
        st.error(f"Failed to authenticate with GitHub: {e}")
        return None

def load_github_issues(repo_name):
    """Load issues from GitHub repository"""
    g = get_github_client()
    if not g:
        return []
    
    try:
        repo = g.get_repo(repo_name)
        issues = list(repo.get_issues(state='open', sort='updated'))
        return issues
    except Exception as e:
        st.error(f"Failed to load issues: {e}")
        return []

def execute_issue(issue_number, repo_name):
    """Execute analysis for a GitHub issue"""
    script_path = Path(__file__).parent / "github_working.py"
    if not script_path.exists():
        st.error("github_working.py not found!")
        return None
    
    try:
        result = subprocess.run(
            ['python3', str(script_path), repo_name, str(issue_number)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path(__file__).parent
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return None, "Execution timed out", 1
    except Exception as e:
        return None, str(e), 1

# Main title
st.title("🤖 CrewAI Dashboard")
st.markdown("---")

# Status section
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Status", "Running", delta="Active")

with col2:
    runs_dir = Path(__file__).parent.parent / "runs"
    if runs_dir.exists():
        run_count = len(list(runs_dir.glob("*")))
    else:
        run_count = 0
    st.metric("Runs", run_count)

with col3:
    templates_dir = Path(__file__).parent.parent / "templates"
    if templates_dir.exists():
        template_count = len(list(templates_dir.glob("*.yaml"))) + len(list(templates_dir.glob("*.yml")))
    else:
        template_count = 0
    st.metric("Templates", template_count)

st.markdown("---")

# GitHub Integration Section
st.header("🔗 GitHub Integration")

# Repository input
col1, col2 = st.columns([3, 1])
with col1:
    repo_input = st.text_input(
        "GitHub Repository",
        value=st.session_state.github_repo,
        placeholder="owner/repo (e.g., NeotronProductions/Beautiful-Timetracker-App)",
        help="Enter the repository in format: owner/repo"
    )
with col2:
    if st.button("Load Issues", type="primary"):
        if repo_input:
            st.session_state.github_repo = repo_input
            with st.spinner(f"Loading issues from {repo_input}..."):
                issues = load_github_issues(repo_input)
                st.session_state.github_issues = issues
                st.session_state.issues_loaded = True
                st.success(f"Loaded {len(issues)} open issues!")
                st.rerun()
        else:
            st.warning("Please enter a repository name")

# Display issues if loaded
if st.session_state.issues_loaded and st.session_state.github_issues:
    st.markdown("---")
    st.subheader(f"📋 Open Issues ({len(st.session_state.github_issues)})")
    
    # Filter options
    col1, col2 = st.columns([2, 1])
    with col1:
        filter_label = st.selectbox(
            "Filter by Label",
            ["All"] + list(set([label.name for issue in st.session_state.github_issues for label in issue.labels])),
            key="label_filter"
        )
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Updated", "Created", "Number"],
            key="sort_by"
        )
    
    # Filter and sort issues
    filtered_issues = st.session_state.github_issues
    if filter_label != "All":
        filtered_issues = [i for i in filtered_issues if any(label.name == filter_label for label in i.labels)]
    
    if sort_by == "Updated":
        filtered_issues = sorted(filtered_issues, key=lambda x: x.updated_at, reverse=True)
    elif sort_by == "Created":
        filtered_issues = sorted(filtered_issues, key=lambda x: x.created_at, reverse=True)
    else:
        filtered_issues = sorted(filtered_issues, key=lambda x: x.number, reverse=True)
    
    # Display issues
    for issue in filtered_issues:
        with st.expander(f"#{issue.number}: {issue.title}", expanded=False):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Issue metadata
                labels_html = " ".join([f'<span style="background-color: #{label.color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; margin-right: 5px;">{label.name}</span>' for label in issue.labels])
                st.markdown(f"""
                **State:** {issue.state.upper()} | **Created:** {issue.created_at.strftime('%Y-%m-%d')} | **Updated:** {issue.updated_at.strftime('%Y-%m-%d')}
                
                **Labels:** {labels_html if labels_html else "None"}
                
                **URL:** [{issue.html_url}]({issue.html_url})
                """, unsafe_allow_html=True)
                
                # Issue body preview
                if issue.body:
                    body_preview = issue.body[:500] + "..." if len(issue.body) > 500 else issue.body
                    st.markdown(f"**Description:**\n{body_preview}")
                else:
                    st.info("No description provided")
            
            with col2:
                # Execute button
                if st.button(f"🚀 Execute #{issue.number}", key=f"execute_{issue.number}", use_container_width=True):
                    with st.spinner(f"Executing issue #{issue.number}..."):
                        stdout, stderr, returncode = execute_issue(issue.number, st.session_state.github_repo)
                        
                        if returncode == 0:
                            st.success("✅ Execution completed!")
                            if stdout:
                                st.text_area("Output", stdout, height=200, key=f"output_{issue.number}")
                            
                            # Auto-continue option
                            st.info("💡 **Workflow continues automatically!** The crew will process the next unprocessed issue.")
                            if st.button(f"⏭️ Continue to Next Issue", key=f"continue_{issue.number}", use_container_width=True):
                                st.rerun()
                        else:
                            st.error("❌ Execution failed")
                            if stderr:
                                st.text_area("Error", stderr, height=200, key=f"error_{issue.number}")
                            if stdout:
                                st.text_area("Output", stdout, height=200, key=f"stdout_{issue.number}")

elif st.session_state.issues_loaded and len(st.session_state.github_issues) == 0:
    st.info("No open issues found in this repository.")

st.markdown("---")

# System Information Section
st.header("System Information")

# Directory status
st.subheader("Directory Status")
col1, col2 = st.columns(2)

with col1:
    st.write("**Working Directory:**")
    st.code(str(Path.cwd()))
    
    st.write("**Runs Directory:**")
    if runs_dir.exists():
        st.success(f"✓ {runs_dir} exists")
    else:
        st.warning(f"⚠ {runs_dir} does not exist")

with col2:
    st.write("**Templates Directory:**")
    if templates_dir.exists():
        st.success(f"✓ {templates_dir} exists")
    else:
        st.warning(f"⚠ {templates_dir} does not exist")

# Environment info
st.subheader("Environment")
env_info = {
    "PORT": os.environ.get("PORT", "8001"),
    "Working Directory": str(Path.cwd()),
    "Python Version": os.sys.version.split()[0],
    "GitHub Token": "✓ Configured" if os.getenv("GITHUB_TOKEN") else "✗ Not configured",
    "GitHub Repo": st.session_state.github_repo or "Not set"
}
st.json(env_info)

# Quick actions
st.markdown("---")
st.subheader("⚡ Quick Actions")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Reload Issues", use_container_width=True):
        if st.session_state.github_repo:
            with st.spinner("Reloading issues..."):
                issues = load_github_issues(st.session_state.github_repo)
                st.session_state.github_issues = issues
                st.success(f"Reloaded {len(issues)} issues!")
                st.rerun()
        else:
            st.warning("Please set a repository first")

with col2:
    if st.button("📊 View All Runs", use_container_width=True):
        if runs_dir.exists():
            runs = list(runs_dir.glob("*"))
            st.write(f"Found {len(runs)} run files")
            for run in runs[:10]:
                st.write(f"- {run.name}")
        else:
            st.info("No runs directory found")

with col3:
    if st.button("📝 View Templates", use_container_width=True):
        if templates_dir.exists():
            templates = list(templates_dir.glob("*.yaml")) + list(templates_dir.glob("*.yml"))
            st.write(f"Found {len(templates)} templates")
            for template in templates[:10]:
                st.write(f"- {template.name}")
        else:
            st.info("No templates directory found")
