# SupermaulTD Build Script (PowerShell)
# Usage: .\build.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SupermaulTD Build Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python and try again" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "🔨 Building SupermaulTD executable..." -ForegroundColor Yellow
Write-Host ""

# Run the Python build script
try {
    python build.py
    Write-Host ""
    Write-Host "✅ Build process completed successfully!" -ForegroundColor Green
} catch {
    Write-Host ""
    Write-Host "❌ Build process failed!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
}

Write-Host ""
Read-Host "Press Enter to exit"
