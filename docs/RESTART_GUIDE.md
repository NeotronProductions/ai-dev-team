# Restart Guide: When Do You Need to Restart?

## ✅ No Restart Needed!

**The pipeline automation works immediately** - no restart required!

### Why?

1. **`automated_crew.py`** loads `.env` file every time it runs
2. **Pipeline functions** are part of the script (not a service)
3. **Changes take effect** on the next execution

## 🚀 How to Use

### Run the crew (works immediately):

```bash
cd ~/ai-dev-team
source .venv/bin/activate

# Process an issue - pipeline automation works!
python3 automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 724
```

The issue will automatically:
- Move to "In Progress" when processing starts
- Move to "Done" when processing completes

## ⚙️ Optional: Restart Dashboard

**Only needed if:**
- You're using the dashboard to trigger executions
- You want to see pipeline status in the dashboard

```bash
sudo systemctl restart pi-crewai-dashboard
```

## 📝 Configuration Changes

If you modify `.env` file:
- ✅ `automated_crew.py` - Picks up changes immediately (no restart)
- ⚠️ Dashboard service - May need restart to see new env vars

## 🎯 Quick Test

To verify pipeline automation works:

```bash
cd ~/ai-dev-team
source .venv/bin/activate

# Process an issue and watch it move in your project board
python3 automated_crew.py NeotronProductions/Beautiful-Timetracker-App 1 724
```

Check your GitHub project board - the issue should move automatically!

## ✅ Summary

**No restart needed!** Just run the script and it works. 🎉
