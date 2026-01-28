# CrewAI Output Export Guide

Complete guide on where CrewAI saves outputs and how to export them.

## 📁 Where Outputs Are Saved

### Default Location

CrewAI automatically saves all outputs to:

```
~/dev/Beautiful-Timetracker-App/implementations/
```

**Full path:** `/home/hempfinder/dev/Beautiful-Timetracker-App/implementations/`

### Output File Format

Each issue processed creates a markdown file:

```
issue_{issue_number}_plan.md
```

**Example:**
- `issue_542_plan.md` - Output for issue #542
- `issue_550_plan.md` - Output for issue #550

### What's Included in Output Files

Each output file contains:

1. **Full Crew Output**
   - Product Manager's user story
   - Architect's technical plan
   - Developer's implementation
   - Code Reviewer's feedback

2. **Extracted Patch** (if available)
   - Unified diff format
   - Ready to apply with `git apply`

3. **Complete Workflow Results**
   - All agent interactions
   - Decision rationale
   - Implementation details

## 🔍 Finding Your Outputs

### Method 1: Check Default Location

```bash
# List all implementation outputs
ls -lh ~/dev/Beautiful-Timetracker-App/implementations/

# View a specific issue output
cat ~/dev/Beautiful-Timetracker-App/implementations/issue_542_plan.md

# Or use your editor
code ~/dev/Beautiful-Timetracker-App/implementations/issue_542_plan.md
```

### Method 2: Search for Recent Outputs

```bash
# Find all implementation files
find ~/dev -name "issue_*_plan.md" -type f

# Find outputs from today
find ~/dev -name "issue_*_plan.md" -type f -mtime -1
```

### Method 3: Check During Execution

When the crew runs, it prints the output location:

```
✓ Implementation plan saved to: /home/hempfinder/dev/Beautiful-Timetracker-App/implementations/issue_542_plan.md
```

## 📤 Exporting Outputs

### Option 1: Copy to Project Directory

Copy outputs to the ai-dev-team project for easy access:

```bash
# Create exports directory
mkdir -p ~/ai-dev-team/exports

# Copy all implementations
cp -r ~/dev/Beautiful-Timetracker-App/implementations/* ~/ai-dev-team/exports/

# Or copy specific issue
cp ~/dev/Beautiful-Timetracker-App/implementations/issue_542_plan.md ~/ai-dev-team/exports/
```

### Option 2: Export to Custom Location

```bash
# Export to a specific directory
EXPORT_DIR=~/crewai-exports
mkdir -p $EXPORT_DIR
cp ~/dev/Beautiful-Timetracker-App/implementations/* $EXPORT_DIR/
```

### Option 3: Export as JSON

Create a script to export outputs in JSON format:

```bash
#!/bin/bash
# export_outputs.sh

OUTPUT_DIR=~/dev/Beautiful-Timetracker-App/implementations
EXPORT_DIR=~/ai-dev-team/exports
mkdir -p $EXPORT_DIR

for file in $OUTPUT_DIR/issue_*_plan.md; do
    if [ -f "$file" ]; then
        issue_num=$(basename "$file" | sed 's/issue_\([0-9]*\)_plan.md/\1/')
        echo "Exporting issue #$issue_num..."
        cp "$file" "$EXPORT_DIR/"
    fi
done

echo "✓ Exported to $EXPORT_DIR"
```

### Option 4: Export with Metadata

Create a comprehensive export script:

```bash
#!/bin/bash
# export_with_metadata.sh

OUTPUT_DIR=~/dev/Beautiful-Timetracker-App/implementations
EXPORT_DIR=~/ai-dev-team/exports/$(date +%Y-%m-%d)
mkdir -p $EXPORT_DIR

# Copy all files
cp -r $OUTPUT_DIR/* $EXPORT_DIR/

# Create index
cat > $EXPORT_DIR/INDEX.md << EOF
# CrewAI Outputs Export
Date: $(date)
Source: $OUTPUT_DIR

## Exported Files

EOF

for file in $EXPORT_DIR/issue_*_plan.md; do
    if [ -f "$file" ]; then
        issue_num=$(basename "$file" | sed 's/issue_\([0-9]*\)_plan.md/\1/')
        echo "- [Issue #$issue_num]($(basename $file))" >> $EXPORT_DIR/INDEX.md
    fi
done

echo "✓ Exported to $EXPORT_DIR"
echo "✓ Index created at $EXPORT_DIR/INDEX.md"
```

## 🔧 Customizing Output Location

### Change Default Output Directory

Edit `automated_crew.py`:

```python
# Line ~30: Change WORK_DIR
WORK_DIR = Path.home() / "dev" / "Your-Project-Name"

# Or set custom implementations directory
IMPLEMENTATIONS_DIR = Path.home() / "crewai-outputs"
```

### Use Environment Variable

Add to `.env`:

```env
CREWAI_OUTPUT_DIR=~/crewai-outputs
```

Then modify the script to use it:

```python
output_dir = Path(os.getenv("CREWAI_OUTPUT_DIR", str(work_dir / "implementations")))
output_file = output_dir / f"issue_{issue_number}_plan.md"
```

## 📊 Viewing Outputs

### View in Terminal

```bash
# View full output
cat ~/dev/Beautiful-Timetracker-App/implementations/issue_542_plan.md

# View with pagination
less ~/dev/Beautiful-Timetracker-App/implementations/issue_542_plan.md

# Search for specific content
grep -i "user story" ~/dev/Beautiful-Timetracker-App/implementations/issue_542_plan.md
```

### View in Browser

```bash
# Convert markdown to HTML (requires pandoc)
pandoc ~/dev/Beautiful-Timetracker-App/implementations/issue_542_plan.md -o output.html
# Then open in browser
```

### View in VS Code

```bash
code ~/dev/Beautiful-Timetracker-App/implementations/
```

## 📦 Batch Export

### Export All Outputs

```bash
#!/bin/bash
# export_all.sh

SOURCE=~/dev/Beautiful-Timetracker-App/implementations
DEST=~/ai-dev-team/exports/all-$(date +%Y%m%d)

mkdir -p $DEST
cp -r $SOURCE/* $DEST/

echo "✓ Exported $(ls -1 $DEST | wc -l) files to $DEST"
```

### Export with Filtering

```bash
# Export only recent outputs (last 7 days)
find ~/dev/Beautiful-Timetracker-App/implementations -name "*.md" -mtime -7 -exec cp {} ~/ai-dev-team/exports/ \;
```

## 🔄 Automated Export

### Add to Script

You can modify `automated_crew.py` to automatically copy outputs:

```python
def export_output(output_file, export_dir=None):
    """Export output to additional location"""
    if export_dir:
        export_path = Path(export_dir)
        export_path.mkdir(exist_ok=True, parents=True)
        shutil.copy(output_file, export_path / output_file.name)
        print(f"✓ Output also exported to: {export_path / output_file.name}")
```

## 📝 Output File Structure

Each output file contains:

```markdown
# Implementation Plan for Issue #542

## Full Crew Output

[Complete output from all agents]

## Extracted Patch

```diff
[Unified diff if available]
```
```

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| List outputs | `ls ~/dev/Beautiful-Timetracker-App/implementations/` |
| View output | `cat ~/dev/Beautiful-Timetracker-App/implementations/issue_542_plan.md` |
| Copy to project | `cp ~/dev/.../implementations/* ~/ai-dev-team/exports/` |
| Find all outputs | `find ~/dev -name "issue_*_plan.md"` |
| Export recent | `find ~/dev/.../implementations -mtime -1 -exec cp {} ~/exports/ \;` |

## 🔗 Related Documentation

- [TERMINAL_COMMANDS.md](TERMINAL_COMMANDS.md) - How to run the crew
- [DASHBOARD_GUIDE.md](DASHBOARD_GUIDE.md) - Dashboard usage
- [USAGE.md](USAGE.md) - General usage guide

---

**Last Updated:** January 2025
