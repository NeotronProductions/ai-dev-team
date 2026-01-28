# Projects V2 (GraphQL) Pipeline Fix

## ✅ Problem Identified

Your GitHub project uses **Projects V2** (the new GraphQL-based system), not classic projects. The REST API was returning 404 because classic projects API doesn't work with Projects V2.

## 🔧 Solution

The `move_issue_in_project` function needs to:
1. **Try Projects V2 first** using GraphQL API
2. Fall back to classic projects if needed

## 📋 What Needs to Be Fixed

The `automated_crew.py` file was accidentally overwritten. It needs to be restored with:

1. **GraphQL Projects V2 support** - Use GraphQL to:
   - Find projects using `projectsV2` query
   - Get project fields (Status field with options like "Todo", "In Progress", "Done")
   - Update field values to move issues

2. **The `move_issue_in_project_v2` function** - Already written, handles:
   - Finding the Status field
   - Finding the target option (e.g., "In Progress", "Done")
   - Adding issues to project if not present
   - Updating the status field value

## 🚀 Testing

Once the file is restored, test with:

```bash
cd ~/ai-dev-team
source .venv/bin/activate
python3 test_pipeline.py NeotronProductions/Beautiful-Timetracker-App 724
```

## 📝 Next Steps

1. Restore `automated_crew.py` with full functionality
2. Integrate `move_issue_in_project_v2` 
3. Update `move_issue_in_project` to try GraphQL first
4. Test pipeline movement

The project ID is: `PVT_kwHOBp6jps4BMdmH`
Project name: "Beautiful-Timetracker-App"
