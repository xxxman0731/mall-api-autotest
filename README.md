# 电商接口自动化测试框架(mall-api-autotest)

一个完整的接口自动化测试实战项目,包含:

- 被测系统:Flask + SQLite 电商 Demo(注册 / 登录 / 商品 / 下单 / 订单查询)
- 测试框架:Python + Pytest + Requests,数据驱动,分层架构
- 落库校验:接口断言之外,直接查询数据库校验数据一致性
- 测试报告:Allure(失败用例自动归档日志)
- 性能测试:JMeter 脚本 + Locust 脚本
- CI 集成:Jenkinsfile(定时回归 + 冒烟测试)

## 项目亮点

- 分层架构:测试代码 / 测试数据 / 公共组件 / 配置完全分离
- 数据驱动:在 YAML 中新增用例即可扩展,无需修改测试代码
- 落库校验:验证"接口返回成功"与"数据真实落库"的一致性
- 失败定位:失败用例自动记录异常信息到 logs/failures/
- 全链路:冒烟 -> 回归 -> 报告 -> CI 定时执行

## 技术栈

| 分类 | 技术 |
| --- | --- |
| 语言 | Python 3.8+ |
| 测试框架 | Pytest(参数化 / fixture / marker / hook) |
| HTTP | Requests(统一封装:日志、超时、token 管理) |
| 测试数据 | YAML 数据驱动 |
| 数据库校验 | SQLite(默认) / MySQL(PyMySQL,可选) |
| 测试报告 | Allure |
| 被测系统 | Flask + SQLite |
| 性能测试 | JMeter / Locust |
| CI | Jenkinsfile |

## 目录结构

```text
mall-api-autotest
├── conftest.py              # 全局 fixture 与失败用例归档钩子
├── pytest.ini               # pytest 配置(标记、路径)
├── requirements.txt         # 依赖清单
├── Jenkinsfile              # CI 流水线
├── config/
│   └── config.yaml          # 环境配置(地址、数据库、测试账号)
├── common/                  # 公共组件层
│   ├── request_client.py    # HTTP 请求封装
│   ├── db_helper.py         # 数据库操作封装(SQLite/MySQL)
│   ├── data_loader.py       # YAML 测试数据加载
│   ├── encrypt.py           # MD5 工具
│   ├── asserts.py           # 通用断言
│   └── logger.py            # 日志
├── testdata/                # 测试数据层(用例与数据分离)
│   ├── register.yaml        # 注册接口用例
│   ├── login.yaml           # 登录接口用例
│   ├── product.yaml         # 商品接口用例
│   └── order.yaml           # 下单接口用例
├── testcases/               # 测试用例层
│   ├── test_00_smoke.py     # 冒烟测试
│   ├── test_01_register.py  # 注册
│   ├── test_02_login.py     # 登录
│   ├── test_03_product.py   # 商品
│   ├── test_04_order.py     # 下单 / 订单
│   └── test_05_db_validation.py  # 落库一致性专项
├── mock_server/             # 被测系统(Demo 后端)
│   ├── app.py               # 服务入口
│   ├── init_db.py           # 手动初始化数据库
│   ├── optimize.py          # 慢 SQL 索引优化演示
│   └── README.md            # 接口文档
├── performance/             # 性能测试
│   ├── order_api.jmx        # JMeter 压测脚本
│   └── locustfile.py        # Locust 压测脚本
├── db/
│   └── mall.sql             # MySQL 版被测库脚本(可选)
├── scripts/
│   ├── start_server.ps1     # 启动被测服务
│   ├── stop_server.ps1      # 停止被测服务
│   └── run_all.ps1          # 一键运行:启动-测试-报告-停止
├── logs/                    # 运行日志与失败归档(自动生成)
└── reports/                 # Allure 结果与报告(自动生成)
```

## 环境要求

- Python 3.8 及以上版本
- 核心依赖:requests / flask / PyYAML / pytest

```bash
python -m pip install -r requirements.txt
```

## 快速开始

### 1. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 2. 启动被测服务(终端一)

```bash
python mock_server/app.py
```

看到提示"被测服务已启动: http://127.0.0.1:5000"即成功,保持窗口运行。

### 3. 运行测试(终端二)

```bash
# 冒烟测试(快速验证核心链路)
python -m pytest -m smoke

# 全量回归
python -m pytest

# 全量回归 + 生成 Allure 结果
python -m pytest --alluredir reports/allure-results --clean-alluredir
```

### 4. 一键运行(Windows)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
```

### 5. 生成并查看 Allure 报告

需先安装 allure 命令行(从 allurereport.org 下载,解压后将 bin 目录加入 PATH):

```bash
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

## 用例设计说明

用例设计综合使用等价类划分、边界值分析、场景法与异常场景设计。

| 被测字段 | 有效等价类 | 无效等价类 |
| --- | --- | --- |
| username | 3-20 位字母数字下划线 | 2 位 / 21 位 / 含特殊字符 / 空串 / 重复 |
| password | 大于等于 6 位 | 5 位 / 缺失 / 空串 |
| phone | 11 位数字 / 不传(可选) | 10 位 / 含字母 |
| quantity | 1-99 整数 | 0 / 负数 / 100 / 非数字 / 缺失 |
| product_id | 存在的商品 id | 不存在 / 缺失 / 0 / 负数 / 非数字 |
| token | 有效 token | 缺失 / 无效 |

当前用例数 45+,接口覆盖:注册、登录、商品列表、商品详情、下单、订单列表、订单详情。

## 框架设计

### 分层结构

```text
config(环境配置) -> common(请求/DB/日志/断言封装) -> testdata(用例数据)
        -> testcases(用例逻辑) <- conftest(fixture 装配)
```

### 关键机制

- 会话级 fixture:自动注册并登录主测试账号,统一管理 token
- 数据重置:每次测试会话开始前清理测试数据并重置库存,用例可重复执行
- 请求响应日志:每次请求与响应都记录到 logs/,排查问题有据可依
- 失败归档:失败用例自动写入 logs/failures/*.json,包含异常信息

## 数据库落库校验

接口测试为什么要查数据库?因为"接口返回成功"不等于"数据正确落库"。

- 注册成功后,校验 users 表存在记录,且密码为加盐 MD5、phone 字段一致
- 下单成功后,校验 orders 表存在订单记录,且:
  - 库存扣减数量 = 下单数量
  - total_price = price * quantity
  - 订单号全局唯一
- 库存不足时,校验库存未被扣减

## 性能测试

### JMeter

1. 启动被测服务
2. 用 JMeter 打开 performance/order_api.jmx
3. 点击运行,查看聚合报告(默认 50 并发、预热 5 秒、循环 10 轮)

脚本内置:登录 -> 正则提取 token -> 携带 token 下单 -> 断言下单成功。

### Locust

```bash
locust -f performance/locustfile.py --host http://127.0.0.1:5000
```

浏览器打开 http://127.0.0.1:8089,配置并发数与增速后开始压测。

### 慢 SQL 优化演示

运行 `python mock_server/optimize.py` 为 orders 高频查询字段添加索引,用
`EXPLAIN QUERY PLAN` 对比优化前后执行计划(SCAN -> SEARCH),这是面试中
"性能瓶颈定位与优化"故事的真实素材。

## CI 集成

Jenkinsfile 提供:每日凌晨 2 点定时回归;冒烟测试;全量回归 + Allure 报告。

接入步骤:Jenkins 新建流水线任务 -> 配置 Git 仓库 -> 流水线定义选择
"Pipeline script from SCM" -> 指定 Jenkinsfile。

## 如何扩展到 200+ 用例

每个接口按五个维度扩展:正常场景 / 边界值 / 异常参数 / 权限控制 / 数据一致性。

- 新增用例只需在 testdata/*.yaml 中追加条目,无需改测试代码
- 可在 mock_server 中新增接口(购物车、支付、退款、地址管理),再写对应用例
- 可为商品列表增加分页、搜索、排序等参数用例

## 切换 MySQL 校验(可选)

1. 安装 MySQL,导入 db/mall.sql
2. 修改 config/config.yaml:database.type 改为 mysql,填写连接信息
3. 安装 PyMySQL:pip install pymysql

## 面试准备

见 docs/面试准备.md,包含 15 个高频追问与答题思路。

## 注意事项

- 密码使用 MD5 加盐仅用于教学演示,生产环境应使用 bcrypt / argon2
- token 存储于内存,服务重启后失效
- 本项目为学习与求职展示用途,请勿用于生产环境
