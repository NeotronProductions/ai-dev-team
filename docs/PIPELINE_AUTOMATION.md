# GitHub Project Pipeline Automation

## ✅ Automatic Issue Movement

Your CrewAI team can now **automatically move issues through your GitHub project pipeline**!

## 🔄 Pipeline Flow

Based on your project board (Todo → In Progress → Being Reviewed → Done):

```
Issue in "Todo"
    ↓ [CrewAI starts processing]
Issue moved to "In Progress"
    ↓ [CrewAI completes]
Issue moved to "Done"
```

## ⚙️ Configuration

Add to your `.env` file:

```bash
cd ~/ai-dev-team

# Enable pipeline movement (default: true)
echo "MOVE_IN_PIPELINE=true" >> .env

# Specify target column when done (default: "Done")
echo "PIPELINE_DONE_COLUMN=Done" >> .env

# Optional: Specify project name (uses first project if not set)
echo "GITHUB_PROJECT_NAME=Beautiful-Timetracker-App" >> .env
```

## 📋 Available Pipeline Stages

Your project has these columns:
- **Todo** - Issues not started (199 items)
- **In Progress** - Actively being worked on
- **Being Reviewed** - Under review
- **Done** - Completed

## 🎯 Current Behavior

**When CrewAI completes an issue:**
1. ✅ Code is written and committed
2. ✅ Branch is created
3. ✅ Issue is moved to "Done" column (if enabled)

## 🔧 Advanced Configuration

### Move to Different Column

You can move to any column by setting `PIPELINE_DONE_COLUMN`:

```bash
# Move to "Being Reviewed" instead
echo "PIPELINE_DONE_COLUMN=Being Reviewed" >> .env

# Move to "In Progress" when starting
# (This would require modifying the code to move at start)
```

### Disable Pipeline Movement

```bash
echo "MOVE_IN_PIPELINE=false" >> .env
```

## 🚀 Complete Workflow

With pipeline automation enabled:

```
1. Issue #724 in "Todo"
    ↓
2. CrewAI starts processing
   → Issue moved to "In Progress" (if configured)
    ↓
3. CrewAI completes:
   - Developer writes code
   - Code applied to repo
   - Branch created and committed
   - PR created (if AUTO_PUSH=true)
    ↓
4. Issue moved to "Done" ✅
```

## 💡 Custom Pipeline Stages

You can customize the workflow by modifying the code to move issues at different stages:

- **Start processing** → Move to "In Progress"
- **Code complete** → Move to "Being Reviewed"  
- **PR created** → Move to "Done"

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MOVE_IN_PIPELINE` | `true` | Enable/disable pipeline movement |
| `PIPELINE_DONE_COLUMN` | `Done` | Column to move to when complete |
| `GITHUB_PROJECT_NAME` | (first project) | Specific project to use |

## ✅ Status

**Pipeline automation is now enabled!** Issues will automatically move to "Done" after CrewAI completes them.
