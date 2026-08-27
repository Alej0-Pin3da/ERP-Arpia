#Requires -Version 5.1
<#
.SYNOPSIS
  Levanta todo el stack ERP-Arpía de una vez (DB + Backend + Frontend) en modo REAL (USE_MOCK=false).
.DESCRIPTION
  Por defecto levanta DB y Backend AMBOS en Docker (docker compose), porque tu .env usa
  DATABASE_URL=...@db:5432 — el host "db" solo resuelve dentro de la red Docker, NO desde el .venv local.
  La API se expone en 8080 (evita Splunk en 8000). El front (vite HMR :5173 o Node :3000) proxya a 8080.
  Con -UseLocalApi fuerza backend local venv (requiere que .env apunte a localhost:5433).
.PARAMETER Mode
  dev  -> vite dev:real (HMR) en 5173
  prod -> vite build + node dist/server.mjs en 3000
.PARAMETER UseLocalApi
  Usa backend local .venv en vez de Docker. Requiere DATABASE_URL apuntando a localhost:5433.
.PARAMETER SkipBuild
  En Mode prod, salta el vite build.
.EXAMPLE
  npm run dev:all            # Docker DB+API en 8080, vite en 5173
  npm run start:all          # Docker DB+API en 8080, Node en 3000
  pwsh -File scripts/start-all.ps1 -UseLocalApi
#>

param(
  [ValidateSet('dev','prod')]
  [string]$Mode = 'dev',
  [switch]$UseLocalApi,
  [switch]$SkipBuild
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path "$PSScriptRoot/..").Path
Set-Location $RepoRoot

function Write-Step($msg) { Write-Host "`n== $msg ==" -ForegroundColor Cyan }
function Test-Command($name) { $null -ne (Get-Command $name -ErrorAction SilentlyContinue) }
function Test-DockerDaemon {
  docker ps 2>$null | Out-Null
  return ($LASTEXITCODE -eq 0)
}
function Get-Occupant($port) {
  try { (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess) } catch { $null }
}
function Wait-Url($url, [int]$maxSec = 60) {
  for ($i=0; $i -lt ($maxSec/2); $i++) {
    try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2; if ($r.StatusCode -lt 500) { return $true } } catch {}
    Start-Sleep -Seconds 2
  }
  return $false
}

# 0) Pre-checks
Write-Step "Pre-checks en $RepoRoot (Mode=$Mode, UseLocalApi=$UseLocalApi)"
if (-not (Test-Command docker)) { throw "docker no está en PATH. Instalá Docker Desktop." }

if (-not (Test-DockerDaemon)) {
  $svc = Get-Service com.docker.service -ErrorAction SilentlyContinue
  if ($svc -and $svc.Status -ne 'Running') {
    Write-Host "Docker Desktop detenido — iniciándolo..." -ForegroundColor Yellow
    try { Start-Service com.docker.service -ErrorAction SilentlyContinue } catch {}
  }
  for ($i=0; $i -lt 20; $i++) { if (Test-DockerDaemon) { break }; Start-Sleep -Seconds 2 }
  if (-not (Test-DockerDaemon)) { throw "Docker Desktop no arranca. Inicialo manualmente y reintentá." }
  Write-Host "Docker daemon listo" -ForegroundColor Green
}

# Puerto backend: si la API docker ya corre, usar su puerto host real (docker port).
# Si no, default 8000 (o COMPOSE_API_PORT si se pasó). Evita matar splunkd.
$BackendPort = 8000
try {
  $hostPort = (docker port arpia-api 2>$null | Select-String '0.0.0.0:(\d+)->8000' | Select-Object -First 1).Matches.Groups[1].Value
  if ($hostPort) { $BackendPort = [int]$hostPort }
} catch {}
# Si 8000 default está ocupado por algo que no es Docker (splunkd), buscar puerto libre >=8080
$portTakenByNonDocker = $false
try {
  $occ = Get-Occupant $BackendPort
  if ($occ) {
    $pn = (Get-Process -Id $occ -ErrorAction SilentlyContinue).ProcessName
    if ($pn -and $pn -notin @('wslrelay','com.docker.backend','docker','python','uvicorn','node')) { $portTakenByNonDocker = $true }
  }
} catch { $portTakenByNonDocker = $false }
if ($portTakenByNonDocker) {
  Write-Warning "Puerto $BackendPort ocupado por no-backend. Buscando puerto libre desde 8080..."
  $BackendPort = 8080
  while ((Get-Occupant $BackendPort) -and $BackendPort -lt 8095) { $BackendPort++ }
}
Write-Host "Backend port: $BackendPort" -ForegroundColor DarkGray
$env:API_PROXY_TARGET = "http://localhost:$BackendPort"

# 1) DB
Write-Step "1/3 — Postgres (docker compose db)"
docker compose up -d db 2>&1 | Out-Host
$health = $null
for ($i=0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 2
  $health = docker inspect --format='{{json .State.Health.Status}}' arpia-db 2>$null
  if ($health -eq '"healthy"') { break }
}
if ($health -eq '"healthy"') { Write-Host "DB healthy" -ForegroundColor Green }
else { Write-Warning "DB no dio healthy. docker logs arpia-db:"; docker logs --tail 30 arpia-db 2>&1 | Out-Host }

# 2) Backend
if (-not $UseLocalApi) {
  Write-Step "2/3 — Backend FastAPI via Docker (arpia-api) en :$BackendPort"
  $apiRunning = docker ps --filter "name=^/arpia-api$" --format "{{.Names}}" 2>$null
  if ($apiRunning -eq 'arpia-api') {
    Write-Host "arpia-api ya corre (puerto host $BackendPort) — no se recrea." -ForegroundColor Green
    $env:API_PROXY_TARGET = "http://localhost:$BackendPort"
  } else {
    $env:COMPOSE_API_PORT = "$BackendPort"
    docker compose up -d api 2>&1 | Out-Host
  }
  $ok = Wait-Url "http://localhost:$BackendPort/docs" 60
  if (-not $ok) {
    Write-Warning "API no respondió en :$BackendPort. docker logs arpia-api:"
    docker logs --tail 60 arpia-api 2>&1 | Out-Host
  } else {
    Write-Host "API Docker OK en :$BackendPort" -ForegroundColor Green
  }
} else {
  Write-Step "2/3 — Backend FastAPI local venv en :$BackendPort (requiere DATABASE_URL -> localhost:5433)"
  $uvicorn = Join-Path $RepoRoot "backend\.venv\Scripts\uvicorn.exe"
  if (-not (Test-Path $uvicorn)) { throw "No existe backend\.venv. Crealo con pip install -r backend/requirements.txt" }
  $conns = Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue
  foreach ($c in $conns) {
    $pName = (Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue).ProcessName
    if ($pName -in @('python','uvicorn','node')) { try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } catch {} }
  }
  $backendLog = Join-Path $RepoRoot "backend_api.log"
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $uvicorn
  $psi.Arguments = "app.main:app --host 0.0.0.0 --port $BackendPort --reload"
  $psi.WorkingDirectory = (Join-Path $RepoRoot "backend")
  $psi.UseShellExecute = $false
  $psi.RedirectStandardOutput = $true
  $psi.RedirectStandardError = $true
  $psi.EnvironmentVariables["PYTHONUNBUFFERED"] = "1"
  $proc = [System.Diagnostics.Process]::Start($psi)
  $null = Register-ObjectEvent -InputObject $proc -EventName OutputDataReceived -Action { Add-Content $Event.MessageData -Path $using:backendLog } -ErrorAction SilentlyContinue
  $null = Register-ObjectEvent -InputObject $proc -EventName ErrorDataReceived -Action { Add-Content $Event.MessageData -Path $using:backendLog } -ErrorAction SilentlyContinue
  $proc.BeginOutputReadLine(); $proc.BeginErrorReadLine()
  Write-Host "Backend PID $($proc.Id) — esperando /docs en :$BackendPort ..." -ForegroundColor Yellow
  $ok = Wait-Url "http://localhost:$BackendPort/docs" 60
  if (-not $ok) {
    Write-Warning "Backend no respondió. Revisá $backendLog y que DATABASE_URL apunte a localhost:5433."
    if (Test-Path $backendLog) { Get-Content $backendLog -Tail 40 | Out-Host }
  } else {
    Write-Host "Backend OK en :$BackendPort (PID $($proc.Id))" -ForegroundColor Green
  }
}

# 3) Frontend
if ($Mode -eq 'prod') {
  Write-Step "3/3 — Frontend PROD (vite build + Node :3000)"
  if (-not $SkipBuild) {
    Write-Host "Construyendo front..." -ForegroundColor Yellow
    npm run build | Out-Host
    if ($LASTEXITCODE -ne 0) { throw "vite build falló" }
  }
  $p3000 = Get-Occupant 3000
  if ($p3000) {
    $pn = (Get-Process -Id $p3000 -ErrorAction SilentlyContinue).ProcessName
    if ($pn -eq 'node') { try { Stop-Process -Id $p3000 -Force -ErrorAction SilentlyContinue } catch {} }
  }
  $env:USE_MOCK = "false"
  Write-Host "Abrí http://localhost:3000 — API_PROXY_TARGET=$($env:API_PROXY_TARGET)" -ForegroundColor Green
  npm run start:real
} else {
  Write-Step "3/3 — Frontend DEV (vite HMR + proxy) en :5173"
  $env:USE_MOCK = "false"
  Write-Host "Abrí http://localhost:5173 — badge debe decir MODO REAL (proxy a $($env:API_PROXY_TARGET))" -ForegroundColor Green
  Write-Host "Verificá: curl http://localhost:5173/api/__mode" -ForegroundColor DarkGray
  npm run dev:real
}
