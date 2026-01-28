# Where to Clone the Repository

## 🎯 Recommended Location

**Best option:** Create a `projects` directory in your home folder

```bash
# Create projects directory (if it doesn't exist)
mkdir -p ~/projects

# Clone the repository
cd ~/projects
git clone https://github.com/NeotronProductions/Beautiful-Timetracker-App.git
cd Beautiful-Timetracker-App

# Create your feature branch
git checkout -b feature/US-011-filter-sessions-by-project
```

## 📁 Alternative Locations

### Option 1: In your home directory (simple)
```bash
cd ~
git clone https://github.com/NeotronProductions/Beautiful-Timetracker-App.git
cd Beautiful-Timetracker-App
```

### Option 2: With your dev tools (if you have a dev folder)
```bash
mkdir -p ~/dev
cd ~/dev
git clone https://github.com/NeotronProductions/Beautiful-Timetracker-App.git
cd Beautiful-Timetracker-App
```

### Option 3: Next to your CrewAI setup
```bash
cd ~/ai-dev-team
git clone https://github.com/NeotronProductions/Beautiful-Timetracker-App.git
cd Beautiful-Timetracker-App
```

## ✅ Recommended Structure

```
~/projects/
  ├── Beautiful-Timetracker-App/     # Your project
  └── ...other projects...

~/ai-dev-team/                       # Your CrewAI tools
  ├── github_working.py
  ├── IMPLEMENTATION_PLAN_593.md
  └── ...
```

## 🚀 Quick Setup Command

```bash
# One-liner to create projects dir and clone
mkdir -p ~/projects && cd ~/projects && git clone https://github.com/NeotronProductions/Beautiful-Timetracker-App.git && cd Beautiful-Timetracker-App && echo "✓ Repository cloned to: $(pwd)"
```

## 💡 Why ~/projects?

- Keeps all your projects organized in one place
- Easy to find and navigate
- Standard practice for developers
- Separates projects from tools/configs
