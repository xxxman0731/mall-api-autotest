# 一键执行:启动服务 -> 运行用例 -> 生成 Allure 报告 -> 停止服务
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

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

Write-Host "[1/4] 启动被测服务..." -ForegroundColor Cyan
$proc = Start-Process -FilePath $python -ArgumentList "mock_server\app.py" -WorkingDirectory $root -WindowStyle Hidden -PassThru
try {
    $ready = $false
    for ($i = 0; $i -lt 20; $i++) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect("127.0.0.1", 5000)
            $tcp.Close()
            $ready = $true
            break
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { throw "被测服务启动失败,请检查 mock_server/app.py 是否正常" }

    Write-Host "[2/4] 运行测试用例..." -ForegroundColor Cyan
    & $python -m pytest --alluredir reports/allure-results --clean-alluredir
    if ($LASTEXITCODE -ne 0) { throw "存在失败用例,请查看 logs/ 与 Allure 报告" }

    Write-Host "[3/4] 生成 Allure 报告..." -ForegroundColor Cyan
    $allureCmd = Get-Command allure -ErrorAction SilentlyContinue
    if ($allureCmd) {
        & allure generate reports/allure-results -o reports/allure-report --clean
        Write-Host "报告已生成: reports/allure-report/index.html" -ForegroundColor Green
    } else {
        Write-Host "未检测到 allure 命令行,跳过报告生成(安装方法见 README.md)" -ForegroundColor Yellow
    }
} finally {
    Write-Host "[4/4] 停止被测服务..." -ForegroundColor Cyan
    if (-not $proc.HasExited) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
}
Write-Host "全部完成" -ForegroundColor Green
