@echo off

cd /d C:\ReverseEngineer-SDLC\ReverseEngineer-SDLC-OpenCode-v2\ReverseEngineer-SDLC\backend

set "DEBUG_AGENT=true"

if not exist .venv (
    python -m venv .venv
)

.venv\Scripts\python.exe -m pip install -r requirements.txt

set "PATH=C:\Users\n_mur\AppData\Roaming\npm;%PATH%"

start "FastAPI" cmd /k "cd /d C:\ReverseEngineer-SDLC\ReverseEngineer-SDLC-OpenCode-v2\ReverseEngineer-SDLC\backend && set DEBUG_AGENT=true && set PATH=C:\Users\n_mur\AppData\Roaming\npm;%PATH% && .venv\Scripts\python.exe -m uvicorn app.main:app --reload"

start "Next.js" cmd /k "cd /d C:\ReverseEngineer-SDLC\ReverseEngineer-SDLC-OpenCode-v2\ReverseEngineer-SDLC\frontend && npm run dev"