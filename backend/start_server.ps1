# Start CreditBridge API Server
# This script properly configures the environment and starts uvicorn

Write-Host "Starting CreditBridge API Server..." -ForegroundColor Green

# Set working directory
Set-Location f:\MillionX_FinTech\backend

# Add current directory to Python path
$env:PYTHONPATH = (Get-Location).Path

# Load .env file manually
if (Test-Path .env) {
    Write-Host "Loading environment variables from .env..." -ForegroundColor Yellow
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.+)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$key" -Value $value
        }
    }
} else {
    Write-Host "WARNING: .env file not found!" -ForegroundColor Red
}

# Start uvicorn
Write-Host "`nStarting uvicorn server..." -ForegroundColor Green
Write-Host "Server will be available at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "API Documentation: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

python -m uvicorn app.main:app --reload --port 8000 --host 127.0.0.1
