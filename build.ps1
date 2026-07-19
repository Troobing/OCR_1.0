# Build OCR-Agent.exe
Write-Host "1/2 Building frontend..." -ForegroundColor Cyan
cd frontend
npx vite build
cd ..

Write-Host "2/2 Packaging exe..." -ForegroundColor Cyan
taskkill /F /IM "OCR-Agent.exe" 2>$null
Remove-Item -Recurse -Force backend\dist, backend\build, backend\OCR-Agent.spec -ErrorAction SilentlyContinue

cd backend
venv\Scripts\python.exe -m PyInstaller --onefile --noconsole --icon app.ico --add-data "../frontend/dist;frontend/dist" --collect-all latex2mathml --name "OCR-Agent" --distpath ".." desktop.py
cd ..

Write-Host "Done! OCR-Agent.exe created" -ForegroundColor Green
