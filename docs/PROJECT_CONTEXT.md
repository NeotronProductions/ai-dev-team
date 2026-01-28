# Project Context for CrewAI Agents

## ✅ What Was Added

The script now **automatically gathers project context** and provides it to all agents. This helps them:

1. **Understand the tech stack** (JavaScript, Python, TypeScript, etc.)
2. **Know project structure** (directories, file types)
3. **Follow coding conventions** (from README, config files)
4. **Use correct dependencies** (from package.json, requirements.txt)

## 🔍 What Gets Detected

The `get_project_context()` function automatically detects:

### 1. **Project Documentation**
- README.md content (first 2000 chars)
- Project description and setup instructions

### 2. **Tech Stack Detection**
- **JavaScript/Node.js**: package.json (dependencies, devDependencies)
- **Python**: requirements.txt
- **TypeScript**: tsconfig.json
- **Build Tools**: webpack.config.js, vite.config.js
- **Frameworks**: next.config.js (Next.js), vue.config.js (Vue), angular.json (Angular)
- **Other**: Cargo.toml (Rust), go.mod (Go), pom.xml (Java), etc.

### 3. **Project Structure**
- File types in the project (.js, .ts, .py, .html, etc.)
- Key directories (src, lib, app, components, public, tests, etc.)

## 📋 How It Works

When processing an issue, the script:

1. **Gathers context** from project files
2. **Provides it to Architect** - for technical planning
3. **Provides it to Developer** - for code implementation
4. **Helps agents** understand the project better

## 🎯 Example Context Output

For a JavaScript project with package.json:

```
## Tech Stack (from package.json)
- **Project Name**: Beautiful-Timetracker-App
- **Description**: Time tracking application
- **Dependencies**: react, express, axios
- **Dev Dependencies**: jest, webpack, eslint

## Project Structure
- **File types found**: .js, .json, .html, .css
- **Key directories**: src, public, tests
```

## 💡 For Fresh Projects

If your project is fresh/minimal:

1. **Add a README.md** with:
   - Project description
   - Tech stack
   - Setup instructions
   - Coding conventions

2. **Add package.json** (for JS projects) or **requirements.txt** (for Python):
   - Lists dependencies
   - Shows tech stack

3. **Create a PROJECT_CONTEXT.md** file (optional):
   - Detailed project description
   - Architecture overview
   - Coding standards
   - The script will read this if you add it

## 🚀 Benefits

**Before (without context):**
- Agents guess the tech stack
- May use wrong frameworks/libraries
- Don't know project structure

**Now (with context):**
- ✅ Agents know the tech stack
- ✅ Use correct dependencies
- ✅ Follow project structure
- ✅ Match coding conventions
- ✅ Produce more accurate code

## 📝 Custom Context File

You can also create a `PROJECT_CONTEXT.md` file in your repo root with:

```markdown
# Project Context

## Tech Stack
- Frontend: Vanilla JavaScript
- Backend: Node.js/Express
- Database: SQLite
- Testing: Jest

## Project Structure
- `/src` - Source code
- `/public` - Static assets
- `/tests` - Test files

## Coding Conventions
- Use ES6+ features
- Follow Airbnb style guide
- Write tests for all features
```

The script will automatically include this in the context!
