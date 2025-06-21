$ErrorActionPreference = "Stop"

Write-Host "`n>>>> Checking for unstaged files to stash..." -ForegroundColor Cyan
$unstagedFiles = (git diff --name-only)

if ($unstagedFiles.Count -gt 0) {
    Write-Host "The following unstaged files will be temporarily stashed:" -ForegroundColor Yellow
    Write-Host "++++++++++++++++++++++++++++++++" -ForegroundColor Red
    $unstagedFiles | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
    Write-Host "++++++++++++++++++++++++++++++++" -ForegroundColor Red
    git stash push --quiet --keep-index --message "pre-commit-stash"
}
else {
    Write-Host "No unstaged files to stash." -ForegroundColor Green
}


try {
    $pythonFiles = (git diff --cached --name-only --diff-filter=ACMR) | Where-Object { $_.EndsWith(".py") }

    if ($pythonFiles.Count -eq 0) {
        Write-Host "`n>>>> No Python files staged for commit. Skipping checks." -ForegroundColor Green
        return 
    }
    else {
        Write-Host "`n>>>> Found $($pythonFiles.Count) Python file(s) to check:" -ForegroundColor Cyan
        Write-Host "++++++++++++++++++++++++++++++++" -ForegroundColor Red
        $pythonFiles | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
        Write-Host "++++++++++++++++++++++++++++++++" -ForegroundColor Red
    }

    Write-Host "`n>>>> Running isort..." -ForegroundColor Green
    python -m isort $pythonFiles

    Write-Host "`n>>>> Running Ruff..." -ForegroundColor Green
    python -m ruff check --fix $pythonFiles

    Write-Host "`n>>>> Running Black..." -ForegroundColor Green
    python -m black $pythonFiles
    
    Write-Host "`n>>>> Running Mypy..." -ForegroundColor Green
    python -m mypy --config-file=mypy.ini $pythonFiles

    git diff --quiet --exit-code
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n>>>> Files were modified by formatters. Staging changes..." -ForegroundColor Yellow
        git add $pythonFiles
    }

    Write-Host "`n>>>> All Python checks passed!" -ForegroundColor Green
}
finally {
    Write-Host "`n>>>> Restoring stashed changes..." -ForegroundColor Yellow
    git stash pop --quiet -ErrorAction SilentlyContinue
}