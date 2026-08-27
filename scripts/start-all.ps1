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

# Intenta levantar Docker Desktop si el daemon está caído (Windows)
function Test-DockerDaemon {
  docker ps 2>$null | Out-Null
  return ($LASTEXITCODE -eq 0)
}
if (-not (Test-DockerDaemon)) {
  $svc = Get-Service com.docker.service -ErrorAction SilentlyContinue
  if ($svc -and $svc.Status -ne 'Running') {
    Write-Host "Docker Desktop detenido — intentando iniciarlo..." -ForegroundColor Yellow
    try { Start-Service com.docker.service -ErrorAction SilentlyContinue; Start-Sleep -Seconds 5 } catch {}
    for ($i=0; $i -lt 15; $i++) {
      if (Test-DockerDaemon) { break }
      Start-Sleep -Seconds 2
    }
  }
  if (-not (Test-DockerDaemon)) {
    Write-Warning "Docker daemon no responde. Si tenés Postgres local en 5433 se usará ese; si no, iniciá Docker Desktop manualmente."
  }
}

# Detecta conflicto en :8000 (Splunk usa 8000 por defecto)
$BackendPort = 8000
$occupant = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess -ErrorAction SilentlyContinue
if ($occupant) {
  $procName = (Get-Process -Id $occupant -ErrorAction SilentlyContinue).ProcessName
  if ($procName -and $procName -ne 'python' -and $procName -ne 'uvicorn' -and $procName -ne 'node') {
    Write-Warning "Puerto 8000 ocupado por '$procName' (PID $occupant) — no es backend. Usando 8001 para FastAPI y ajustando proxy."
    $BackendPort = 8001
    $env:API_PROXY_TARGET = "http://localhost:$BackendPort"
  }
}
Write-Host "Backend port seleccionado: $BackendPort (API_PROXY_TARGET=$($env:API_PROXY_TARGET))" -ForegroundColor DarkGray

# 1) DB
Write-Step "1/3 — Postgres (arpia-db) via docker compose"
$dockerOk = $true
try { docker compose up -d db 2>&1 | Out-Host; if ($LASTEXITCODE -ne 0) { $dockerOk = $false } } catch { $dockerOk = $false }
if ($dockerOk) {
  Write-Host "Esperando healthcheck de postgres (pg_isready)..." -ForegroundColor Yellow
  $retries = 0
  $health = $null
  do {
    Start-Sleep -Seconds 2
    $health = docker inspect --format='{{json .State.Health.Status}}' arpia-db 2>$null
    $retries++
    if ($retries -gt 30) { Write-Warning "Timeout esperando postgres healthy. Revisá: docker logs arpia-db — probando conexión directa a 5433..."; break }
  } while ($health -ne '"healthy"')
  if ($health -eq '"healthy"') { Write-Host "DB healthy $health" -ForegroundColor Green }
  else {
    $conn = Get-NetTCPConnection -LocalPort 5433 -ErrorAction SilentlyContinue
    if ($conn) { Write-Host "Postgres escuchando en 5433 (proceso $($conn.OwningProcess)) — continuando sin healthcheck docker" -ForegroundColor Yellow }
    else { Write-Warning "No hay postgres en 5433 y docker no dio healthy. El backend puede fallar al conectar a DB." }
  }
} else {
  Write-Warning "No se pudo iniciar DB vía docker. Verificando 5433 local..."
  $conn = Get-NetTCPConnection -LocalPort 5433 -ErrorAction SilentlyContinue
  if ($conn) { Write-Host "Postgres local detectado en 5433 — continuando" -ForegroundColor Green }
  else { throw "Sin DB disponible. Iniciá Docker Desktop o tu Postgres local en 5433." }
}

# 2) Backend FastAPI :$BackendPort
if ($UseDockerApi) {
  Write-Step "2/3 — Backend FastAPI via docker (arpia-api) :$BackendPort"
  # Si BackendPort es 8001, mapeamos 8001:8000 para el contenedor
  if ($BackendPort -ne 8000) {
    Write-Host "Usando host $BackendPort -> container 8000 (Splunk en 8000)" -ForegroundColor Yellow
    $env:COMPOSE_API_PORT = "$BackendPort"
  }
  docker compose up -d api | Out-Host
  $target = "http://localhost:$BackendPort/docs"
  Write-Host "Esperando $target ..." -ForegroundColor Yellow
  $ok = $false
  for ($i=0; $i -lt 30; $i++) {
    try { $res = Invoke-WebRequest -Uri $target -UseBasicParsing -TimeoutSec 2; if ($res.StatusCode -eq 200) { $ok=$true; break } } catch {}
    Start-Sleep -Seconds 2
  }
  if (-not $ok) { Write-Warning "API docker no respondió en 60s. Logs:"; docker logs --tail 50 arpia-api | Out-Host }
  else { Write-Host "API docker OK en :$BackendPort" -ForegroundColor Green }
} else {
  Write-Step "2/3 — Backend FastAPI local venv en :$BackendPort"
  $uvicorn = Join-Path $RepoRoot "backend\.venv\Scripts\uvicorn.exe"
  if (-not (Test-Path $uvicorn)) { $uvicorn = Join-Path $RepoRoot "backend\.venv\Scripts\python.exe" }
  if (-not (Test-Path $uvicorn)) { throw "No se encontró backend\.venv. Crealo: cd backend; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt" }

  # Solo mata procesos python/uvicorn/node en ese puerto, nunca splunkd/system
  $conns = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
  foreach ($c in $conns) {
    $pName = (Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue).ProcessName
    if ($pName -in @('python','uvicorn','node')) {
      Write-Host "Puerto $BackendPort ocupado por $pName (PID $($c.OwningProcess)) — liberando..." -ForegroundColor Yellow
      try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
    } elseif ($pName) {
      Write-Host "Puerto $BackendPort ocupado por $pName (PID $($c.OwningProcess)) — no se toca (ej. splunkd)" -ForegroundColor DarkGray
    }
  }

  $backendLog = Join-Path $RepoRoot "backend_api.log"
  Write-Host "Lanzando uvicorn en background (log: $backendLog) ..." -ForegroundColor Yellow
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $uvicorn
  if ($uvicorn.EndsWith("uvicorn.exe")) {
    $psi.Arguments = "app.main:app --host 0.0.0.0 --port $BackendPort --reload"
    $psi.WorkingDirectory = (Join-Path $RepoRoot "backend")
  } else {
    $psi.Arguments = "-m uvicorn app.main:app --host 0.0.0.0 --port $BackendPort --reload"
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
  Write-Host "Backend PID $($proc.Id) — esperando /docs en :$BackendPort ..." -ForegroundColor Yellow
  $ok = $false
  for ($i=0; $i -lt 30; $i++) {
    try { $res = Invoke-WebRequest -Uri "http://localhost:$BackendPort/docs" -UseBasicParsing -TimeoutSec 2; if ($res.StatusCode -eq 200) { $ok=$true; break } } catch {}
    Start-Sleep -Seconds 2
  }
  if (-not $ok) {
    Write-Warning "Backend no respondió en 60s en :$BackendPort. Revisá $backendLog y que DATABASE_URL apunte a localhost:5433 (DB_PORT en .env)."
    if (Test-Path $backendLog) { Get-Content $backendLog -Tail 50 | Out-Host }
  } else {
    Write-Host "Backend OK en :$BackendPort (PID $($proc.Id))" -ForegroundColor Green
    Write-Host "Para detenerlo: Stop-Process -Id $($proc.Id) -Force" -ForegroundColor DarkGray
    # Exporta el port elegido para el proxy del front
    $env:API_PROXY_TARGET = "http://localhost:$BackendPort"
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
  Write-Host "Levantando Node en :3000 con USE_MOCK=false (proxy a :$BackendPort)..." -ForegroundColor Yellow
  if ($env:API_PROXY_TARGET) { Write-Host "API_PROXY_TARGET=$($env:API_PROXY_TARGET)" -ForegroundColor DarkGray }
  Write-Host "Comando: npm run start:real  (cross-env USE_MOCK=false API_PROXY_TARGET=$($env:API_PROXY_TARGET) node dist/server.mjs)" -ForegroundColor DarkGray
  # Mata 3000 previo solo si es node
  $conns3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
  foreach ($c in $conns3000) {
    $pName = (Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue).ProcessName
    if ($pName -eq 'node') { Write-Host "Puerto 3000 ocupado por node (PID $($c.OwningProcess)) — liberando..." -ForegroundColor Yellow; try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } catch {} }
  }
  # Lanza en foreground para que el usuario vea logs y haga Ctrl+C
  $env:USE_MOCK = "false"
  if (-not $env:API_PROXY_TARGET) { $env:API_PROXY_TARGET = "http://localhost:$BackendPort" }
  npm run start:real
} else {
  Write-Step "3/3 — Frontend DEV (vite HMR + proxy) en :5173 — USE_MOCK=false"
  Write-Host "Ejecutando: npm run dev:real  (cross-env USE_MOCK=false tsx server.ts + vite)" -ForegroundColor DarkGray
  Write-Host "Abrí http://localhost:5173 — badge debe decir MODO REAL" -ForegroundColor Green
  Write-Host "Verificá: curl http://localhost:3000/api/__mode  o  http://localhost:5173/api/__mode" -ForegroundColor DarkGray
  $env:USE_MOCK = "false"
  npm run dev:real
}
