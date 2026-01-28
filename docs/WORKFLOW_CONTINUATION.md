# How the Workflow Continues Automatically

## 🔄 Automated Workflow Continuation

Your CrewAI team is designed to **automatically continue** processing issues one after another. Here's how it works:

## 📋 Workflow Steps

### Step 1: Issue Execution
When you click "Execute #608" (or any issue):
1. CrewAI crew processes the issue through 4 agents:
   - Product Manager → User story
   - Architect → Technical plan
   - Developer → Diff patch
   - Reviewer → Quality check

### Step 2: Automatic Continuation
After execution completes:
- ✅ Issue is marked as processed
- ✅ Implementation plan saved
- ✅ System automatically identifies next unprocessed issue
- ✅ Ready to process next issue

### Step 3: Batch Processing
You can enable **automatic batch processing**:

**Option A: Use Automated Dashboard**
```bash
streamlit run ~/ai-dev-team/dashboard_automated.py --server.port=8001
```

Click **"🔄 Process All Remaining"** - the crew will:
1. Process issue #608
2. Automatically move to next unprocessed issue
3. Process that issue
4. Continue until all issues are done

**Option B: Command Line Batch**
```bash
cd ~/ai-dev-team
source .venv/bin/activate
python3 automated_crew.py NeotronProductions/Beautiful-Timetracker-App 10
```
This processes 10 issues automatically, one after another.

## 🎯 Current Workflow (Manual)

Right now, the dashboard shows:
- ✅ Issue #608 executed
- ✅ Output shown
- ⏭️ **You click "Continue to Next Issue"** to proceed

## 🚀 Enhanced Workflow (Automated)

To enable **fully automated** continuation:

### 1. Switch to Automated Dashboard

Update your dashboard service:
```bash
cd ~/ai-dev-team

# Update start script
cat > start_dashboard.sh << 'EOF'
#!/bin/bash
cd "$HOME/ai-dev-team"
source .venv/bin/activate
export PORT=${PORT:-8001}
streamlit run dashboard_automated.py --server.port=$PORT --server.address=0.0.0.0
EOF

# Restart service
sudo systemctl restart pi-crewai-dashboard
```

### 2. Use Automated Features

The automated dashboard provides:
- **"Process This Issue"** - Process current issue
- **"Process All Remaining"** - Automatically process ALL unprocessed issues
- **Progress tracking** - See which issues are done
- **Auto-continuation** - Moves to next issue automatically

## 📊 Workflow States

### Issue States:
- ⏳ **Unprocessed** - Not yet worked on
- 🔄 **Processing** - Currently being worked on by crew
- ✅ **Processed** - Completed, plan saved

### Automatic Flow:
```
Issue #608 (Unprocessed)
    ↓ [Execute]
Issue #608 (Processing)
    ↓ [Crew completes]
Issue #608 (Processed) → Next Issue (Unprocessed)
    ↓ [Auto-continue]
Next Issue (Processing)
    ↓ [Repeat]
```

## 🔧 How to Enable Auto-Continue

### Method 1: Dashboard Button
After execution, click **"⏭️ Continue to Next Issue"**

### Method 2: Batch Mode
Use the automated dashboard and click **"🔄 Process All Remaining"**

### Method 3: Script Mode
```bash
# Process 5 issues automatically
python3 automated_crew.py NeotronProductions/Beautiful-Timetracker-App 5
```

## 💡 What Happens Automatically

1. **Issue Selection**: System finds next unprocessed issue
2. **Crew Execution**: All 4 agents work on it
3. **Result Saving**: Plan saved to `implementations/issue_XXX_plan.md`
4. **Progress Tracking**: Issue marked in `processed_issues.json`
5. **Next Issue**: Automatically moves to next unprocessed issue
6. **Repeat**: Continues until all issues processed

## 🎯 Next Steps for You

**To enable full automation:**

1. **Switch to automated dashboard:**
   ```bash
   # Update and restart
   cd ~/ai-dev-team
   # Edit start_dashboard.sh to use dashboard_automated.py
   sudo systemctl restart pi-crewai-dashboard
   ```

2. **Or use command line:**
   ```bash
   python3 automated_crew.py NeotronProductions/Beautiful-Timetracker-App 10
   ```

3. **Monitor progress:**
   - Check `processed_issues.json` for completed issues
   - View `implementations/` folder for saved plans
   - Dashboard shows remaining issues

The workflow **automatically continues** - you just need to enable batch processing mode!
