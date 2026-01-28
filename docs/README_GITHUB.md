# GitHub Integration with CrewAI

This guide explains how to connect CrewAI to GitHub to execute issues.

## Quick Start

### 1. Setup GitHub Integration

Run the setup script:

```bash
cd ~/ai-dev-team
./setup_github_integration.sh
```

This will:
- Prompt you for a GitHub Personal Access Token
- Configure your repository
- Install optional dependencies

### 2. Manual Setup (Alternative)

Create a `.env` file in `~/ai-dev-team/`:

```bash
cd ~/ai-dev-team
cat > .env << EOF
GITHUB_TOKEN=your_github_personal_access_token_here
GITHUB_REPO=owner/repo
EOF
```

### 3. Get a GitHub Personal Access Token

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click "Generate new token" → "Generate new token (classic)"
3. Name it (e.g., "CrewAI Integration")
4. Select scopes:
   - ✅ `repo` - Full control of private repositories
   - ✅ `read:org` - Read org and team membership
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again!)
7. Add it to your `.env` file

### 4. Execute a GitHub Issue

```bash
cd ~/ai-dev-team
source .venv/bin/activate

# Execute issue #123 from the configured repo
python3 github_crew.py 123

# Or specify a different repo
python3 github_crew.py 123 owner/repo
```

## How It Works

The `github_crew.py` script creates a CrewAI crew with two agents:

1. **GitHub Issue Manager** - Analyzes issues, searches repositories, understands requirements
2. **Code Analyst** - Analyzes code, provides implementation guidance

### Tools Used

- **GithubSearchTool** - Semantic search through GitHub repositories (issues, PRs, code)
- **ComposioTool** (optional) - Advanced GitHub API actions

## Example Workflow

```python
from github_crew import execute_issue

# Execute issue #42 from my-repo
result = execute_issue(42, "myusername/my-repo")
print(result)
```

## Configuration

All configuration is in `~/ai-dev-team/.env`:

```env
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=owner/repo
```

## Advanced Usage

### Custom Agents

You can modify `github_crew.py` to create custom agents for your specific needs:

```python
custom_agent = Agent(
    role='Your Custom Role',
    goal='Your goal',
    backstory='Your backstory',
    tools=setup_github_tools(),
    verbose=True
)
```

### Multiple Repositories

You can work with different repositories by specifying them in the command:

```bash
python3 github_crew.py 123 owner1/repo1
python3 github_crew.py 456 owner2/repo2
```

## Troubleshooting

### "GITHUB_TOKEN not set"
- Make sure you've created a `.env` file with your token
- Or export it: `export GITHUB_TOKEN='your_token'`

### "Repository not found"
- Check that the repository format is correct: `owner/repo`
- Verify your token has access to the repository

### "Rate limit exceeded"
- GitHub API has rate limits
- Wait a bit and try again
- Consider using a token with higher rate limits

## Security Notes

⚠️ **Important**: Never commit your `.env` file to git!

Add to `.gitignore`:
```
.env
*.env
```

## Next Steps

- Customize agents for your specific workflow
- Add more tools (e.g., code generation, testing)
- Integrate with your CI/CD pipeline
- Set up automated issue triage

## Resources

- [CrewAI Documentation](https://docs.crewai.com/)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [CrewAI GitHub Tools](https://docs.crewai.com/en/tools/search-research/githubsearchtool)
