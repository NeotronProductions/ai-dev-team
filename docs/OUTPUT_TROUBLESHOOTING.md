# Output Troubleshooting Guide

## Issue: Minimal Output in Files

If your output files (like `issue_528_plan.md`) contain very little information, this guide will help you diagnose and fix the issue.

## Common Causes

### 1. Crew Execution Failed or Incomplete

**Symptoms:**
- Output file contains only a few lines
- Output seems incomplete or cut off
- Error messages in terminal but no detailed output saved

**Solution:**
- Check terminal output for errors
- Verify LLM is working (Ollama or OpenAI)
- Check network connectivity
- Review issue complexity (very large issues may timeout)

### 2. LLM Configuration Issues

**Symptoms:**
- Output is just error messages
- "Fallback to LiteLLM is not available" errors
- No actual agent responses

**Solution:**
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check OpenAI key is set
echo $OPENAI_API_KEY

# Verify in .env file
cat ~/ai-dev-team/.env
```

### 3. Result Object Not Properly Captured

**Symptoms:**
- Output file exists but is minimal
- Terminal shows execution completed
- No error messages

**Solution:**
The script has been updated to better capture results. Re-run the issue:

```bash
python3 scripts/automated_crew.py owner/repo 1 528
```

## Improved Output Capture

The script now:

1. **Captures Multiple Output Formats**
   - Main result string
   - Task outputs separately
   - Raw output if available
   - Debug information if minimal

2. **Adds Metadata**
   - Timestamp
   - Result type
   - Output length
   - Number of tasks

3. **Better Error Handling**
   - Saves error information if execution fails
   - Includes traceback in output file
   - Warns about minimal outputs

## Checking Output Quality

### Good Output Should Contain:

1. **User Story** (from Product Manager)
   - Clear acceptance criteria
   - Out of scope items
   - Risks identified

2. **Technical Plan** (from Architect)
   - Files to change
   - Implementation approach
   - Test strategy

3. **Implementation** (from Developer)
   - Code changes
   - Diff patch (if applicable)
   - Test code

4. **Code Review** (from Reviewer)
   - Correctness feedback
   - Security concerns
   - Edge cases
   - Style suggestions

### Minimal Output Example (Problem):

```markdown
# Implementation Plan for Issue #528

## Full Crew Output

Your final answer must be the great and the most complete as possible...
```

This indicates the crew didn't complete properly.

## Diagnostic Steps

### Step 1: Check Terminal Output

When running the crew, watch for:

```
🚀 Starting crew execution...
[Agent activity...]
Crew Execution Complete
Result type: <class 'crewai.agent.agent.Agent'>
Result length: 5000 characters
```

If you see very low character count (< 100), there's a problem.

### Step 2: Verify LLM is Working

```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Test with a simple query
curl http://localhost:11434/api/generate -d '{
  "model": "qwen2.5-coder:3b",
  "prompt": "Hello",
  "stream": false
}'
```

### Step 3: Check Issue Complexity

Very large or complex issues might:
- Timeout
- Exceed token limits
- Cause LLM errors

Try with a simpler issue first to verify the setup.

### Step 4: Review Error Logs

Check for errors in:
- Terminal output
- Output file (may contain error section)
- System logs

## Re-running Failed Issues

To re-run an issue that had minimal output:

```bash
# Remove from processed list (if needed)
# Edit: ~/ai-dev-team/data/processed_issues.json

# Re-run the issue
python3 scripts/automated_crew.py owner/repo 1 528
```

## Getting More Verbose Output

Enable verbose mode (already enabled by default):

```python
crew = Crew(
    agents=[...],
    tasks=[...],
    verbose=True  # Already set
)
```

## Manual Output Inspection

Check what was actually captured:

```bash
# View the output file
cat ~/dev/Beautiful-Timetracker-App/implementations/issue_528_plan.md

# Check file size (should be > 1KB for good output)
ls -lh ~/dev/Beautiful-Timetracker-App/implementations/issue_528_plan.md

# Search for key sections
grep -i "user story" ~/dev/.../implementations/issue_528_plan.md
grep -i "technical plan" ~/dev/.../implementations/issue_528_plan.md
```

## Expected Output Size

- **Good output:** 2-10 KB (2000-10000 characters)
- **Minimal output:** < 1 KB (< 1000 characters) - indicates problem
- **Excellent output:** 10+ KB with detailed plans and code

## Fixing Issue #528

To get better output for issue #528:

1. **Check if it was processed correctly:**
   ```bash
   cat ~/dev/Beautiful-Timetracker-App/implementations/issue_528_plan.md
   ```

2. **Re-run with verbose output:**
   ```bash
   python3 scripts/automated_crew.py owner/repo 1 528
   ```

3. **Monitor terminal for errors:**
   - Watch for LLM errors
   - Check for timeouts
   - Verify all agents completed

4. **Check the new output file:**
   - Should have metadata section
   - Should show output length
   - Should include all task outputs

## Contact & Support

If outputs remain minimal after these steps:

1. Check CrewAI version compatibility
2. Verify LLM provider (Ollama/OpenAI) is working
3. Review issue complexity
4. Check system resources (memory, CPU)

---

**Last Updated:** January 2025
