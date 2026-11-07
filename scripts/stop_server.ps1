# 停止被测服务
$pidFile = Join-Path $PSScriptRoot "server.pid"
if (-not (Test-Path $pidFile)) {
    Write-Host "未找到运行中的服务"
    exit 0
}
$procId = (Get-Content $pidFile | Select-Object -First 1).Trim()
$parsed = 0
if ([int]::TryParse($procId, [ref]$parsed) -and $parsed -gt 0) {
    Stop-Process -Id $parsed -Force -ErrorAction SilentlyContinue
    Write-Host "被测服务已停止 PID=$parsed"
}
Remove-Item $pidFile -Force
