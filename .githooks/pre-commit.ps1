# Pre-commit hook para Windows PowerShell
# Asegura que el script se detenga si algún comando falla
$ErrorActionPreference = "Stop"

Write-Host "`n>>>> Running isort for Python files..." -ForegroundColor Green  
& "C:\Users\facun\AppData\Local\Microsoft\WindowsApps\python3.11.exe" -m isort .

Write-Host "`n>>>> Running Ruff for Python files..." -ForegroundColor Green
& "C:\Users\facun\AppData\Local\Microsoft\WindowsApps\python3.11.exe" -m ruff check --fix .

Write-Host "`n>>>> Running Black for Python files..." -ForegroundColor Green
& "C:\Users\facun\AppData\Local\Microsoft\WindowsApps\python3.11.exe" -m black .

Write-Host "`n>>>> Running Mypy for type checking..." -ForegroundColor Green
& "C:\Users\facun\AppData\Local\Microsoft\WindowsApps\python3.11.exe" -m mypy --config-file=mypy.ini .

# Verificar si algún archivo fue modificado por los comandos anteriores
$gitStatus = & git diff --exit-code 2>$null
$exitCode = $LASTEXITCODE

# Si hay cambios, los añadimos automáticamente al commit
if ($exitCode -ne 0) {
    Write-Host "`n>>>> Some files have been modified! Adding them to the commit..." -ForegroundColor Yellow
    & git add -u
    Write-Host "`n>>>> Files have been updated and staged for commit." -ForegroundColor Green
    exit 1  # Abortamos el commit para que el usuario pueda realizarlo nuevamente con los cambios
}

# Si no hubo cambios, dejamos que el commit continúe
Write-Host "`n>>>> All checks passed! Ready to commit." -ForegroundColor Green
