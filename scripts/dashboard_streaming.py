#!/usr/bin/env python3
"""
CrewAI Dashboard with Real-Time Streaming Progress
Shows live progress of each agent as they process issues
"""

import streamlit as st
import os
import subprocess
import json
import threading
import queue
from pathlib import Path
from dotenv import load_dotenv
from github import Github
from github.Auth import Token

load_dotenv()

st.set_page_config(
    page_title="CrewAI Dashboard - Live Progress",
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
if 'current_issue' not in st.session_state:
    st.session_state.current_issue = None
if 'stream_output' not in st.session_state:
    st.session_state.stream_output = []
if 'agent_status' not in st.session_state:
    st.session_state.agent_status = {}

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

def get_sub_issues(repo_name, issue_number):
    """Get sub-issues (child issues) for a given parent issue"""
    g = get_github_client()
    if not g:
        return []
    
    try:
        repo = g.get_repo(repo_name)
        
        # Method 1: Try GitHub Sub-Issues API (if available)
        try:
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
        parent_issue = repo.get_issue(issue_number)
        if not parent_issue.body:
            return []
        
        import re
        issue_refs = re.findall(r'#(\d+)', parent_issue.body)
        sub_issues = []
        
        for ref_num in issue_refs:
            try:
                ref_num_int = int(ref_num)
                if ref_num_int != issue_number:
                    linked_issue = repo.get_issue(ref_num_int)
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
        return []

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

def execute_issue_streaming(issue_number, repo_name):
    """Execute issue with real-time streaming output"""
    script_path = Path(__file__).parent / "automated_crew.py"
    if not script_path.exists():
        return None, "automated_crew.py not found!", 1
    
    # Clear previous output
    st.session_state.stream_output = []
    st.session_state.agent_status = {}
    
    try:
        # Start process with real-time output
        process = subprocess.Popen(
            ['python3', str(script_path), repo_name, '1', str(issue_number)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            cwd=Path(__file__).parent
        )
        
        # Stream output in real-time
        output_lines = []
        current_agent = None
        
        # Create placeholder for live updates
        status_placeholder = st.empty()
        output_placeholder = st.empty()
        
        for line in process.stdout:
            line = line.strip()
            if line:
                output_lines.append(line)
                st.session_state.stream_output.append(line)
                
                # Detect agent activity (CrewAI verbose output patterns)
                if "Product Manager" in line or "role='Product Manager'" in line or "Product Manager" in line:
                    current_agent = "Product Manager"
                    st.session_state.agent_status["current"] = "Product Manager"
                    st.session_state.agent_status["Product Manager"] = "🔄 Working..."
                elif "Software Architect" in line or "role='Software Architect'" in line:
                    current_agent = "Software Architect"
                    st.session_state.agent_status["current"] = "Software Architect"
                    st.session_state.agent_status["Software Architect"] = "🔄 Working..."
                elif "Developer" in line and ("role=" in line or "role:" in line):
                    current_agent = "Developer"
                    st.session_state.agent_status["current"] = "Developer"
                    st.session_state.agent_status["Developer"] = "🔄 Working..."
                elif "Code Reviewer" in line or "role='Code Reviewer'" in line:
                    current_agent = "Code Reviewer"
                    st.session_state.agent_status["current"] = "Code Reviewer"
                    st.session_state.agent_status["Code Reviewer"] = "🔄 Working..."
                elif "Task" in line and ("completed" in line.lower() or "finished" in line.lower()):
                    if current_agent:
                        st.session_state.agent_status[current_agent] = "✅ Completed"
                
                # Update display in real-time
                with status_placeholder.container():
                    display_agent_status()
                
                with output_placeholder.container():
                    display_live_output()
        
        process.wait()
        returncode = process.returncode
        
        # Mark final status
        if returncode == 0:
            for agent in ["Product Manager", "Software Architect", "Developer", "Code Reviewer"]:
                if agent in st.session_state.agent_status:
                    if "✅" not in str(st.session_state.agent_status[agent]):
                        st.session_state.agent_status[agent] = "✅ Completed"
        
        # Final update
        with status_placeholder.container():
            display_agent_status()
        
        return "\n".join(output_lines), "", returncode
        
    except Exception as e:
        import traceback
        return None, f"{str(e)}\n{traceback.format_exc()}", 1

def display_agent_status():
    """Display agent status in real-time"""
    st.markdown("### 👥 Agent Status")
    
    agents = ["Product Manager", "Software Architect", "Developer", "Code Reviewer"]
    cols = st.columns(4)
    
    for i, agent in enumerate(agents):
        with cols[i]:
            status = st.session_state.agent_status.get(agent, "⏳ Pending")
            current = st.session_state.agent_status.get("current", "")
            
            if agent == current:
                st.markdown(f"**{agent}**<br>🔄 **Active**", unsafe_allow_html=True)
                st.progress(0.5)  # Show progress
            elif "✅" in str(status):
                st.markdown(f"**{agent}**<br>✅ **Done**", unsafe_allow_html=True)
                st.progress(1.0)  # Complete
            else:
                st.markdown(f"**{agent}**<br>⏳ Pending", unsafe_allow_html=True)
                st.progress(0.0)  # Not started

def display_live_output():
    """Display live output stream"""
    st.markdown("### 📝 Live Output Stream")
    output_text = "\n".join(st.session_state.stream_output[-200:])  # Last 200 lines
    if output_text:
        st.code(output_text, language="text")
    else:
        st.info("Waiting for output...")

def display_progress():
    """Display real-time progress"""
    st.markdown("### 🔄 Live Progress")
    
    # Agent status
    agents = ["Product Manager", "Software Architect", "Developer", "Code Reviewer"]
    cols = st.columns(4)
    
    for i, agent in enumerate(agents):
        with cols[i]:
            status = st.session_state.agent_status.get(agent, "⏳ Pending")
            current = st.session_state.agent_status.get("current", "")
            
            if agent == current:
                st.markdown(f"**{agent}**<br>🔄 {status}", unsafe_allow_html=True)
            elif "✅" in str(status):
                st.markdown(f"**{agent}**<br>{status}", unsafe_allow_html=True)
            else:
                st.markdown(f"**{agent}**<br>⏳ Pending", unsafe_allow_html=True)
    
    # Stream output
    st.markdown("### 📝 Live Output")
    output_text = "\n".join(st.session_state.stream_output[-100:])  # Last 100 lines
    st.code(output_text, language="text")

# Main title
st.title("🤖 CrewAI Dashboard - Live Progress")
st.markdown("---")

# Status section
col1, col2, col3 = st.columns(3)

with col1:
    status = "🟢 Active" if not st.session_state.processing else "🟡 Processing"
    st.metric("Status", status)

with col2:
    if st.session_state.issues_loaded:
        total = len(st.session_state.github_issues)
        st.metric("Total Issues", total)
    else:
        st.metric("Total Issues", "-")

with col3:
    if st.session_state.current_issue:
        st.metric("Current Issue", f"#{st.session_state.current_issue}")
    else:
        st.metric("Current Issue", "-")

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

# Processing Section
if st.session_state.processing and st.session_state.current_issue:
    st.markdown("---")
    st.header(f"🔄 Processing Issue #{st.session_state.current_issue}")
    
    # Execute with streaming
    stdout, stderr, returncode = execute_issue_streaming(
        st.session_state.current_issue,
        st.session_state.github_repo
    )
    
    st.session_state.processing = False
    
    st.markdown("---")
    if returncode == 0:
        st.success(f"✅ Issue #{st.session_state.current_issue} completed!")
    else:
        st.error(f"❌ Issue #{st.session_state.current_issue} failed")
        if stderr:
            st.text_area("Error Details", stderr, height=200)
    
    # Show final output
    if stdout:
        with st.expander("View Complete Output", expanded=False):
            st.code(stdout, language="text")
    
    st.session_state.current_issue = None
    
    if st.button("🔄 Process Next Issue", use_container_width=True):
        # Find next unprocessed issue
        for issue in st.session_state.github_issues:
            if issue.number != st.session_state.current_issue:
                st.session_state.current_issue = issue.number
                st.session_state.processing = True
                st.rerun()
                break

# Issues List
if st.session_state.issues_loaded and st.session_state.github_issues:
    st.markdown("---")
    st.subheader(f"📋 Open Issues ({len(st.session_state.github_issues)})")
    
    # Filter and sort
    col1, col2 = st.columns([2, 1])
    with col1:
        sort_by = st.selectbox("Sort by", ["Updated", "Number"], key="sort_by")
    
    filtered = st.session_state.github_issues
    if sort_by == "Updated":
        filtered = sorted(filtered, key=lambda x: x.updated_at, reverse=True)
    else:
        filtered = sorted(filtered, key=lambda x: x.number, reverse=True)
    
    # Display issues
    for issue in filtered[:20]:
        # Check for sub-issues
        sub_issues = get_sub_issues(st.session_state.github_repo, issue.number)
        has_sub_issues = len(sub_issues) > 0
        
        # Build expander title with sub-issue indicator
        title = f"#{issue.number}: {issue.title}"
        if has_sub_issues:
            title += f" 📋 ({len(sub_issues)} sub-issue{'s' if len(sub_issues) > 1 else ''})"
        
        with st.expander(title, expanded=False):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.write(f"**State:** {issue.state} | **URL:** [{issue.html_url}]({issue.html_url})")
                
                # Show sub-issues if they exist
                if has_sub_issues:
                    st.markdown("**📋 Sub-Issues:**")
                    for sub in sub_issues:
                        st.markdown(f"- **#{sub.number}**: [{sub.title}]({sub.html_url})")
                    st.markdown("---")
                
                if issue.body:
                    st.markdown(issue.body[:300] + "..." if len(issue.body) > 300 else issue.body)
            
            with col2:
                if not st.session_state.processing:
                    if st.button(f"🚀 Process", key=f"process_{issue.number}", use_container_width=True):
                        st.session_state.processing = True
                        st.session_state.current_issue = issue.number
                        st.rerun()

# System Info
st.markdown("---")
with st.expander("System Information"):
    st.json({
        "Working Directory": str(Path.cwd()),
        "GitHub Token": "✓ Configured" if os.getenv("GITHUB_TOKEN") else "✗ Not configured",
        "GitHub Repo": st.session_state.github_repo or "Not set"
    })
