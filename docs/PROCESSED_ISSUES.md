# Processed Issues Behavior

How the AI crew handles issues that have already been processed.

## Quick Answer

- **Batch Mode** (processing multiple issues): **SKIPS** already processed issues
- **Specific Issue Mode** (processing one issue): **OVERRIDES** - will process again even if already done

## How It Works

### Processed Issues Tracking

The script tracks processed issues in:

```
~/ai-dev-team/data/processed_issues.json
```

This file contains a JSON array of issue numbers that have been processed:

```json
[550, 689, 690, 691, 692, ...]
```

### Batch Mode (Multiple Issues)

When you run:

```bash
python3 scripts/automated_crew.py owner/repo 5
```

The script will:
1. Load the list of processed issues from `processed_issues.json`
2. Get all open issues from GitHub
3. **Skip** any issues that are already in the processed list
4. Process only **unprocessed** issues
5. Mark each completed issue as processed

**Example:**
- Issues 550, 689, 690 are already processed
- Issues 691, 692, 693 are new
- Running `python3 scripts/automated_crew.py owner/repo 5` will:
  - Skip 550, 689, 690
  - Process 691, 692, 693 (and more if available)

### Specific Issue Mode (One Issue)

When you run:

```bash
python3 scripts/automated_crew.py owner/repo 1 550
```

The script will:
1. **NOT check** if issue #550 is already processed
2. Process the issue **regardless** of previous processing
3. **Override** any existing output files
4. Mark it as processed again (or add it if not already there)

**This means:**
- Existing output file will be **overwritten**
- Existing git branch/commit will be **replaced** (if branch exists, it may be deleted and recreated)
- The issue will be processed from scratch

## Why This Behavior?

### Batch Mode Skips
- Prevents duplicate work
- Allows you to process new issues without redoing old ones
- Efficient for ongoing automation

### Specific Issue Mode Overrides
- Allows you to **reprocess** an issue if:
  - The previous output was incomplete/incorrect
  - You want to regenerate with different parameters
  - The issue was updated on GitHub
  - You want to test changes to the crew configuration

## Checking Processed Issues

### View Processed Issues List

```bash
cat ~/ai-dev-team/data/processed_issues.json
```

### Check if Specific Issue is Processed

```bash
python3 -c "import json; data=json.load(open('~/ai-dev-team/data/processed_issues.json')); print('550' in [str(x) for x in data])"
```

### Count Processed Issues

```bash
python3 -c "import json; data=json.load(open('~/ai-dev-team/data/processed_issues.json')); print(f'Processed: {len(data)} issues')"
```

## Resetting Processed Issues

### Remove Specific Issue from Processed List

```bash
# Edit the file manually
nano ~/ai-dev-team/data/processed_issues.json

# Or use Python
python3 << EOF
import json
with open('~/ai-dev-team/data/processed_issues.json', 'r') as f:
    data = json.load(f)
data = [x for x in data if x != 550]  # Remove issue 550
with open('~/ai-dev-team/data/processed_issues.json', 'w') as f:
    json.dump(data, f)
print("Removed issue 550 from processed list")
EOF
```

### Clear All Processed Issues

```bash
echo "[]" > ~/ai-dev-team/data/processed_issues.json
```

**Warning:** This will cause the script to try processing all issues again in batch mode.

## Reprocessing an Issue

### Method 1: Use Specific Issue Mode (Recommended)

```bash
# This will override existing processing
python3 scripts/automated_crew.py owner/repo 1 550
```

### Method 2: Remove from Processed List, Then Batch

```bash
# Remove issue from processed list
python3 -c "import json; data=json.load(open('~/ai-dev-team/data/processed_issues.json')); data.remove(550); json.dump(data, open('~/ai-dev-team/data/processed_issues.json', 'w'))"

# Now batch mode will pick it up
python3 scripts/automated_crew.py owner/repo 5
```

## What Gets Overwritten?

When reprocessing an issue, these files/actions may be affected:

1. **Output File:**
   - `~/dev/Beautiful-Timetracker-App/implementations/issue_550_plan.md`
   - Will be **overwritten** with new content

2. **Exported Copy:**
   - `~/ai-dev-team/exports/issue_550_plan.md`
   - Will be **overwritten** with new content

3. **Git Branch:**
   - If branch `feature/issue-550` exists, it may be:
     - Deleted and recreated, OR
     - Switched to and new commits added
   - Check the script's branch handling logic

4. **Git Commit:**
   - New commit will be created
   - Previous commit may remain in history (if branch wasn't deleted)

5. **Pull Request:**
   - If PR already exists, a new commit will be added to it
   - If branch was recreated, a new PR may be created

## Best Practices

### For Production Use

1. **Use batch mode** for regular processing
   - Let it skip already processed issues
   - More efficient and safer

2. **Use specific issue mode** only when:
   - You need to reprocess a specific issue
   - Testing changes to the crew
   - Fixing incomplete outputs

### For Testing

1. **Clear processed list** before testing
   ```bash
   echo "[]" > ~/ai-dev-team/data/processed_issues.json
   ```

2. **Process specific issues** to test changes
   ```bash
   python3 scripts/automated_crew.py owner/repo 1 550
   ```

### For Recovery

If an issue was processed incorrectly:

1. **Check the output file** first:
   ```bash
   cat ~/dev/Beautiful-Timetracker-App/implementations/issue_550_plan.md
   ```

2. **If output is bad**, reprocess:
   ```bash
   python3 scripts/automated_crew.py owner/repo 1 550
   ```

3. **If you want to keep old output**, backup first:
   ```bash
   cp ~/dev/Beautiful-Timetracker-App/implementations/issue_550_plan.md \
      ~/dev/Beautiful-Timetracker-App/implementations/issue_550_plan.md.backup
   ```

## Dashboard Behavior

The **Automated Dashboard** (`dashboard_automated.py`) also uses the processed issues list:

- Shows processed vs unprocessed issues
- Only processes unprocessed issues
- Allows you to skip issues manually
- Saves to the same `processed_issues.json` file

## Summary Table

| Mode | Command | Behavior | Check Processed? |
|------|---------|----------|------------------|
| Batch | `python3 ... owner/repo 5` | **SKIPS** processed | ✅ Yes |
| Specific | `python3 ... owner/repo 1 550` | **OVERRIDES** | ❌ No |

## Related Documentation

- [TERMINAL_COMMANDS.md](TERMINAL_COMMANDS.md) - How to run the crew
- [DIFF_AND_PR_WORKFLOW.md](DIFF_AND_PR_WORKFLOW.md) - How code changes are applied
- [OUTPUT_EXPORT.md](OUTPUT_EXPORT.md) - Where outputs are saved

---

**Last Updated:** January 2025
