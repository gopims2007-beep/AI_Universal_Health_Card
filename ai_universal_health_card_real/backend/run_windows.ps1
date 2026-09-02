python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
Write-Host "Edit .env, create MySQL database, then run:"
Write-Host "uvicorn app.main:app --reload --port 8000"
