# See what will be committed
git status
git diff

# Stage changes (or use git add -p to review hunks)
git add -A

# Commit
git commit -m "chore: add API/validator/tests scaffolding and minor README cleanup"

# Find current branch
git rev-parse --abbrev-ref HEAD

# Push to origin on that branch (replace <branch> if needed)
git push origin <branch>
