pipeline {
    agent any
    // 每日凌晨 2 点定时回归(也可在 Jenkins 界面配置 Webhook 提测触发)
    triggers { cron('H 2 * * *') }
    environment {
        PYTHON = 'python'
    }
    stages {
        stage('拉取代码') {
            steps { checkout scm }
        }
        stage('安装依赖') {
            steps { bat "${PYTHON} -m pip install -r requirements.txt" }
        }
        stage('启动被测服务') {
            steps {
                powershell "Start-Process -FilePath '${PYTHON}' -ArgumentList 'mock_server/app.py' -WorkingDirectory ${WORKSPACE} -WindowStyle Hidden -PassThru | Select-Object -ExpandProperty Id | Set-Content -Path server.pid"
            }
        }
        stage('冒烟测试') {
            steps { bat "${PYTHON} -m pytest -m smoke" }
        }
        stage('全量回归') {
            steps { bat "${PYTHON} -m pytest --alluredir reports/allure-results --clean-alluredir" }
        }
        stage('生成 Allure 报告') {
            steps { bat "allure generate reports/allure-results -o reports/allure-report --clean" }
        }
    }
    post {
        always {
            powershell "if (Test-Path server.pid) { \$id = Get-Content server.pid; Stop-Process -Id \$id -Force -ErrorAction SilentlyContinue }"
        }
        failure {
            echo '回归测试存在失败用例,请查看 Allure 报告'
        }
    }
}
