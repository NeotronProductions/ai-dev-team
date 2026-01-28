#!/bin/bash
# Script to commit current changes and merge into develop branch

set -e

REPO_DIR="${1:-$HOME/dev/Beautiful-Timetracker-App}"

if [ ! -d "$REPO_DIR/.git" ]; then
    echo "❌ Error: $REPO_DIR is not a git repository"
    exit 1
fi

cd "$REPO_DIR"

echo "📋 Current Status:"
echo "=================="
git status --short

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo ""
echo "🌿 Current branch: $CURRENT_BRANCH"

# Check if there are changes to commit
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No changes to commit"
else
    echo ""
    echo "📝 Staging all changes..."
    git add .
    
    echo "💾 Committing changes..."
    git commit -m "chore: update implementation files and patches" || {
        echo "⚠️  Commit failed or no changes to commit"
    }
fi

# Switch to develop branch
echo ""
echo "🔄 Switching to develop branch..."
git checkout develop || {
    echo "⚠️  Could not switch to develop. Creating it..."
    git checkout -b develop
}

# Pull latest develop
echo ""
echo "⬇️  Pulling latest develop..."
git pull origin develop || {
    echo "⚠️  Could not pull develop (may not exist on remote)"
}

# Merge current branch into develop
if [ "$CURRENT_BRANCH" != "develop" ]; then
    echo ""
    echo "🔀 Merging $CURRENT_BRANCH into develop..."
    git merge "$CURRENT_BRANCH" --no-edit || {
        echo "❌ Merge failed. Please resolve conflicts manually."
        exit 1
    }
    echo "✅ Merge successful"
else
    echo "ℹ️  Already on develop branch"
fi

# Push to remote
echo ""
echo "⬆️  Pushing to remote..."
git push origin develop || {
    echo "⚠️  Could not push to remote. You may need to:"
    echo "   git push -u origin develop"
}

echo ""
echo "✅ Done! Changes committed and merged into develop"
