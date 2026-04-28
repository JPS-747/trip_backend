# Git Push Script
# This script will add all changes, commit with a message, and push to the current branch.

# Usage: powershell ./git-push.ps1 "Your commit message"

param(
    [string]$Message = "Update"
)

git add .
git commit -m "$Message"
git push
