# Automated Crew Workflow

## 🚀 How Your Crew Continues to Next Steps

Your CrewAI team now has **automated workflow capabilities** that allow it to:

### 1. **Sequential Issue Processing**
- Automatically picks the next unprocessed issue
- Processes it through the full crew workflow
- Moves to the next issue automatically

### 2. **Three-Agent Workflow**

**Issue Analyst** → **Code Implementer** → **Code Reviewer**

1. **Analyst** analyzes the issue and creates implementation plan
2. **Implementer** writes the actual code changes
3. **Reviewer** checks quality and completeness

### 3. **Automated Actions**

The crew can:
- ✅ Analyze issues automatically
- ✅ Generate implementation plans
- ✅ Create code changes
- ✅ Review implementations
- ✅ Create git branches
- ✅ Commit changes
- ✅ Track processed issues

## 📋 Usage

### Option 1: Automated Dashboard

```bash
# Use the enhanced dashboard
streamlit run ~/ai-dev-team/dashboard_automated.py --server.port=8001
```

Features:
- Load all issues from a repository
- See which issues are processed/unprocessed
- Click "Process This Issue" to run the crew
- Click "Process All Remaining" for batch processing
- View processing status in real-time

### Option 2: Command Line

```bash
cd ~/ai-dev-team
source .venv/bin/activate

# Process one issue
python3 automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1

# Process multiple issues
python3 automated_crew.py NeotronProductions/Beautiful-Timetracker-App 5
```

## 🔄 Workflow Steps

1. **Load Issues** → Dashboard fetches all open issues
2. **Select Issue** → Crew picks next unprocessed issue
3. **Analyze** → Analyst creates implementation plan
4. **Implement** → Implementer writes code
5. **Review** → Reviewer checks quality
6. **Save** → Plan saved to `implementations/issue_XXX_plan.md`
7. **Commit** → Creates branch and commits (if git repo)
8. **Mark Processed** → Issue marked as done
9. **Next Issue** → Automatically moves to next unprocessed issue

## 📁 Output Files

- `processed_issues.json` - Tracks which issues have been processed
- `implementations/issue_XXX_plan.md` - Implementation plans for each issue

## 🎯 Next Steps for Your Crew

1. **Start the automated dashboard:**
   ```bash
   streamlit run ~/ai-dev-team/dashboard_automated.py --server.port=8001
   ```

2. **Load your repository issues**

3. **Click "Process All Remaining"** to let the crew work through all issues automatically

4. **Monitor progress** in the dashboard

The crew will automatically:
- Pick the next issue
- Process it through all agents
- Save the implementation
- Move to the next issue
- Continue until all issues are processed

## 💡 Tips

- The crew tracks processed issues, so you can stop and resume
- Implementation plans are saved for review
- You can skip issues if needed
- The crew creates git branches for each issue
