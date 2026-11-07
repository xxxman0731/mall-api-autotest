"""全局 fixture 与 pytest 钩子。

- env_config: 读取 config/config.yaml
- api: HTTP 客户端封装
- db: 数据库操作封装(落库校验)
- login_user / auth_headers: 会话级主测试账号
- 失败用例自动记录到 logs/failures/
"""
import json
import os
import sys
import time

import pytest
import yaml

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT_DIR)

from common.db_helper import DBHelper
from common.logger import setup_logger
from common.request_client import ApiClient

logger = setup_logger(log_dir=os.path.join(ROOT_DIR, "logs"))


@pytest.fixture(scope="session")
def env_config():
    with open(os.path.join(ROOT_DIR, "config", "config.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def api(env_config):
    return ApiClient(env_config["base_url"])


@pytest.fixture(scope="session")
def db(env_config):
    helper = DBHelper(env_config["database"])
    yield helper
    helper.close()


@pytest.fixture(scope="session", autouse=True)
def reset_test_data(db):
    """测试会话开始前清空测试数据并重置库存,保证用例可重复执行。"""
    db.execute("DELETE FROM orders")
    db.execute("DELETE FROM users")
    db.execute("DELETE FROM products WHERE name = '限量测试商品'")
    seeds = [
        ("iPhone 15 Pro", 100),
        ("小米手环 9", 500),
        ("罗技鼠标 MX Master 3S", 200),
        ("机械键盘 K870", 150),
        ("显示器 27寸 4K", 80),
    ]
    for name, stock in seeds:
        db.execute("UPDATE products SET stock = ? WHERE name = ?", (stock, name))
    yield


@pytest.fixture(scope="session")
def login_user(api, db, env_config):
    """主测试账号:自动注册并登录,返回 token 等信息。"""
    username = env_config["test_user"]["username"]
    password = env_config["test_user"]["password"]
    if not db.query_one("SELECT id FROM users WHERE username = ?", (username,)):
        resp = api.post("/api/register", json={"username": username, "password": password})
        assert resp.status_code in (200, 201, 409), "预置账号注册失败: {}".format(resp.text)
    resp = api.post("/api/login", json={"username": username, "password": password})
    assert resp.status_code == 200, "预置账号登录失败: {}".format(resp.text)
    data = resp.json()["data"]
    return {"username": username, "password": password, "token": data["token"], "user_id": data["user_id"]}


@pytest.fixture(scope="session")
def auth_headers(login_user):
    return {"Authorization": "Bearer {}".format(login_user["token"])}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """失败用例自动记录异常信息,方便问题定位。"""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        fail_dir = os.path.join(ROOT_DIR, "logs", "failures")
        os.makedirs(fail_dir, exist_ok=True)
        info = {
            "case": item.nodeid,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "exception": str(call.excinfo.value) if call.excinfo else "",
        }
        safe_name = item.name.replace("/", "_").replace("\\", "_")
        with open(os.path.join(fail_dir, "{}.json".format(safe_name)), "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        logger.error("失败用例已记录: %s", item.nodeid)
