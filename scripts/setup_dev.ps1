# Setup development environment for Estudify (PowerShell)
# Usage: Open PowerShell, cd to project root and run: .\scripts\setup_dev.ps1
# This script will create a .venv (if missing), activate it, install requirements,
# copy .env.example to .env (if .env missing) and generate a SECRET_KEY.

param()

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ProjectRoot

# 1) Create venv if missing
if (-not (Test-Path .venv)) {
    Write-Host "Creating virtual environment .venv..."
    python -m venv .venv
} else {
    Write-Host ".venv already exists"
}

# 2) Activate venv
$activate = Join-Path $PWD '.venv\Scripts\Activate.ps1'
if (Test-Path $activate) {
    Write-Host "Activating .venv..."
    & $activate
} else {
    Write-Error "Activation script not found at $activate"
    exit 1
}

# 3) Upgrade pip and install requirements
Write-Host "Upgrading pip and installing requirements..."
python -m pip install --upgrade pip
if (Test-Path requirements.txt) {
    python -m pip install -r requirements.txt
} else {
    Write-Warning "requirements.txt not found"
}

# 4) Create .env from example if missing
if (-not (Test-Path .env)) {
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-Host ".env created from .env.example"

        # Generate SECRET_KEY and replace
        $secret = python - <<'PY'
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
PY
        $secret = $secret.Trim()
        (Get-Content .env) -replace '^SECRET_KEY=.*', "SECRET_KEY=$secret" | Set-Content .env
        Write-Host "SECRET_KEY generated and written to .env"
    } else {
        Write-Warning ".env.example not found; create .env manually"
    }
} else {
    Write-Host ".env already exists — not modifying"
}

Write-Host "Setup finished. Activate the venv with: .\.venv\Scripts\Activate.ps1 if not active."