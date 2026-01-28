#!/bin/bash
# Script to merge all feature branches into develop

set -e

REPO_DIR="${1:-$HOME/dev/Beautiful-Timetracker-App}"

if [ ! -d "$REPO_DIR/.git" ]; then
    echo "❌ Error: $REPO_DIR is not a git repository"
    exit 1
fi

cd "$REPO_DIR"

echo "📋 Git Status:"
echo "=============="
git status --short
echo ""

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "🌿 Current branch: $CURRENT_BRANCH"
echo ""

# Fetch latest from remote
echo "⬇️  Fetching latest from remote..."
git fetch origin || echo "⚠️  Could not fetch (may not have remote configured)"
echo ""

# Get all feature branches
echo "🔍 Finding feature branches..."
FEATURE_BRANCHES=$(git branch -a | grep -E 'feature/|remotes/origin/feature/' | sed 's/^[* ] //' | sed 's/remotes\/origin\///' | sort -u | grep -v 'HEAD' || true)

if [ -z "$FEATURE_BRANCHES" ]; then
    echo "ℹ️  No feature branches found"
    exit 0
fi

echo "Found feature branches:"
echo "$FEATURE_BRANCHES" | while read branch; do
    echo "  - $branch"
done
echo ""

# Switch to develop
echo "🔄 Switching to develop branch..."
if git show-ref --verify --quiet refs/heads/develop; then
    git checkout develop
else
    echo "⚠️  Develop branch doesn't exist locally. Creating it..."
    if git show-ref --verify --quiet refs/remotes/origin/develop; then
        git checkout -b develop origin/develop
    else
        git checkout -b develop
    fi
fi

# Pull latest develop
echo ""
echo "⬇️  Pulling latest develop..."
git pull origin develop || {
    echo "⚠️  Could not pull develop (may not exist on remote or no remote configured)"
}

# Merge each feature branch
echo ""
echo "🔀 Merging feature branches into develop..."
echo "=========================================="

MERGED_COUNT=0
FAILED_COUNT=0
FAILED_BRANCHES=()

for branch in $FEATURE_BRANCHES; do
    # Skip if it's the current branch or develop
    if [ "$branch" = "develop" ] || [ "$branch" = "$CURRENT_BRANCHES" ]; then
        continue
    fi
    
    # Check if branch exists locally, if not try to checkout from remote
    if ! git show-ref --verify --quiet refs/heads/"$branch"; then
        if git show-ref --verify --quiet refs/remotes/origin/"$branch"; then
            echo "📥 Checking out $branch from remote..."
            git checkout -b "$branch" "origin/$branch" || {
                echo "⚠️  Could not checkout $branch, skipping..."
                FAILED_COUNT=$((FAILED_COUNT + 1))
                FAILED_BRANCHES+=("$branch")
                continue
            }
        else
            echo "⚠️  Branch $branch not found locally or remotely, skipping..."
            FAILED_COUNT=$((FAILED_COUNT + 1))
            FAILED_BRANCHES+=("$branch")
            continue
        fi
    fi
    
    # Switch back to develop
    git checkout develop
    
    echo ""
    echo "🔀 Merging $branch into develop..."
    
    # Check if already merged
    if git merge-base --is-ancestor "$branch" develop 2>/dev/null; then
        echo "✅ $branch is already merged into develop (skipping)"
        MERGED_COUNT=$((MERGED_COUNT + 1))
        continue
    fi
    
    # Try to merge
    if git merge "$branch" --no-edit; then
        echo "✅ Successfully merged $branch"
        MERGED_COUNT=$((MERGED_COUNT + 1))
    else
        echo "❌ Failed to merge $branch (conflicts or errors)"
        echo "   Resolve conflicts manually and run: git merge --continue"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        FAILED_BRANCHES+=("$branch")
        
        # Ask if user wants to continue
        read -p "Continue with next branch? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Stopping merge process..."
            break
        fi
    fi
done

# Summary
echo ""
echo "=========================================="
echo "📊 Merge Summary:"
echo "=========================================="
echo "✅ Successfully merged: $MERGED_COUNT branch(es)"
echo "❌ Failed: $FAILED_COUNT branch(es)"

if [ ${#FAILED_BRANCHES[@]} -gt 0 ]; then
    echo ""
    echo "Failed branches:"
    for branch in "${FAILED_BRANCHES[@]}"; do
        echo "  - $branch"
    done
    echo ""
    echo "To resolve conflicts manually:"
    echo "  1. git status  # See conflicted files"
    echo "  2. Resolve conflicts in files"
    echo "  3. git add <resolved-files>"
    echo "  4. git merge --continue"
fi

# Show current status
echo ""
echo "📋 Current status:"
git status --short

# Ask if user wants to push
echo ""
read -p "Push develop to remote? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⬆️  Pushing develop to remote..."
    git push origin develop || {
        echo "⚠️  Could not push. You may need to:"
        echo "   git push -u origin develop"
    }
    echo "✅ Done!"
else
    echo "ℹ️  Skipping push. To push manually:"
    echo "   git push origin develop"
fi
