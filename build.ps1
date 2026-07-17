# 一键打包 OCR-Agent.exe
# 用法：右键 → 使用 PowerShell 运行，或在终端执行 .\build.ps1

Write-Host "1/2 构建前端..." -ForegroundColor Cyan
cd frontend
npx vite build
cd ..

Write-Host "2/2 打包 exe..." -ForegroundColor Cyan
taskkill /F /IM "OCR-Agent.exe" 2>$null
Remove-Item -Recurse -Force backend\dist, backend\build, backend\OCR-Agent.spec -ErrorAction SilentlyContinue

cd backend
venv\Scripts\python.exe -m PyInstaller --onefile --noconsole --icon app.ico --add-data "../frontend/dist;frontend/dist" --collect-all latex2mathml --name "OCR-Agent" --distpath ".." desktop.py
cd ..

Write-Host "完成！OCR-Agent.exe 已生成" -ForegroundColor Green
