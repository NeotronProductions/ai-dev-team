# 📋 Sub-Issues Handling Guide

## Overview

CrewAI now supports handling GitHub issues that have sub-issues (child issues). This allows you to break down large user stories into smaller, manageable tasks.

## How Sub-Issues Are Detected

The system detects sub-issues in two ways:

1. **GitHub Sub-Issues API** (if available)
   - Uses the official GitHub API endpoint for sub-issues
   - Works with GitHub Enterprise or projects that support sub-issues

2. **Issue Body Parsing** (fallback)
   - Scans the issue body for references like `#123`, `#456`
   - Includes any open issues referenced in the parent issue
   - Automatically filters out the parent issue itself

## Configuration

Add these environment variables to your `.env` file:

```bash
# Enable/disable sub-issue processing (default: true)
PROCESS_SUB_ISSUES=true

# Strategy for handling sub-issues (default: include)
# Options:
#   - "include": Sub-issues are included in parent issue context (recommended)
#   - "sequential": Process sub-issues separately after parent
#   - "skip": Don't process sub-issues separately
SUB_ISSUE_STRATEGY=include
```

## Processing Strategies

### 1. "include" Strategy (Default) ✅ Recommended

**How it works:**
- Sub-issues are automatically included in the parent issue's context
- The Architect and Developer agents see all sub-issues when planning
- All sub-issues are addressed in a single implementation
- One PR is created for the entire parent issue

**Best for:**
- Related tasks that should be implemented together
- Breaking down a feature into logical components
- When sub-issues are tightly coupled

**Example:**
```
Parent Issue #100: "Add user authentication"
  - Sub-issue #101: "Create login form"
  - Sub-issue #102: "Add password validation"
  - Sub-issue #103: "Implement session management"

Result: One implementation that addresses all three sub-issues
```

### 2. "sequential" Strategy

**How it works:**
- Parent issue is processed first
- Then each sub-issue is processed separately
- Each sub-issue gets its own branch, commit, and PR
- Sub-issues are processed in the order they appear

**Best for:**
- Independent tasks that can be done separately
- When you want separate PRs for each sub-issue
- When sub-issues have dependencies on each other

**Example:**
```
Parent Issue #100: "Add user authentication"
  - Sub-issue #101: "Create login form" → PR #1
  - Sub-issue #102: "Add password validation" → PR #2
  - Sub-issue #103: "Implement session management" → PR #3

Result: Three separate implementations and PRs
```

### 3. "skip" Strategy

**How it works:**
- Sub-issues are detected but not processed separately
- Only the parent issue is processed
- Sub-issues are still shown in the context for reference

**Best for:**
- When sub-issues are just documentation/reference
- When you want to handle sub-issues manually
- When sub-issues are tracked elsewhere

## Usage Examples

### Example 1: Feature with Components (Use "include")

```markdown
Issue #50: "Add dark mode support"

This issue includes:
- #51: Update CSS variables for dark theme
- #52: Add theme toggle button
- #53: Persist theme preference in localStorage
```

**Configuration:**
```bash
PROCESS_SUB_ISSUES=true
SUB_ISSUE_STRATEGY=include
```

**Result:** One implementation covering all three sub-issues.

### Example 2: Independent Tasks (Use "sequential")

```markdown
Issue #60: "Improve performance"

This issue includes:
- #61: Optimize image loading
- #62: Add code splitting
- #63: Implement lazy loading
```

**Configuration:**
```bash
PROCESS_SUB_ISSUES=true
SUB_ISSUE_STRATEGY=sequential
```

**Result:** Three separate implementations, each with its own PR.

## Dashboard Display

The dashboard will show:
- Parent issues with sub-issue indicators
- Number of sub-issues found
- Sub-issue titles when processing

## Pipeline Movement

When using "sequential" strategy:
- Each sub-issue moves through the pipeline independently
- Sub-issues are moved to "In Progress" when processing starts
- Sub-issues are moved to "Done" when processing completes

## Best Practices

1. **Use "include" for related features**
   - When sub-issues are part of the same feature
   - When you want one cohesive implementation

2. **Use "sequential" for independent tasks**
   - When sub-issues can be done in any order
   - When you want separate PRs for review

3. **Link issues clearly**
   - Reference sub-issues in the parent issue body
   - Use clear numbering: "This includes #101, #102, #103"

4. **Keep sub-issues focused**
   - Each sub-issue should be a single, clear task
   - Avoid making sub-issues too large

## Troubleshooting

### Sub-issues not detected?

1. **Check issue body** - Make sure sub-issues are referenced with `#123` format
2. **Verify sub-issues are open** - Only open issues are included
3. **Check API access** - Ensure GitHub token has proper permissions

### Sub-issues processed when they shouldn't be?

1. Set `PROCESS_SUB_ISSUES=false` to disable completely
2. Use `SUB_ISSUE_STRATEGY=skip` to detect but not process
3. Remove sub-issue references from parent issue body

### Want to process only specific sub-issues?

Currently, all detected sub-issues are processed. To exclude specific ones:
- Remove the reference from the parent issue body
- Or close the sub-issue (only open issues are included)

## Future Enhancements

Potential improvements:
- [ ] Selective sub-issue processing (choose which ones)
- [ ] Dependency ordering (process sub-issues in dependency order)
- [ ] Sub-issue templates (auto-create sub-issues from parent)
- [ ] Visual hierarchy in dashboard

## Summary

Sub-issues support helps you:
- ✅ Break down large features into manageable tasks
- ✅ Keep related work together or separate as needed
- ✅ Maintain clear issue hierarchies
- ✅ Automate complex workflows

Choose the strategy that best fits your workflow!
