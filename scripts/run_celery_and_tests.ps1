<#
Helper script for Windows developers to run Redis (Docker), start a Celery worker, and run pytest integration tests.

Usage:
  .\scripts\run_celery_and_tests.ps1

Prereqs:
  - Docker installed and running
  - Python virtualenv activated for project
  - Redis image (will be pulled automatically)
#>

Write-Host "Starting Redis via Docker (container name: estudify-redis)..."
docker run -d --name estudify-redis -p 6379:6379 redis:7 || Write-Host "Redis container may already be running."

Write-Host "Starting Celery worker (in background). Open another terminal to see logs if needed."
# Adjust python path if necessary; this assumes the virtualenv is activated
Start-Process -NoNewWindow -FilePath pwsh -ArgumentList '-NoLogo','-NoProfile','-Command','celery -A config worker -l info' -WindowStyle Hidden

Write-Host "Give the worker a few seconds to connect to Redis..."
Start-Sleep -Seconds 5

Write-Host "Running integration tests (tests/integration/)"
pytest --maxfail=1 -q tests/integration/

Write-Host "Integration run finished. If you want to stop Redis container run: docker rm -f estudify-redis"
