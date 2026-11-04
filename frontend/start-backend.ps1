$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'backend/app.py'))) {
    $projectRoot = Join-Path $projectRoot '.publish-repo'
}
$runtimePython = Join-Path $projectRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $runtimePython)) {
    throw 'Create the backend .venv and install backend/requirements-live.txt as explained in README.md.'
}
Push-Location -LiteralPath $projectRoot
try {
    docker compose up -d --wait fuseki
    if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop, then retry.' }
    & $runtimePython -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
