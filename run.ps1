# LLM Flight Recorder - Startup Script
# Starts both backend (FastAPI) and frontend (Streamlit) in separate windows

Write-Host "Starting LLM Flight Recorder..." -ForegroundColor Green
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Start Backend (FastAPI) in new window
Write-Host "Starting Backend (FastAPI)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PSScriptRoot'; .\.venv\Scripts\Activate; Write-Host 'Backend Server' -ForegroundColor Green; uvicorn backend.main:app --reload --port 8000"
)

# Wait for backend to initialize
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 4

# Start Frontend (Streamlit) in new window
Write-Host "Starting Frontend (Streamlit)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$PSScriptRoot'; .\.venv\Scripts\Activate; Write-Host 'Frontend Dashboard' -ForegroundColor Green; streamlit run frontend/app.py"
)

Write-Host ""
Write-Host "LLM Flight Recorder Started!" -ForegroundColor Green
Write-Host ""
Write-Host "Backend API: http://localhost:8000" -ForegroundColor White
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "Frontend: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in each window to stop" -ForegroundColor Yellow
