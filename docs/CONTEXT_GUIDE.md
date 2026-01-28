# 📋 CrewAI Context Guide

## What Context CrewAI Currently Uses

The `automated_crew.py` script automatically gathers context from your project:

### ✅ Currently Read:
1. **README.md** - Project overview, features, setup instructions
2. **PROJECT_CONTEXT.md** - Detailed tech stack, coding conventions, architecture
3. **package.json** - Dependencies and project metadata (if exists)
4. **requirements.txt** - Python dependencies (if exists)
5. **Project Structure** - File types and directory layout
6. **Sample Code Files** - Main entry points (index.html, key JS/CSS files) for pattern reference
7. **Config Files** - Detects tech stack from config files

## 🎯 What Additional Context Would Help?

### 1. **API Documentation** (if applicable)
If your project uses external APIs or has API endpoints:
- Create `API_DOCS.md` with endpoints, request/response formats
- Include authentication methods
- Example requests/responses

### 2. **Design System / UI Guidelines**
If you have specific design requirements:
- Create `DESIGN_GUIDELINES.md`
- Include color palette, typography, spacing
- Component patterns, interaction patterns
- Accessibility requirements

### 3. **Testing Patterns**
If you want consistent testing:
- Create `TESTING.md` or `TEST_PATTERNS.md`
- Example test cases
- Testing framework preferences
- Coverage expectations

### 4. **Architecture Decisions**
If you have specific architectural choices:
- Create `ARCHITECTURE.md`
- Explain why certain patterns are used
- Module boundaries and responsibilities
- Data flow diagrams

### 5. **Common Patterns / Templates**
If you have reusable code patterns:
- Create `PATTERNS.md` or `TEMPLATES.md`
- Common function signatures
- Error handling patterns
- State management patterns

### 6. **Known Issues / Constraints**
If there are specific limitations:
- Create `CONSTRAINTS.md`
- Browser compatibility requirements
- Performance constraints
- Security considerations

### 7. **Examples of Similar Features**
If you want new features to match existing ones:
- Reference existing implementations in comments
- Include links to similar issues/PRs
- Show before/after examples

## 📝 For Your Vanilla JS Project

Based on your current setup, you already have:
- ✅ **README.md** - Good overview
- ✅ **PROJECT_CONTEXT.md** - Excellent detailed context
- ✅ **SERVER_SETUP.md** - Server configuration

### What You Could Add:

1. **CODE_EXAMPLES.md** (Optional)
   - Show examples of how you want code structured
   - Common patterns you prefer
   - Anti-patterns to avoid

2. **FEATURE_SPECS.md** (Optional)
   - Detailed specifications for complex features
   - User flow diagrams
   - Edge cases to handle

3. **STYLING_GUIDE.md** (Optional)
   - CSS naming conventions (BEM, etc.)
   - Color variables and usage
   - Animation guidelines
   - Responsive breakpoints

## 🔍 How Context is Used

The context is passed to:
1. **Architect Agent** - Uses it to create technical plans
2. **Developer Agent** - Uses it to write code matching your conventions
3. **Reviewer Agent** - Uses it to verify code matches standards

## 💡 Best Practices

1. **Keep it Updated** - Update context files as your project evolves
2. **Be Specific** - Include code examples, not just descriptions
3. **Show, Don't Tell** - Include actual code snippets
4. **Keep it Relevant** - Focus on what affects code generation
5. **Use Examples** - Show good and bad examples

## 🚀 Quick Checklist

For a vanilla JS project like yours, you have:
- ✅ README.md
- ✅ PROJECT_CONTEXT.md
- ✅ Code structure (will be read automatically)

Optional additions:
- ⬜ CODE_EXAMPLES.md (if you want specific patterns)
- ⬜ STYLING_GUIDE.md (if you have strict CSS rules)
- ⬜ FEATURE_SPECS.md (for complex features)

## 📌 Current Status

Your project context is **already well-configured**! The `PROJECT_CONTEXT.md` file you have contains:
- Tech stack details
- Coding conventions
- Project structure
- Design philosophy
- Code examples

This should be sufficient for CrewAI to generate code that matches your project style.

## 🎯 Recommendation

**You're good to go!** Your current context files are comprehensive. Only add more if:
- You notice CrewAI making style mistakes
- You have very specific requirements not covered
- You want to enforce particular patterns

The system will automatically read your existing code files as examples, so as you build the project, CrewAI will learn from your patterns.
