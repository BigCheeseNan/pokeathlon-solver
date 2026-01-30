#!/usr/bin/env pwsh
# Script to launch both backend and frontend servers

Write-Host "Starting Pokeathlon Backend and Frontend..." -ForegroundColor Green

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Define paths
$backendDir = Join-Path $scriptDir "web\backend"
$frontendDir = Join-Path $scriptDir "web\frontend"

# Function to cleanup on exit
function Cleanup {
    Write-Host "`nShutting down servers..." -ForegroundColor Yellow
    Get-Job | Stop-Job
    Get-Job | Remove-Job
}

# Register cleanup on Ctrl+C
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup } | Out-Null

try {
    # Start backend server
    Write-Host "`nStarting Backend (FastAPI)..." -ForegroundColor Cyan
    $backendJob = Start-Job -ScriptBlock {
        param($dir)
        Set-Location $dir
        uvicorn main:app --reload --host 0.0.0.0 --port 8000 2>&1
    } -ArgumentList $backendDir
    
    # Wait a moment for backend to start
    Start-Sleep -Seconds 2
    
    # Start frontend server
    Write-Host "Starting Frontend (Vite)..." -ForegroundColor Cyan
    $frontendJob = Start-Job -ScriptBlock {
        param($dir)
        Set-Location $dir
        npm run dev 2>&1
    } -ArgumentList $frontendDir
    
    Write-Host "`n" -NoNewline
    Write-Host ("=" * 60) -ForegroundColor Green
    Write-Host "Servers are starting!" -ForegroundColor Green
    Write-Host "Backend (FastAPI):  http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Frontend (Vite):    http://localhost:5173" -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Green
    Write-Host "`nPress Ctrl+C to stop both servers`n" -ForegroundColor Yellow
    
    # Monitor jobs and show output
    while ($true) {
        $backendOutput = Receive-Job -Job $backendJob
        $frontendOutput = Receive-Job -Job $frontendJob
        
        if ($backendOutput) {
            Write-Host "[Backend] " -ForegroundColor Magenta -NoNewline
            Write-Host $backendOutput
        }
        
        if ($frontendOutput) {
            Write-Host "[Frontend] " -ForegroundColor Blue -NoNewline
            Write-Host $frontendOutput
        }
        
        # Check if jobs are still running
        if ($backendJob.State -eq "Failed" -or $frontendJob.State -eq "Failed") {
            Write-Host "`nOne or more servers failed to start!" -ForegroundColor Red
            
            if ($backendJob.State -eq "Failed") {
                Write-Host "`nBackend Error:" -ForegroundColor Red
                Receive-Job -Job $backendJob
            }
            
            if ($frontendJob.State -eq "Failed") {
                Write-Host "`nFrontend Error:" -ForegroundColor Red
                Receive-Job -Job $frontendJob
            }
            
            break
        }
        
        Start-Sleep -Milliseconds 500
    }
}
catch {
    Write-Host "`nError: $_" -ForegroundColor Red
}
finally {
    Cleanup
}
