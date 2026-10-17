# ============================================================================
#  SOVEREIGN INDIC VOICE TRIAGE & COMPLIANCE - 1-CLICK DEMO LAUNCHER
#  Ignite With Bangalore: SLNG • Unmute • Google Gemini 2.5 Flash • GitHub
# ============================================================================

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  SOVEREIGN INDIC VOICE AGENT: 1-CLICK DEMO LAUNCHER" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

$rootPath = $PSScriptRoot
Set-Location $rootPath

# 1. Check if FastAPI Backend (Port 8000) is running
Write-Host "[1/3] Checking FastAPI Backend on port 8000..." -ForegroundColor Yellow
$backendPort = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue

if ($backendPort) {
    Write-Host "  [OK] FastAPI Backend is already running on http://localhost:8000" -ForegroundColor Green
} else {
    Write-Host "  -> Launching FastAPI Backend (port 8000) in new window..." -ForegroundColor Gray
    Start-Process -FilePath powershell.exe -ArgumentList "-NoExit", "-Command", "Set-Location '$rootPath\backend'; .\venv\Scripts\python.exe -m uvicorn main:app --port 8000 --reload"
    Start-Sleep -Seconds 3
}

# 2. Check if React Dashboard (Port 5173) is running
Write-Host "[2/3] Checking React Dashboard on port 5173..." -ForegroundColor Yellow
$dashboardPort = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue

if ($dashboardPort) {
    Write-Host "  [OK] React Dashboard is already running on http://localhost:5173" -ForegroundColor Green
} else {
    Write-Host "  -> Launching Vite Dashboard (port 5173) in new window..." -ForegroundColor Gray
    Start-Process -FilePath powershell.exe -ArgumentList "-NoExit", "-Command", "Set-Location '$rootPath\dashboard'; npm run dev"
    Start-Sleep -Seconds 3
}

# 3. Health check against FastAPI backend
Write-Host "[3/3] Performing Provider Readiness Health Check..." -ForegroundColor Yellow
$retries = 5
$healthy = $false

for ($i = 1; $i -le $retries; $i++) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/providers/status" -TimeoutSec 3 -ErrorAction Stop
        if ($response.status -eq "ready" -or $response.providers) {
            $healthy = $true
            Write-Host "  [OK] Backend health check passed! Active Providers:" -ForegroundColor Green
            $response.providers.PSObject.Properties | ForEach-Object {
                Write-Host "       • $($_.Name): $($_.Value.name) (ready=$($_.Value.ready))" -ForegroundColor Cyan
            }
            break
        }
    } catch {
        Write-Host "  ... Waiting for backend to bind ($i/$retries)..." -ForegroundColor DarkGray
        Start-Sleep -Seconds 2
    }
}

if (-not $healthy) {
    Write-Host "  [WARN] Backend is still initializing. Check the opened terminal window." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "  DEMO STACK READY!" -ForegroundColor Green
Write-Host "  • Live Interactive Dashboard: http://localhost:5173" -ForegroundColor White
Write-Host "  • FastAPI API Docs:          http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Compiled Spec Artifacts:   http://localhost:8000/api/spec/compiled" -ForegroundColor White
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "Opening http://localhost:5173 in your default browser..." -ForegroundColor Gray
Start-Process "http://localhost:5173"
Write-Host ""
