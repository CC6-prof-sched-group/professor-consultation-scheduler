# Team Git Workflow Guide

This guide ensures smooth collaboration on the Professor Consultation Scheduler project by establishing a clear branching strategy and workflow. Following this process helps us avoid merge conflicts and maintain a clean, organized codebase.

---

## Overview

![work-flow-picture](img/work-flow-picture.png)

### Branch Strategy

We use a **3-tier branching model** to manage development, testing, and production:

**main** = The Production. Stable, tested code ready for deployment 


**dev** =  The Integration & Testing. Consolidates all features for testing before release 


**feature/\*** = The Feature Development. Individual branches for specific features or tasks 

---

## Getting Started

### 1. Create Your Feature Branch

Start by creating a new branch for your feature or task:

```bash
git checkout -b yourname/<feature-name>
```

**Branch Naming Convention:**
- Use lowercase with hyphens: `von/user-authentication`, `von/booking-system`
- Be descriptive but concise

### 2. Work on Your Feature

Make your changes and commit regularly:

```bash
git add .
git commit -m "descriptive commit message"
```

### 3. Push Your Branch

Push your feature branch to the remote repository:

```bash
git push -u origin name/<feature-name>
```

---

## Preparing for Merge

### Step 1: Sync with Latest Dev Branch

Before merging, ensure your branch has the latest changes from `dev`:

```bash
git checkout name/<feature-name>
git fetch origin
git merge origin/dev
```

**Why this matters:** This allows you to resolve any merge conflicts in your own branch before submitting a pull request to `dev`. This keeps the `dev` branch clean and prevents integration issues.

### Step 2: Resolve Conflicts (if any)

If conflicts occur during the merge:
1. Open the conflicted files
2. Resolve conflicts by choosing the correct version of the code
3. Commit the merge: `git commit -m "Merge dev into feature/<feature-name>"`
4. Continue with the push

### Step 3: Push to Remote

After syncing with `dev`, push your updated branch:

```bash
git push origin name/<feature-name>
```

---

## Creating a Pull Request (PR)

1. Go to the GitHub repository
2. Click **"New Pull Request"**
3. Set the base branch as **`dev`** (not main!)
4. Set the compare branch as **your feature branch**
5. Fill in the PR title and description
6. Request a code review from team members
7. Wait for approval before merging

---

## Merging to Dev and Main

### Merging to Dev (Regular Development)
- Feature branches are merged into `dev` via PR
- This allows team testing before production release
- Multiple features can be integrated and tested together

### Merging to Main (Production Release)
1. Thoroughly test the `dev` branch
2. Create a PR from `dev` to `main`
3. Get team lead approval
4. Merge to `main` only when confident the release is stable

---

## Quick Reference

### Common Commands

```bash
# Check current branch
git branch

# List all branches (local and remote)
git branch -a

# Switch to a branch
git checkout <branch-name>

# Update your local branch with remote changes
git fetch origin
git pull origin <branch-name>

# View commit history
git log --oneline

# Undo last commit (before pushing)
git reset --soft HEAD~1
```

### Emergency: Undo Recent Push

If you accidentally pushed something wrong:

```bash
git revert <commit-hash>
git push origin name/<feature-name>
```

---

## Best Practices

**Do:**
- Create a new branch for each feature/task
- Commit frequently with meaningful messages
- Sync with `dev` before creating a PR
- Test your code before submitting a PR
- Keep commits focused and logical
- Use descriptive PR titles and descriptions

**Don't:**
- Push directly to `main` or `dev` (use PRs)
- Mix multiple features in one branch
- Commit with vague messages like "fix" or "update"
- Ignore merge conflicts
- Force push to shared branches
