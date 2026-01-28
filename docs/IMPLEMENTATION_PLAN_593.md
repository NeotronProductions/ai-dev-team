# Implementation Plan: Issue #593 - Filter Sessions by Project

## 📋 Issue Summary
**US-011: Filter Sessions by Project**

As a user, I want to filter the session history to show only sessions for selected project(s), so that I can focus on specific project activities and analyze time spent on individual projects.

**Estimate:** 3.5 hours  
**Labels:** Epic 3: Session History, Sprint 2 (Balanced)

## ✅ Acceptance Criteria
- [ ] Filter dropdown with all projects
- [ ] "All Projects" option available
- [ ] Multi-select capability
- [ ] Filter persists during session
- [ ] Performant filtering
- [ ] Clear filter button visible
- [ ] URL state optional

## 🚀 Step-by-Step Implementation

### Step 1: Setup Repository
```bash
# Clone the repository (if not already cloned)
git clone https://github.com/NeotronProductions/Beautiful-Timetracker-App.git
cd Beautiful-Timetracker-App

# Create feature branch
git checkout -b feature/US-011-filter-sessions-by-project
# or
git checkout -b fix/issue-593
```

### Step 2: Explore Codebase
```bash
# Find session history related files
find . -type f \( -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" \) | grep -i -E "(session|history|filter)" | head -10

# Look for project-related components
find . -type f \( -name "*.tsx" -o -name "*.ts" \) | grep -i project | head -10

# Check for existing filter implementations
grep -r "filter" --include="*.tsx" --include="*.ts" | head -10
```

### Step 3: Identify Components to Modify
Look for:
- Session history component/page
- Project list/data source
- State management (Redux, Context, etc.)
- Routing/URL state handling

### Step 4: Implementation Tasks

#### Task 1: Create Filter Component
- Multi-select dropdown component
- "All Projects" option
- Clear filter button

#### Task 2: Integrate Filter Logic
- Filter sessions based on selected projects
- Handle "All Projects" case
- Ensure performant filtering (consider memoization)

#### Task 3: State Management
- Store filter state (component state or global state)
- Persist during session (localStorage or state management)
- Optional: Sync with URL params

#### Task 4: UI/UX
- Position filter dropdown appropriately
- Show active filter state
- Clear visual indication of filtered results

#### Task 5: Testing
- Manual testing with various project combinations
- Test "All Projects" option
- Test filter persistence
- Test clear filter functionality

### Step 5: Code Structure Example

```typescript
// Example structure (adjust based on your codebase)
interface SessionFilterProps {
  projects: Project[];
  selectedProjects: string[];
  onFilterChange: (projects: string[]) => void;
  onClearFilter: () => void;
}

// Filter component
const SessionFilter: React.FC<SessionFilterProps> = ({
  projects,
  selectedProjects,
  onFilterChange,
  onClearFilter
}) => {
  // Implementation
};

// Usage in session history
const SessionHistory = () => {
  const [filteredProjects, setFilteredProjects] = useState<string[]>([]);
  
  const filteredSessions = useMemo(() => {
    if (filteredProjects.length === 0) return sessions;
    return sessions.filter(session => 
      filteredProjects.includes(session.projectId)
    );
  }, [sessions, filteredProjects]);
  
  // Render with filter
};
```

### Step 6: Testing Checklist
- [ ] Filter by single project
- [ ] Filter by multiple projects
- [ ] "All Projects" shows all sessions
- [ ] Filter persists on page navigation
- [ ] Clear filter resets to show all
- [ ] Performance is acceptable with many sessions
- [ ] URL state works (if implemented)

### Step 7: Commit and Push
```bash
git add .
git commit -m "feat: implement project filter for session history (US-011)

- Add multi-select project filter dropdown
- Implement filter logic with 'All Projects' option
- Add clear filter button
- Persist filter state during session
- Add URL state support (optional)

Closes #593"
git push origin feature/US-011-filter-sessions-by-project
```

### Step 8: Create Pull Request
- Link to issue #593
- Include screenshots/demo
- Reference acceptance criteria
- Note any optional features implemented

## 🔍 Quick Commands

```bash
# Re-analyze the issue
cd ~/ai-dev-team
source .venv/bin/activate
python3 github_working.py NeotronProductions/Beautiful-Timetracker-App 593

# Check related issues
python3 -c "from github import Github; from github.Auth import Token; import os; from dotenv import load_dotenv; load_dotenv(); auth = Token(os.getenv('GITHUB_TOKEN')); g = Github(auth=auth); repo = g.get_repo('NeotronProductions/Beautiful-Timetracker-App'); issues = [i for i in repo.get_issues(state='open', labels=['Epic 3: Session History'])][:5]; [print(f'#{i.number}: {i.title}') for i in issues]"
```

## 📝 Notes
- This is part of Epic 3: Session History
- Estimated 3.5 hours
- Has 5 sub-tasks (check issue for details)
- Manual testing required
