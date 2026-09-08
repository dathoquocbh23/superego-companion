# Chạy backend ở chế độ demo offline (đọc cấu hình từ .env).
#   PS> ./run-dev.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
