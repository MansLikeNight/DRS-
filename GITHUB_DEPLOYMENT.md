# GitHub Deployment Guide

This guide will walk you through deploying the Daily Drill Report System to GitHub.

## Prerequisites

- Git installed on your machine
- GitHub account
- Remote repository created: https://github.com/MansLikeNight/DRS-.git

## Step-by-Step Deployment

### 1. Initialize Git Repository

```powershell
# Navigate to your project directory (if not already there)
cd C:\Users\PC\DailyDrillReport

# Initialize Git repository
git init

# Check status
git status
```

### 2. Configure Git (First Time Only)

```powershell
# Set your name and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify configuration
git config --list
```

### 3. Stage All Files

```powershell
# Add all files to staging
git add .

# Verify what will be committed
git status
```

### 4. Create Initial Commit

```powershell
# Commit with descriptive message
git commit -m "Initial commit: Complete Daily Drill Report System v1.0

- Core shift management with day/night tracking
- Multi-user approval workflow (Supervisor → Manager → Client)
- Real-time drilling progress tracking with core tray images
- Activity logging and material consumption tracking
- 24-hour combined view for day/night shifts
- BOQ generation (daily/monthly)
- Export capabilities (PDF, Excel, CSV)
- Interactive activity breakdown charts
- Role-based access control
- Complete test suite and documentation
- Production-ready configuration"
```

### 5. Add Remote Repository

```powershell
# Add GitHub remote
git remote add origin https://github.com/MansLikeNight/DRS-.git

# Verify remote
git remote -v
```

### 6. Push to GitHub

```powershell
# Push to main branch
git push -u origin main

# If you get an error about 'master' vs 'main', rename the branch:
git branch -M main
git push -u origin main
```

### 7. Verify Deployment

1. Visit: https://github.com/MansLikeNight/DRS-
2. Check that all files are present
3. Verify README displays correctly
4. Check that `.gitignore` is working (no `.env`, `db.sqlite3`, or `__pycache__`)

## Common Issues & Solutions

### Issue 1: Authentication Failed

**Solution**: Use Personal Access Token (PAT)

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Use token as password when prompted

Or configure Git credential manager:
```powershell
git config --global credential.helper manager
```

### Issue 2: Branch Already Exists

```powershell
# Force push (use with caution on first deploy)
git push -u origin main --force
```

### Issue 3: Large Files Rejected

If you have large files (>100MB):
```powershell
# Install Git LFS
git lfs install

# Track large file types
git lfs track "*.psd"
git lfs track "*.zip"

# Add .gitattributes
git add .gitattributes
git commit -m "Add: Git LFS configuration"
git push
```

### Issue 4: Sensitive Data in Commit History

**Prevention**: Always check `.gitignore` before first commit

**If already committed**:
```powershell
# Remove file from Git but keep locally
git rm --cached .env
git rm --cached db.sqlite3

# Commit removal
git commit -m "Remove: Sensitive files from repository"
git push
```

## GitHub Repository Configuration

### 1. Set Repository Description

Navigate to repository → Settings → General:
- **Description**: "Django-based web application for managing drilling operations, progress reporting, and BOQ generation"
- **Website**: Your production URL (if deployed)
- **Topics**: `django`, `python`, `drilling`, `reporting`, `boq`, `data-management`

### 2. Configure Branch Protection (Optional)

Settings → Branches → Add rule:
- Branch name pattern: `main`
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass
- ✅ Require branches to be up to date

### 3. Enable GitHub Pages (Optional)

For hosting documentation:
- Settings → Pages → Source: `main` branch, `/docs` folder
- Add documentation to `docs/` directory

### 4. Set Up GitHub Actions (Optional)

Create `.github/workflows/django-tests.yml`:

```yaml
name: Django CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      env:
        SECRET_KEY: test-secret-key-for-ci
        DEBUG: False
      run: |
        python manage.py test
```

## Future Updates

### Making Changes

```powershell
# 1. Make your code changes

# 2. Check what changed
git status
git diff

# 3. Stage changes
git add .

# 4. Commit with descriptive message
git commit -m "Add: Feature description"

# 5. Push to GitHub
git push
```

### Creating Releases

```powershell
# Tag a version
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Create release on GitHub
# Go to repository → Releases → Draft a new release
# Select tag, add release notes, attach binaries if needed
```

### Working with Branches

```powershell
# Create feature branch
git checkout -b feature/new-feature

# Work on feature, commit changes
git add .
git commit -m "Add: New feature"

# Push feature branch
git push -u origin feature/new-feature

# Create Pull Request on GitHub
# After review and merge, update local main
git checkout main
git pull
```

## Post-Deployment Checklist

- [ ] Repository is public/private as intended
- [ ] README displays correctly with badges
- [ ] LICENSE file is present
- [ ] `.gitignore` is working (no sensitive files pushed)
- [ ] All documentation files are present
- [ ] Repository description and topics are set
- [ ] Branch protection rules configured (if desired)
- [ ] GitHub Actions CI/CD setup (if desired)
- [ ] Collaborators invited (if working in a team)

## Backup Strategy

Even with GitHub, maintain local backups:

```powershell
# Clone to external drive periodically
git clone https://github.com/MansLikeNight/DRS-.git D:\Backups\DRS-backup

# Or create bundle
git bundle create DRS-backup.bundle --all
```

## Next Steps

1. **Deploy to Production**: See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
2. **Set Up CI/CD**: Automate testing and deployment
3. **Monitor Issues**: Respond to community issues and PRs
4. **Release Management**: Create versioned releases for major updates

---

**Congratulations!** 🎉 Your Daily Drill Report System is now on GitHub!

Repository URL: https://github.com/MansLikeNight/DRS-.git
