#Requires -Version 5.1
<#
.SYNOPSIS
  Levanta todo el stack ERP-Arpía de una vez (DB + Backend FastAPI + Frontend) en modo REAL (USE_MOCK=false).
.DESCRIPTION
  - DB: docker compose up -d db (postgres:16, healthcheck) o reutiliza si ya está healthy
  - Backend: por defecto local venv (uvicorn --reload) en 8000; con -UseDockerApi usa docker compose api
  - Frontend: dev (vite HMR en 5173 + proxy) o prod (vite build + node dist/server.mjs en 3000)
  Valentina/mock desaparece solo cuando los 3 están en REAL y /api/__mode da {"mode":"real"}.
.PARAMETER Mode
  dev  -> vite dev:real (recomendado, HMR) en 5173
  prod -> vite build + node start:real en 3000
.PARAMETER UseDockerApi
  Si está presente, levanta el backend vía docker compose api en vez de venv local.
.PARAMETER SkipBuild
  En Mode prod, salta el vite build (usa dist existente).
.EXAMPLE
  pwsh -File scripts/start-all.ps1
  pwsh -File scripts/start-all.ps1 -Mode prod
  pwsh -File scripts/start-all.ps1 -UseDockerApi
  npm run dev:all   # atajo a dev
  npm run start:all # atajo a prod
#>

param(
  [ValidateSet('dev','prod')]
  [string]$Mode = 'dev',
  [switch]$UseDockerApi,
  [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path "$PSScriptRoot/..").Path
Set-Location $RepoRoot

function Write-Step($msg) { Write-Host "`n== $msg ==" -ForegroundColor Cyan }
function Test-Command($name) { $null -ne (Get-Command $name -ErrorAction SilentlyContinue) }

# 0) Pre-checks
Write-Step "Pre-checks en $RepoRoot (Mode=$Mode, UseDockerApi=$UseDockerApi)"
if (-not (Test-Command docker)) { throw "docker no está en PATH. Instalá Docker Desktop o usá tu Postgres local y corré el backend manual." }
if (-not (Test-Path ".env")) { Write-Warning ".env no encontrado — usando defaults de docker-compose.yml / .env.example" }

# 1) DB
Write-Step "1/3 — Postgres (arpia-db) via docker compose"
docker compose up -d db | Out-Host
Write-Host "Esperando healthcheck de postgres (pg_isready)..." -ForegroundColor Yellow
$retries = 0
do {
  Start-Sleep -Seconds 2
  $health = docker inspect --format='{{json .State.Health.Status}}' arpia-db 2>$null
  $retries++
  if ($retries -gt 30) { throw "Timeout esperando postgres healthy. Revisá: docker logs arpia-db" }
} while ($health -ne '"healthy"')
Write-Host "DB healthy $health" -ForegroundColor Green

# 2) Backend FastAPI :8000
if ($UseDockerApi) {
  Write-Step "2/3 — Backend FastAPI via docker (arpia-api) :8000"
  docker compose up -d api | Out-Host
  $target = "http://localhost:8000/docs"
  Write-Host "Esperando $target ..." -ForegroundColor Yellow
  $ok = $false
  for ($i=0; $i -lt 30; $i++) {
    try { $res = Invoke-WebRequest -Uri $target -UseBasicParsing -TimeoutSec 2; if ($res.StatusCode -eq 200) { $ok=$true; break } } catch {}
    Start-Sleep -Seconds 2
  }
  if (-not $ok) { Write-Warning "API docker no respondió en 60s. Logs:"; docker logs --tail 50 arpia-api | Out-Host }
  else { Write-Host "API docker OK en :8000" -ForegroundColor Green }
} else {
  Write-Step "2/3 — Backend FastAPI local venv en :8000"
  $uvicorn = Join-Path $RepoRoot "backend\.venv\Scripts\uvicorn.exe"
  if (-not (Test-Path $uvicorn)) { $uvicorn = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe" }
  if (-not (Test-Path $uvicorn)) { throw "No se encontró backend\.venv. Crealo: cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt" }

  # Mata uvicorn previo en 8000 si existe (evita EADDRINUSE)
  $p8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
  if ($p8000) { Write-Host "Puerto 8000 ocupado por PID $p8000 — liberando..." -ForegroundColor Yellow; try { Stop-Process -Id $p8000 -Force -ErrorAction SilentlyContinue } catch {} }

  $backendLog = Join-Path $RepoRoot "backend_api.log"
  Write-Host "Lanzando uvicorn en background (log: $backendLog) ..." -ForegroundColor Yellow
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $uvicorn
  if ($uvicorn.EndsWith("uvicorn.exe")) {
    $psi.Arguments = "app.main:app --host 0.0.0.0 --port 8000 --reload"
    $psi.WorkingDirectory = (Join-Path $RepoRoot "backend")
  } else {
    $psi.Arguments = "-m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    $psi.WorkingDirectory = (Join-Path $RepoRoot "backend")
  }
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1"
  $proc = [System.Diagnostics.Process]::Start($psi)
  # Redirige logs async
  $null = Register-ObjectEvent -InputObject $proc -EventName OutputDataReceived -Action { Add-Content $Event.MessageData -Path $using:backendLog } -ErrorAction SilentlyContinue
  $null = Register-ObjectEvent -InputObject $proc -EventName ErrorDataReceived -Action { Add-Content $Event.MessageData -Path $using:backendLog } -ErrorAction SilentlyContinue
  $proc.BeginOutputReadLine(); $proc.BeginErrorReadLine()
  Write-Host "Backend PID $($proc.Id) — esperando /docs ..." -ForegroundColor Yellow
  $ok = $false
  for ($i=0; $i -lt 30; $i++) {
    try { $res = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 2; if ($res.StatusCode -eq 200) { $ok=$true; break } } catch {}
    Start-Sleep -Seconds 2
  }
  if (-not $ok) {
    Write-Warning "Backend no respondió en 60s. Revisá $backendLog y que DATABASE_URL apunte a localhost:5433 (DB_PORT en .env)."
    Get-Content $backendLog -Tail 50 | Out-Host
  } else {
    Write-Host "Backend OK en :8000 (PID $($proc.Id))" -ForegroundColor Green
    Write-Host "Para detenerlo: Stop-Process -Id $($proc.Id) -Force" -ForegroundColor DarkGray
  }
}

# 3) Frontend
if ($Mode -eq 'prod') {
  Write-Step "3/3 — Frontend PROD (vite build + Node :3000)"
  if (-not $SkipBuild) {
    Write-Host "Construyendo front (vite build)..." -ForegroundColor Yellow
    npm run build | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "vite build falló" }
  }
  Write-Host "Levantando Node en :3000 con USE_MOCK=false (proxy a :8000)..." -ForegroundColor Yellow
  Write-Host "Comando: npm run start:real  (cross-env USE_MOCK=false node dist/server.mjs)" -ForegroundColor DarkGray
  # Mata 3000 previo
  $p3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
  if ($p3000) { Write-Host "Puerto 3000 ocupado por PID $p3000 — liberando..." -ForegroundColor Yellow; try { Stop-Process -Id $p3000 -Force -ErrorAction SilentlyContinue } catch {} }
  # Lanza en foreground para que el usuario vea logs y haga Ctrl+C
  $env:USE_MOCK = "false"
  npm run start:real
} else {
  Write-Step "3/3 — Frontend DEV (vite HMR + proxy) en :5173 — USE_MOCK=false"
  Write-Host "Ejecutando: npm run dev:real  (cross-env USE_MOCK=false tsx server.ts + vite)" -ForegroundColor DarkGray
  Write-Host "Abrí http://localhost:5173 — badge debe decir MODO REAL" -ForegroundColor Green
  Write-Host "Verificá: curl http://localhost:3000/api/__mode  o  http://localhost:5173/api/__mode" -ForegroundColor DarkGray
  $env:USE_MOCK = "false"
  npm run dev:real
}
