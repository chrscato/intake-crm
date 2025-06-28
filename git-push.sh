#!/bin/bash

# Git Auto Push Script
# This script adds all changes, commits with a custom message, and pushes to origin master

echo "🚀 Git Auto Push Script"
echo "========================"

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository!"
    echo "Please run this script from within a git repository."
    exit 1
fi

# Check if there are any changes to commit
if git diff-index --quiet HEAD --; then
    echo "✅ No changes to commit. Working directory is clean."
    exit 0
fi

echo "📁 Adding all changes..."
git add .

echo ""
echo "💬 Enter your commit message:"
read -r commit_message

# Check if commit message is empty
if [ -z "$commit_message" ]; then
    echo "❌ Error: Commit message cannot be empty!"
    exit 1
fi

echo ""
echo "📝 Committing changes with message: '$commit_message'"
git commit -m "$commit_message"

echo ""
echo "🚀 Pushing to origin master..."
git push origin master

echo ""
echo "✅ Successfully pushed to GitHub!"
echo "📊 Commit: $commit_message" 