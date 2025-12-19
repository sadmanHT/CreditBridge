# Load environment variables from .env file
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}

# Set PYTHONPATH
$env:PYTHONPATH = "f:\MillionX_FinTech\backend"

# Start uvicorn
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
