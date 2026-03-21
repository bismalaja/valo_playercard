param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [switch]$RunAudit,
    [switch]$RunHttpProbes,
    [switch]$RunBootstrapFlow
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Push-Location $repoRoot

try {

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Run-Command {
    param([string]$Command)
    Write-Host "[cmd] $Command" -ForegroundColor DarkGray
    Invoke-Expression $Command
}

# Resolve python executable (prefer project venv)
$pythonExe = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
$pythonExe = [System.IO.Path]::GetFullPath($pythonExe)
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Step "Using Python interpreter: $pythonExe"

Write-Step "Install pinned dependencies"
Run-Command "$pythonExe -m pip install -r requirements.txt"

Write-Step "Run Django system checks"
Run-Command "$pythonExe manage.py check"

Write-Step "Run targeted security tests"
Run-Command "$pythonExe manage.py test profiles.tests.test_security -v 2"

if ($RunBootstrapFlow) {
    Write-Step "Run bootstrap admin credential flow checks"

    if (-not $env:BOOTSTRAP_ADMIN_USERNAME) { $env:BOOTSTRAP_ADMIN_USERNAME = "admin" }
    if (-not $env:BOOTSTRAP_ADMIN_EMAIL) { $env:BOOTSTRAP_ADMIN_EMAIL = "admin@example.com" }
    if (-not $env:BOOTSTRAP_ADMIN_PASSWORD) { $env:BOOTSTRAP_ADMIN_PASSWORD = "ChangeMe_Strong_123!" }

    Write-Host "BOOTSTRAP_ADMIN_USERNAME=$($env:BOOTSTRAP_ADMIN_USERNAME)" -ForegroundColor Yellow
    Write-Host "BOOTSTRAP_ADMIN_EMAIL=$($env:BOOTSTRAP_ADMIN_EMAIL)" -ForegroundColor Yellow
    Write-Host "BOOTSTRAP_ADMIN_PASSWORD is set for this process." -ForegroundColor Yellow

    Write-Host "First setup_project run (create or skip)" -ForegroundColor Gray
    Run-Command "$pythonExe manage.py setup_project"

    Write-Host "Second setup_project run (should skip rotation by default)" -ForegroundColor Gray
    Run-Command "$pythonExe manage.py setup_project"

    $env:BOOTSTRAP_ADMIN_PASSWORD = "ChangeMe_Strong_456!"
    Write-Host "Rotate flow with --rotate-admin-password" -ForegroundColor Gray
    Run-Command "$pythonExe manage.py setup_project --rotate-admin-password"
}

if ($RunAudit) {
    Write-Step "Run dependency vulnerability audit"
    Run-Command "$pythonExe -m pip install pip-audit"
    Run-Command "$pythonExe -m pip_audit --progress-spinner off"
}

if ($RunHttpProbes) {
    Write-Step "HTTP probes (requires runserver already running at $BaseUrl)"

    Write-Host "Login redirect safety probe" -ForegroundColor Gray
    try {
        $loginResp = Invoke-WebRequest -Uri "$BaseUrl/accounts/login/?next=https://evil.example" -Method Get -MaximumRedirection 0 -ErrorAction SilentlyContinue
        Write-Host "Login page reachable: HTTP $($loginResp.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "Login GET probe completed (redirect or block may be expected)." -ForegroundColor Green
    }

    Write-Host "GET logout should be blocked (405 expected)" -ForegroundColor Gray
    try {
        $logoutResp = Invoke-WebRequest -Uri "$BaseUrl/accounts/logout/" -Method Get -MaximumRedirection 0 -ErrorAction Stop
        Write-Host "Logout GET returned HTTP $($logoutResp.StatusCode)" -ForegroundColor Yellow
    } catch {
        if ($_.Exception.Response) {
            Write-Host "Logout GET blocked with HTTP $([int]$_.Exception.Response.StatusCode)" -ForegroundColor Green
        } else {
            Write-Host "Logout GET probe failed without HTTP response." -ForegroundColor Yellow
        }
    }

    Write-Host "Tracker endpoint rate-limit probe (likely 401 unless logged in; 429 after burst when authenticated)" -ForegroundColor Gray
    $trackerBody = '{"riot_id":"Tyloo","riot_tag":"#NA1"}'
    for ($i = 1; $i -le 12; $i++) {
        try {
            $trackerResp = Invoke-RestMethod -Uri "$BaseUrl/api/fetch-tracker/" -Method Post -ContentType "application/json" -Body $trackerBody -ErrorAction Stop
            Write-Host "Attempt ${i}: success" -ForegroundColor Gray
        } catch {
            if ($_.Exception.Response) {
                $code = [int]$_.Exception.Response.StatusCode
                Write-Host "Attempt ${i}: HTTP $code" -ForegroundColor Gray
            } else {
                Write-Host "Attempt ${i}: request failed" -ForegroundColor Gray
            }
        }
    }
}

Write-Step "Security smoke test complete"
Write-Host "Tip: use -RunAudit for pip-audit, -RunBootstrapFlow for setup_project checks, and -RunHttpProbes for live endpoint probes." -ForegroundColor Green

} finally {
    Pop-Location
}
