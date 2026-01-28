#!/usr/bin/env python3
"""
Enhanced CrewAI Dashboard with Automated Issue Processing
Allows crew to automatically process issues one by one
"""

import streamlit as st
import os
import subprocess
import json
from pathlib import Path
from dotenv import load_dotenv
from github import Github
from github.Auth import Token

load_dotenv()

st.set_page_config(
    page_title="CrewAI Automated Dashboard",
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
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'processed_issues' not in st.session_state:
    processed_file = Path(__file__).parent.parent / "data" / "processed_issues.json"
    if processed_file.exists():
        with open(processed_file, 'r') as f:
            st.session_state.processed_issues = set(json.load(f))
    else:
        st.session_state.processed_issues = set()

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

def get_next_unprocessed_issue(issues):
    """Get the next unprocessed issue"""
    for issue in issues:
        if issue.number not in st.session_state.processed_issues:
            return issue
    return None

def mark_issue_processed(issue_number):
    """Mark an issue as processed"""
    st.session_state.processed_issues.add(issue_number)
    processed_file = Path(__file__).parent.parent / "data" / "processed_issues.json"
    with open(processed_file, 'w') as f:
        json.dump(list(st.session_state.processed_issues), f)

def execute_issue_automated(issue_number, repo_name):
    """Execute automated crew on an issue"""
    script_path = Path(__file__).parent / "automated_crew.py"
    if not script_path.exists():
        return None, "automated_crew.py not found!", 1
    
    try:
        result = subprocess.run(
            ['python3', str(script_path), repo_name, '1'],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes
            cwd=Path(__file__).parent
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return None, "Execution timed out (5 minutes)", 1
    except Exception as e:
        return None, str(e), 1

# Main title
st.title("🤖 CrewAI Automated Dashboard")
st.markdown("---")

# Status section
col1, col2, col3 = st.columns(3)

with col1:
    status = "🟢 Active" if not st.session_state.processing else "🟡 Processing"
    st.metric("Status", status)

with col2:
    st.metric("Processed Issues", len(st.session_state.processed_issues))

with col3:
    if st.session_state.issues_loaded:
        unprocessed = len([i for i in st.session_state.github_issues if i.number not in st.session_state.processed_issues])
        st.metric("Remaining", unprocessed)
    else:
        st.metric("Remaining", "-")

st.markdown("---")

# GitHub Integration Section
st.header("🔗 GitHub Integration")

col1, col2 = st.columns([3, 1])
with col1:
    repo_input = st.text_input(
        "GitHub Repository",
        value=st.session_state.github_repo,
        placeholder="owner/repo",
        disabled=st.session_state.processing
    )
with col2:
    if st.button("Load Issues", type="primary", disabled=st.session_state.processing):
        if repo_input:
            st.session_state.github_repo = repo_input
            with st.spinner(f"Loading issues from {repo_input}..."):
                issues = load_github_issues(repo_input)
                st.session_state.github_issues = issues
                st.session_state.issues_loaded = True
                st.success(f"Loaded {len(issues)} open issues!")
                st.rerun()

# Automated Processing Section
if st.session_state.issues_loaded and st.session_state.github_issues:
    st.markdown("---")
    st.header("⚙️ Automated Processing")
    
    next_issue = get_next_unprocessed_issue(st.session_state.github_issues)
    
    if next_issue:
        st.subheader(f"Next Issue: #{next_issue.number} - {next_issue.title}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Process This Issue", type="primary", use_container_width=True, 
                        disabled=st.session_state.processing):
                st.session_state.processing = True
                st.rerun()
        
        with col2:
            if st.button("⏭️ Skip This Issue", use_container_width=True, 
                        disabled=st.session_state.processing):
                mark_issue_processed(next_issue.number)
                st.success(f"Issue #{next_issue.number} skipped")
                st.rerun()
        
        with col3:
            if st.button("🔄 Process All Remaining", use_container_width=True,
                        disabled=st.session_state.processing):
                st.session_state.processing = True
                st.session_state.process_all = True
                st.rerun()
        
        # Show issue details
        with st.expander("View Issue Details"):
            st.write(f"**URL:** [{next_issue.html_url}]({next_issue.html_url})")
            st.write(f"**Created:** {next_issue.created_at.strftime('%Y-%m-%d')}")
            st.write(f"**Updated:** {next_issue.updated_at.strftime('%Y-%m-%d')}")
            if next_issue.body:
                st.markdown(f"**Description:**\n{next_issue.body[:500]}...")
    else:
        st.success("✅ All issues have been processed!")

# Processing status
if st.session_state.processing:
    st.markdown("---")
    st.header("🔄 Processing Status")
    
    if next_issue:
        with st.spinner(f"Processing issue #{next_issue.number}..."):
            stdout, stderr, returncode = execute_issue_automated(
                next_issue.number, 
                st.session_state.github_repo
            )
            
            if returncode == 0:
                st.success(f"✅ Issue #{next_issue.number} processed successfully!")
                mark_issue_processed(next_issue.number)
                
                if stdout:
                    with st.expander("View Output"):
                        st.text(stdout)
            else:
                st.error(f"❌ Failed to process issue #{next_issue.number}")
                if stderr:
                    st.text(stderr)
            
            st.session_state.processing = False
            
            # Continue to next if process_all is set
            if st.session_state.get('process_all', False):
                next_issue = get_next_unprocessed_issue(st.session_state.github_issues)
                if next_issue:
                    st.info(f"Moving to next issue: #{next_issue.number}")
                    st.rerun()
                else:
                    st.session_state.process_all = False
                    st.success("🎉 All issues processed!")
            
            st.rerun()

# Issues List
if st.session_state.issues_loaded:
    st.markdown("---")
    st.subheader(f"📋 All Issues ({len(st.session_state.github_issues)})")
    
    # Filter options
    col1, col2 = st.columns([2, 1])
    with col1:
        show_filter = st.selectbox(
            "Show",
            ["All", "Unprocessed", "Processed"],
            key="show_filter"
        )
    with col2:
        sort_by = st.selectbox("Sort by", ["Updated", "Number"], key="sort_by")
    
    # Filter issues
    filtered = st.session_state.github_issues
    if show_filter == "Unprocessed":
        filtered = [i for i in filtered if i.number not in st.session_state.processed_issues]
    elif show_filter == "Processed":
        filtered = [i for i in filtered if i.number in st.session_state.processed_issues]
    
    # Sort
    if sort_by == "Updated":
        filtered = sorted(filtered, key=lambda x: x.updated_at, reverse=True)
    else:
        filtered = sorted(filtered, key=lambda x: x.number, reverse=True)
    
    # Display
    for issue in filtered[:20]:  # Show first 20
        is_processed = issue.number in st.session_state.processed_issues
        status_icon = "✅" if is_processed else "⏳"
        
        with st.expander(f"{status_icon} #{issue.number}: {issue.title}", expanded=False):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**State:** {issue.state} | **URL:** [{issue.html_url}]({issue.html_url})")
                if issue.body:
                    st.markdown(issue.body[:300] + "..." if len(issue.body) > 300 else issue.body)
            with col2:
                if not is_processed:
                    if st.button(f"Process", key=f"process_{issue.number}"):
                        st.session_state.processing = True
                        st.session_state.current_issue = issue.number
                        st.rerun()

# System Info
st.markdown("---")
with st.expander("System Information"):
    st.json({
        "Working Directory": str(Path.cwd()),
        "GitHub Token": "✓ Configured" if os.getenv("GITHUB_TOKEN") else "✗ Not configured",
        "GitHub Repo": st.session_state.github_repo or "Not set",
        "Processed Issues": len(st.session_state.processed_issues)
    })
