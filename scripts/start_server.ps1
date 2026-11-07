# 启动被测服务(后台隐藏窗口)
$root = Split-Path -Parent $PSScriptRoot
$candidates = @(
    (Join-Path $root ".venv\Scripts\python.exe"),
    "E:\Python312\python.exe",
    "python"
)
$python = $null
foreach ($c in $candidates) {
    if ($c -eq "python") {
        $cmd = Get-Command python -ErrorAction SilentlyContinue
        if ($cmd) { $python = $cmd.Source; break }
    } elseif (Test-Path $c) {
        $python = $c
        break
    }
}
if (-not $python) { Write-Error "未找到 Python,请先安装并加入 PATH"; exit 1 }
$proc = Start-Process -FilePath $python -ArgumentList "mock_server\app.py" -WorkingDirectory $root -WindowStyle Hidden -PassThru
Set-Content -Path (Join-Path $PSScriptRoot "server.pid") -Value $proc.Id
Write-Host "被测服务已启动 PID=$($proc.Id)  http://127.0.0.1:5000"
