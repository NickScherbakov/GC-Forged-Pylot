<#
================================================================================
 GC-Forged-Pylot Automated Setup Script (auto_setup.ps1)
================================================================================

 LANG: English / Русский / 中文  (scroll for localized instructions)

--------------------------------------------------------------------------------
 ENGLISH (Usage)
--------------------------------------------------------------------------------
 Purpose:
     Fully unattended installation of GC-Forged-Pylot on Windows (PowerShell 5.1+).

 Quick Start:
     powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1

 Common Parameters:
     -ModelUrl <url>              Override model download URL.
     -ModelFileName <name>        Target GGUF filename.
     -ModelDir <path>             Custom models directory (default: ./models).
     -ContextSize <int>           llama.cpp context size (default 1024).
     -ApiKey <string>             API key injected into config & .env.
     -Port <int>                  Server port for generated config (default 8000).
     -SkipModelDownload           Do not download model (use existing path / .env).
     -ForceReinstallDependencies  Reinstall all Python deps (cleans previous install).
     -NoSmokeTest                 Skip import smoke test of llama_cpp.
     -NoStartScript               Do not generate start_server.ps1.
     -NoConfig                    Skip generating auto_config.json.
     -VerboseSetup                Extra logging.

 Exit Codes:
     0 success / >0 fatal error encountered.

--------------------------------------------------------------------------------
 РУССКИЙ (Использование)
--------------------------------------------------------------------------------
 Назначение:
     Полностью автоматическая установка GC-Forged-Pylot под Windows.

 Быстрый запуск:
     powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1

 Параметры:
     -ModelUrl <url>              Свой URL модели.
     -ModelFileName <name>        Имя файла GGUF.
     -ModelDir <path>             Каталог для моделей.
     -ContextSize <int>           Размер контекста (по умолчанию 1024).
     -ApiKey <string>             API ключ для .env и конфига.
     -Port <int>                  Порт сервера (по умолчанию 8000).
     -SkipModelDownload           Пропустить скачивание модели.
     -ForceReinstallDependencies  Переустановить зависимости заново.
     -NoSmokeTest                 Пропустить дымовой импорт llama_cpp.
     -NoStartScript               Не создавать стартовый скрипт.
     -NoConfig                    Не генерировать auto_config.json.
     -VerboseSetup                Расширенные логи.

--------------------------------------------------------------------------------
 中文 (使用说明)
--------------------------------------------------------------------------------
 目的:
     在 Windows 上无人值守安装 GC-Forged-Pylot。

 快速开始:
     powershell -ExecutionPolicy Bypass -File scripts/auto_setup.ps1

 参数:
     -ModelUrl <url>              自定义模型下载地址。
     -ModelFileName <name>        GGUF 模型文件名。
     -ModelDir <path>             模型目录 (默认 ./models)。
     -ContextSize <int>           上下文大小 (默认 1024)。
     -ApiKey <string>             API 密钥写入 .env 与配置。
     -Port <int>                  服务器端口 (默认 8000)。
     -SkipModelDownload           跳过模型下载。
     -ForceReinstallDependencies  重新安装所有依赖。
     -NoSmokeTest                 跳过 llama_cpp 试导入。
     -NoStartScript               不生成启动脚本。
     -NoConfig                    不生成 auto_config.json。
     -VerboseSetup                输出详细日志。

 注意: 若模型已存在可使用 -SkipModelDownload 以加速。
================================================================================
#>

param(
    [string]$ModelUrl = "https://huggingface.co/jmft/tinyllama-1.1b-chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K.gguf",
    [string]$ModelFileName = "tinyllama-1.1b-chat-v1.0.Q4_K.gguf",
    [string]$ModelDir = "models",
    [int]$ContextSize = 1024,
    [string]$ApiKey = "test-key-123",
    [int]$Port = 8000,
    [string]$ModelPreset = "auto",            # auto | tinyllama-q4 | tinyllama-q2
    [string]$ModelSha256 = "",                # Optional expected SHA256 checksum
    [switch]$SkipModelDownload,
    [switch]$ForceReinstallDependencies,
    [switch]$NoSmokeTest,
    [switch]$NoStartScript,
    [switch]$NoConfig,
    [switch]$VerboseSetup
    ,[switch]$AutoFetchChecksum
    ,[string]$SelectPreset = ""           # Optional direct preset override when using menu
)
# --- Extended Model Presets (multi-model menu support) ---
$extendedPresets = @{
    'tinyllama-q4' = @{ url = 'https://huggingface.co/jmft/tinyllama-1.1b-chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K.gguf'; file = 'tinyllama-1.1b-chat-v1.0.Q4_K.gguf'; size_gb = 0.74; min_ram_gb = 6; ctx_rec = 1024 };
    'tinyllama-q2' = @{ url = 'https://huggingface.co/jmft/tinyllama-1.1b-chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q2_K.gguf'; file = 'tinyllama-1.1b-chat-v1.0.Q2_K.gguf'; size_gb = 0.48; min_ram_gb = 4; ctx_rec = 768 };
    'phi-2-q4_0' = @{ url = 'https://huggingface.co/QuantFactory/phi-2-GGUF/resolve/main/phi-2.Q4_0.gguf'; file = 'phi-2.Q4_0.gguf'; size_gb = 1.2; min_ram_gb = 8; ctx_rec = 1024 };
    'mistral-7b-instruct-q4' = @{ url = 'https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf'; file = 'mistral-7b-instruct-v0.2.Q4_K_M.gguf'; size_gb = 4.5; min_ram_gb = 16; ctx_rec = 2048 };
}

$ErrorActionPreference = 'Stop'
Write-Host "[INFO] Auto setup started" -ForegroundColor Cyan
if ($VerboseSetup) { Write-Host "[DEBUG] Parameters: $(($PSBoundParameters | Out-String))" }

# --- Model Preset Resolution ---
$presetMap = $extendedPresets

if ($ModelPreset -eq 'menu') {
    Write-Host "[INFO] Available model presets:" -ForegroundColor Cyan
    "Name                          Size(GB)  MinRAM  RecCtx" | Write-Host
    "--------------------------------------------------------------" | Write-Host
    foreach($k in $extendedPresets.Keys){
        $p = $extendedPresets[$k]
        $line = "{0,-30} {1,6:N2}  {2,6}  {3,6}" -f $k, $p.size_gb, $p.min_ram_gb, $p.ctx_rec
        Write-Host $line
    }
    if ($SelectPreset -and $extendedPresets.ContainsKey($SelectPreset)) {
        $ModelPreset = $SelectPreset
        Write-Host "[INFO] Using explicitly selected preset: $ModelPreset" -ForegroundColor Cyan
    } else {
        try {
            $totalRamGB = [math]::Round(((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB),2)
            $eligible = $extendedPresets.GetEnumerator() | Where-Object { $_.Value.min_ram_gb -le $totalRamGB } | Sort-Object { $_.Value.size_gb }
            if ($eligible.Count -gt 0) { $ModelPreset = $eligible[-1].Key } else { $ModelPreset = 'tinyllama-q2' }
            Write-Host "[INFO] Auto-selected preset '$ModelPreset' for RAM=$totalRamGB GB" -ForegroundColor Cyan
        } catch {
            Write-Host "[WARN] RAM detection failed; falling back tinyllama-q4" -ForegroundColor Yellow
            $ModelPreset = 'tinyllama-q4'
        }
    }
}
elseif ($ModelPreset -eq 'auto') {
    try {
        $totalRamGB = [math]::Round(((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB),2)
        if ($totalRamGB -lt 6) { $ModelPreset = 'tinyllama-q2' } else { $ModelPreset = 'tinyllama-q4' }
        Write-Host "[INFO] Auto-selected model preset '$ModelPreset' based on RAM=$totalRamGB GB" -ForegroundColor Cyan
    } catch {
        Write-Host "[WARN] Could not detect RAM, falling back to tinyllama-q4" -ForegroundColor Yellow
        $ModelPreset = 'tinyllama-q4'
    }
}

if ($presetMap.ContainsKey($ModelPreset)) {
    if (-not $PSBoundParameters.ContainsKey('ModelUrl')) { $ModelUrl = $presetMap[$ModelPreset].url }
    if (-not $PSBoundParameters.ContainsKey('ModelFileName')) { $ModelFileName = $presetMap[$ModelPreset].file }
    if ($ContextSize -eq 1024 -and $presetMap[$ModelPreset].ContainsKey('ctx_rec')) { $ContextSize = $presetMap[$ModelPreset].ctx_rec }
    Write-Host "[INFO] Using preset: $ModelPreset -> $ModelFileName (ctx=$ContextSize)" -ForegroundColor Cyan
} else {
    Write-Host "[WARN] Unknown ModelPreset '$ModelPreset' - using direct parameters" -ForegroundColor Yellow
}

# Root path
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "[INFO] Project root: $ProjectRoot"
Set-Location $ProjectRoot

function Test-Python {
    function Download-FileWithProgress {
        param(
            [Parameter(Mandatory=$true)][string]$Url,
            [Parameter(Mandatory=$true)][string]$Destination
        )
        try {
            Add-Type -AssemblyName System.Net.Http
            $client = New-Object System.Net.Http.HttpClient
            $response = $client.GetAsync($Url, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).Result
            if (-not $response.IsSuccessStatusCode) { throw "HTTP $($response.StatusCode)" }
            $total = $response.Content.Headers.ContentLength
            $stream = $response.Content.ReadAsStreamAsync().Result
            $fs = [System.IO.File]::Open($Destination, [System.IO.FileMode]::Create)
            $buffer = New-Object byte[] 65536
            $read = 0
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            while (($len = $stream.Read($buffer,0,$buffer.Length)) -gt 0) {
                $fs.Write($buffer,0,$len)
                $read += $len
                if ($total -and $total -gt 0) {
                    $pct = [int](($read / $total) * 100)
                    $rate = if ($sw.Elapsed.TotalSeconds -gt 0) { [math]::Round(($read/1MB)/$sw.Elapsed.TotalSeconds,2) } else { 0 }
                    Write-Progress -Activity "Downloading model" -Status "$pct% ($rate MB/s)" -PercentComplete $pct
                }
            }
            $fs.Close(); $stream.Close(); $client.Dispose();
            Write-Progress -Activity "Downloading model" -Completed
        } catch {
            Write-Host "[WARN] Chunked download failed: $($_.Exception.Message); falling back Invoke-WebRequest" -ForegroundColor Yellow
            Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing
        }
    }
    try {
        $ver = python --version 2>&1
        if (-not $ver) { return $false }
        Write-Host "[INFO] Python detected: $ver" -ForegroundColor Green
        return $true
    } catch { return $false }
}

if (-not (Test-Python)) {
    Write-Host "[ERROR] Python не найден в PATH. Установите Python 3.10+ и перезапустите." -ForegroundColor Red
    exit 1
}

# --- Virtual Environment ---
$VenvPath = Join-Path $ProjectRoot 'venv'
$PythonExe = Join-Path $VenvPath 'Scripts\python.exe'
if ($ForceReinstallDependencies -and (Test-Path $VenvPath)) {
    Write-Host "[INFO] Force reinstall requested: removing existing venv" -ForegroundColor Yellow
    try { Remove-Item -Recurse -Force $VenvPath } catch { Write-Host "[WARN] Cannot remove venv: $($_.Exception.Message)" -ForegroundColor Yellow }
}
if (-not (Test-Path $VenvPath)) {
    Write-Host "[INFO] Creating virtual environment" -ForegroundColor Cyan
    python -m venv $VenvPath
} else {
    Write-Host "[INFO] venv already exists, reusing" -ForegroundColor Yellow
}

if (-not (Test-Path $PythonExe)) {
    Write-Host "[ERROR] Python executable inside venv not found: $PythonExe" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Upgrading pip" -ForegroundColor Cyan
& $PythonExe -m pip install --upgrade pip setuptools wheel

# --- Requirements Installation ---
Write-Host "[INFO] Installing dependencies from requirements.txt" -ForegroundColor Cyan
try {
    & $PythonExe -m pip install -r requirements.txt
} catch {
    Write-Host "[WARN] Initial install failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "[INFO] Retrying llama-cpp-python with prefer-binary" -ForegroundColor Cyan
    try { & $PythonExe -m pip install --prefer-binary llama-cpp-python } catch { Write-Host "[ERROR] llama-cpp-python fallback failed" -ForegroundColor Red }
}

if ($VerboseSetup) {
    Write-Host "[DEBUG] Installed packages:" -ForegroundColor DarkCyan
    & $PythonExe -m pip list | Select-String "llama-cpp|fastapi|uvicorn|numpy" | ForEach-Object { Write-Host "[DEBUG] $_" }
}

# --- Models Directory ---
$ModelsDir = Join-Path $ProjectRoot $ModelDir
if (-not (Test-Path $ModelsDir)) { New-Item -ItemType Directory -Path $ModelsDir | Out-Null }
$ModelPath = Join-Path $ModelsDir $ModelFileName

if ($SkipModelDownload) {
    Write-Host "[INFO] Skipping model download by request" -ForegroundColor Yellow
} else {
    $needsDownload = -not (Test-Path $ModelPath)
    if (-not $needsDownload) {
        Write-Host "[INFO] Model already exists: $ModelPath" -ForegroundColor Yellow
    }
    if ($needsDownload) {
        Write-Host "[INFO] Downloading model: $ModelFileName" -ForegroundColor Cyan
        try {
            Download-FileWithProgress -Url $ModelUrl -Destination $ModelPath
            Write-Host "[INFO] Model downloaded: $ModelPath" -ForegroundColor Green
        } catch {
            Write-Host "[ERROR] Failed to download model: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
    if ($ModelSha256) {
        try {
            $hash = (Get-FileHash -Path $ModelPath -Algorithm SHA256).Hash.ToLower()
            if ($hash -ne $ModelSha256.ToLower()) {
                    elseif ($AutoFetchChecksum -and -not $ModelSha256) {
                        Write-Host "[INFO] Attempting auto-fetch of checksum (.sha256)" -ForegroundColor Cyan
                        $checksumUrl = "$ModelUrl.sha256"
                        try {
                            $csTmp = Join-Path $env:TEMP "model.sha256.txt"
                            Invoke-WebRequest -Uri $checksumUrl -OutFile $csTmp -UseBasicParsing -ErrorAction Stop
                            $raw = (Get-Content $csTmp -ErrorAction Stop) -join "" | Trim
                            # Parse first 64 hex chars
                            $candidate = ($raw -replace "[^0-9a-fA-F]","" ).Substring(0,64)
                            if ($candidate.Length -eq 64) {
                                $ModelSha256 = $candidate
                                Write-Host "[INFO] Auto-fetched checksum: $ModelSha256" -ForegroundColor Green
                                $hash = (Get-FileHash -Path $ModelPath -Algorithm SHA256).Hash.ToLower()
                                if ($hash -ne $ModelSha256.ToLower()) {
                                    Write-Host "[ERROR] Auto-fetched checksum mismatch" -ForegroundColor Red
                                    Write-Host "Expected: $ModelSha256" -ForegroundColor Red
                                    Write-Host "Actual  : $hash" -ForegroundColor Red
                                    exit 2
                                } else { Write-Host "[INFO] Checksum verified (auto-fetched)" -ForegroundColor Green }
                            } else {
                                Write-Host "[WARN] Unable to parse checksum file" -ForegroundColor Yellow
                            }
                            Remove-Item $csTmp -Force -ErrorAction SilentlyContinue
                        } catch {
                            Write-Host "[WARN] Auto-fetch checksum failed: $($_.Exception.Message)" -ForegroundColor Yellow
                        }
                    }
                Write-Host "[ERROR] Checksum mismatch for $ModelFileName" -ForegroundColor Red
                Write-Host "[ERROR] Expected: $ModelSha256" -ForegroundColor Red
                Write-Host "[ERROR] Actual  : $hash" -ForegroundColor Red
                try { Remove-Item -Force $ModelPath } catch { }
                exit 2
            } else {
                Write-Host "[INFO] Checksum verified (SHA256)" -ForegroundColor Green
            }
        } catch {
            Write-Host "[WARN] Failed to compute checksum: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

# --- .env Creation ---
$EnvFile = Join-Path $ProjectRoot '.env'
$envContent = @(
    "GC_MODEL_PATH=$ModelPath",
    "GC_API_KEY=$ApiKey"
) -join "`n"
Set-Content -Path $EnvFile -Value $envContent -Encoding UTF8
Write-Host "[INFO] .env written" -ForegroundColor Green

# --- Auto Config JSON ---
$ConfigDir = Join-Path $ProjectRoot 'config'
if (-not (Test-Path $ConfigDir)) { New-Item -ItemType Directory -Path $ConfigDir | Out-Null }
$AutoConfig = Join-Path $ConfigDir 'auto_config.json'
if (-not $NoConfig) {
    $cfg = @{ 
        server = @{ host = "127.0.0.1"; port = $Port; verbose = $false };
        model  = @{ path = $ModelPath; n_ctx = $ContextSize; n_gpu_layers = 0 };
        cache  = @{ enabled = $true; size = 100; ttl = 3600 };
        api_keys = @($ApiKey)
    }
    $cfg | ConvertTo-Json -Depth 6 | Set-Content -Path $AutoConfig -Encoding UTF8
    Write-Host "[INFO] Created config/auto_config.json" -ForegroundColor Green
} else {
    Write-Host "[INFO] Skipping auto_config.json generation" -ForegroundColor Yellow
}

# --- Start Script ---
if (-not $NoStartScript) {
    $StartScript = Join-Path $ProjectRoot 'scripts\start_server.ps1'
    $startContent = @'
param(
    [int]$Port = 8000,
    [string]$Config = "..\config\auto_config.json"
)
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPy = Join-Path $ProjectRoot '..\venv\Scripts\python.exe'
if (-not (Test-Path $VenvPy)) { Write-Host "[ERROR] venv python not found" -ForegroundColor Red; exit 1 }
Write-Host "[INFO] Starting server on port $Port" -ForegroundColor Cyan
& $VenvPy ..\main.py --config $Config --host 127.0.0.1 --port $Port
'@
    $startContent | Set-Content -Path $StartScript -Encoding UTF8
    Write-Host "[INFO] Created start_server.ps1" -ForegroundColor Green
} else {
    Write-Host "[INFO] Skipping start_server.ps1 generation" -ForegroundColor Yellow
}

# --- Basic Smoke Test (optional, non-fatal) ---
if (-not $NoSmokeTest) {
    Write-Host "[INFO] Performing smoke import test" -ForegroundColor Cyan
    try {
        & $PythonExe -c "import llama_cpp, sys; print('[SMOKE] llama_cpp imported OK')" 2>$null
    } catch { Write-Host "[WARN] llama_cpp import failed (may be stub): $($_.Exception.Message)" -ForegroundColor Yellow }
} else {
    Write-Host "[INFO] Smoke test skipped" -ForegroundColor Yellow
}

Write-Host "[SUCCESS] Auto setup complete." -ForegroundColor Green
Write-Host "Run (EN): powershell -ExecutionPolicy Bypass -File scripts/start_server.ps1" -ForegroundColor Cyan
Write-Host "Запуск (RU): powershell -ExecutionPolicy Bypass -File scripts/start_server.ps1" -ForegroundColor Cyan
Write-Host "运行 (ZH): powershell -ExecutionPolicy Bypass -File scripts/start_server.ps1" -ForegroundColor Cyan
