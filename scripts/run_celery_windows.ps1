# Windows helper to run Celery using the solo pool (avoids prefork issues on Windows)
# Usage: Open PowerShell (recommended: run as Administrator) and run:
#   ./scripts/run_celery_windows.ps1

Param(
  [string]$VenvActivate = ".venv\Scripts\Activate.ps1",
  [int]$concurrency = 1
)

Write-Host "Running Celery worker (Windows-friendly): using solo pool"

if (Test-Path $VenvActivate) {
    Write-Host "Activating virtual environment: $VenvActivate"
    & $VenvActivate
} else {
    Write-Host "Warning: virtualenv activate script not found at $VenvActivate"
}

Write-Host "Starting Celery with solo pool (safe on Windows). Ctrl+C to stop."

# Primary attempt using celery entrypoint
try {
    celery -A config.celery_app worker -l info -P solo -c $concurrency
} catch {
    Write-Host "Primary celery command failed, falling back to python -m celery"
    python -m celery -A config.celery_app worker -l info -P solo -c $concurrency
}

Write-Host "Celery worker exited."