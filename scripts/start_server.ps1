param(
    [int]$Port = 8000
)
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPy = Join-Path $ProjectRoot '..\venv\Scripts\python.exe'
if (-not (Test-Path $VenvPy)) { Write-Host "[ERROR] venv python not found" -ForegroundColor Red; exit 1 }
Write-Host "[INFO] Starting server on port $Port" -ForegroundColor Cyan
& $VenvPy ..\main.py --config ..\config\auto_config.json --host 127.0.0.1 --port $Port