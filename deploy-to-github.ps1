# Daily Drill Report System - GitHub Deployment Script
# Run this script to deploy your project to GitHub

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Daily Drill Report System" -ForegroundColor Cyan
Write-Host "GitHub Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Git is installed
Write-Host "[1/8] Checking Git installation..." -ForegroundColor Yellow
try {
    $gitVersion = git --version
    Write-Host "[OK] Git found: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Git not found. Please install Git first:" -ForegroundColor Red
    Write-Host "  Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Configure Git (if not already configured)
Write-Host "[2/8] Configuring Git..." -ForegroundColor Yellow
$gitName = git config --global user.name
$gitEmail = git config --global user.email

if (-not $gitName) {
    $name = Read-Host "Enter your name for Git commits"
    git config --global user.name "$name"
    Write-Host "[OK] Git name configured" -ForegroundColor Green
} else {
    Write-Host "[OK] Git already configured: $gitName ($gitEmail)" -ForegroundColor Green
}
Write-Host ""

# Initialize Git repository
Write-Host "[3/8] Initializing Git repository..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "[OK] Git repository already initialized" -ForegroundColor Green
} else {
    git init
    Write-Host "[OK] Git repository initialized" -ForegroundColor Green
}
Write-Host ""

# Create .env.example if it doesn't exist
Write-Host "[4/8] Checking configuration files..." -ForegroundColor Yellow
if (-not (Test-Path ".env.example")) {
    Write-Host "[ERROR] .env.example not found" -ForegroundColor Red
    exit 1
} else {
    Write-Host "[OK] .env.example found" -ForegroundColor Green
}

if (-not (Test-Path ".gitignore")) {
    Write-Host "[ERROR] .gitignore not found" -ForegroundColor Red
    exit 1
} else {
    Write-Host "[OK] .gitignore found" -ForegroundColor Green
}
Write-Host ""

# Check for sensitive files
Write-Host "[5/8] Checking for sensitive files..." -ForegroundColor Yellow
$sensitiveFiles = @(".env", "db.sqlite3", "*.log")
$foundSensitive = $false

foreach ($pattern in $sensitiveFiles) {
    $files = Get-ChildItem -Path . -Filter $pattern -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch "\\\.venv\\" }
    if ($files) {
        Write-Host "[WARNING] Found sensitive file(s): $pattern" -ForegroundColor Yellow
        Write-Host "  These files are in .gitignore and will NOT be committed" -ForegroundColor Yellow
        $foundSensitive = $true
    }
}

if (-not $foundSensitive) {
    Write-Host "[OK] No sensitive files found in project root" -ForegroundColor Green
}
Write-Host ""

# Stage all files
Write-Host "[6/8] Staging files for commit..." -ForegroundColor Yellow
git add .

$stagedFiles = git diff --cached --name-only
$fileCount = ($stagedFiles | Measure-Object).Count

Write-Host "[OK] Staged $fileCount files" -ForegroundColor Green
Write-Host ""

# Show what will be committed
Write-Host "Files to be committed:" -ForegroundColor Cyan
Write-Host "---------------------" -ForegroundColor Cyan
git diff --cached --name-status | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
Write-Host ""

# Confirm before commit
$confirm = Read-Host "Do you want to proceed with the commit? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Deployment cancelled." -ForegroundColor Yellow
    exit 0
}
Write-Host ""

# Create initial commit
Write-Host "[7/8] Creating initial commit..." -ForegroundColor Yellow
$commitMessage = @"
Initial commit: Complete Daily Drill Report System v1.0

Features:
- Core shift management with day/night tracking
- Multi-user approval workflow (Supervisor → Manager → Client)
- Real-time drilling progress tracking with core tray images
- Activity logging and material consumption tracking
- 24-hour combined view for day/night shifts
- BOQ generation (daily/monthly)
- Export capabilities (PDF, Excel, CSV)
- Interactive activity breakdown charts (Chart.js)
- Role-based access control
- Complete test suite and documentation
- Production-ready configuration

Tech Stack:
- Django 5.0
- Python 3.11+
- Bootstrap 5
- PostgreSQL (production)
- Pillow, ReportLab, xlsxwriter
- Gunicorn, WhiteNoise

Documentation:
- README.md: Quick start and usage guide
- DATA_ENGINEERING.md: Data pipeline and analytics
- PRODUCTION_DEPLOYMENT.md: Deployment instructions
- PRODUCTION_CHECKLIST.md: Pre-deployment checklist
- CONTRIBUTING.md: Contribution guidelines
- LICENSE: MIT License
"@

git commit -m $commitMessage
Write-Host "[OK] Commit created" -ForegroundColor Green
Write-Host ""

# Add remote repository
Write-Host "[8/8] Configuring GitHub remote..." -ForegroundColor Yellow
$remoteUrl = "https://github.com/MansLikeNight/DRS-.git"

# Check if remote already exists
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "[OK] Remote 'origin' already configured: $existingRemote" -ForegroundColor Green
} else {
    git remote add origin $remoteUrl
    Write-Host "[OK] Remote 'origin' added: $remoteUrl" -ForegroundColor Green
}
Write-Host ""

# Rename branch to main if needed
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    Write-Host "Renaming branch from '$currentBranch' to 'main'..." -ForegroundColor Yellow
    git branch -M main
    Write-Host "[OK] Branch renamed to 'main'" -ForegroundColor Green
    Write-Host ""
}

# Push to GitHub
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ready to push to GitHub!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repository: $remoteUrl" -ForegroundColor Cyan
Write-Host "Branch: main" -ForegroundColor Cyan
Write-Host ""
Write-Host "Run the following command to push:" -ForegroundColor Yellow
Write-Host ""
Write-Host "    git push -u origin main" -ForegroundColor Green
Write-Host ""
Write-Host "Note: You may need to authenticate with GitHub." -ForegroundColor Yellow
Write-Host "      Use your GitHub username and Personal Access Token (PAT)" -ForegroundColor Yellow
Write-Host ""

# Offer to push automatically
$autoPush = Read-Host "Do you want to push now? (y/n)"
if ($autoPush -eq "y") {
    Write-Host ""
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    try {
        git push -u origin main
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "[OK] Deployment successful!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Your project is now on GitHub:" -ForegroundColor Cyan
        Write-Host "  $remoteUrl" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "  1. Visit the repository on GitHub" -ForegroundColor Gray
        Write-Host "  2. Configure repository settings (description, topics)" -ForegroundColor Gray
        Write-Host "  3. Set up branch protection rules (optional)" -ForegroundColor Gray
        Write-Host "  4. Deploy to production (see PRODUCTION_DEPLOYMENT.md)" -ForegroundColor Gray
        Write-Host ""
    } catch {
        Write-Host ""
        Write-Host "[ERROR] Push failed. Please check your credentials and try again." -ForegroundColor Red
        Write-Host ""
        Write-Host "Troubleshooting:" -ForegroundColor Yellow
        Write-Host "  1. Verify GitHub credentials" -ForegroundColor Gray
        Write-Host "  2. Generate Personal Access Token if needed" -ForegroundColor Gray
        Write-Host "  3. Run manually: git push -u origin main" -ForegroundColor Gray
        Write-Host ""
        exit 1
    }
} else {
    Write-Host ""
    Write-Host "Deployment prepared but not pushed." -ForegroundColor Yellow
    Write-Host "Run 'git push -u origin main' when ready." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "Deployment script completed." -ForegroundColor Cyan
