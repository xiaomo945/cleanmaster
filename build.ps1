# 电脑清理大师 - 一键打包脚本
# 用法：以管理员身份打开 PowerShell，进入本目录，执行  .\build.ps1
# 生成的单文件 exe 位于 dist\电脑清理大师.exe

$ErrorActionPreference = "Stop"

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "未检测到 PyInstaller，正在安装…" -ForegroundColor Yellow
    pip install pyinstaller
}

Write-Host "开始打包…" -ForegroundColor Cyan
pyinstaller --onefile --windowed --name "电脑清理大师" clean_master.py

if (Test-Path "dist\电脑清理大师.exe") {
    Write-Host "完成：dist\电脑清理大师.exe" -ForegroundColor Green
} else {
    Write-Host "打包似乎未完成，请检查上方输出。" -ForegroundColor Red
}
