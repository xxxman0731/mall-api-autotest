"""数据库落库一致性校验专项用例。"""
import pytest

from common.encrypt import md5_password


@pytest.mark.regression
def test_db_password_stored_as_salted_md5(api, db, env_config):
    api.post("/api/register", json={"username": "auto_db_001", "password": "Test123456"})
    row = db.query_one("SELECT password FROM users WHERE username = ?", ("auto_db_001",))
    assert row is not None, "注册后数据库应有用户记录"
    assert row["password"] == md5_password("Test123456", env_config["password_salt"]), "密码应为加盐 MD5"
    assert row["password"] != "Test123456", "数据库中不应存储明文密码"


@pytest.mark.regression
def test_db_stock_consistency(api, db, auth_headers):
    before = db.query_one("SELECT stock FROM products WHERE id = ?", (2,))["stock"]
    resp = api.post("/api/orders", json={"product_id": 2, "quantity": 5}, headers=auth_headers)
    assert resp.status_code == 201
    after = db.query_one("SELECT stock FROM products WHERE id = ?", (2,))["stock"]
    assert before - after == 5, "下单前后库存扣减数量不一致"


@pytest.mark.regression
def test_db_order_amount_consistency(api, db, auth_headers):
    price = db.query_one("SELECT price FROM products WHERE id = ?", (2,))["price"]
    resp = api.post("/api/orders", json={"product_id": 2, "quantity": 4}, headers=auth_headers)
    data = resp.json()["data"]
    row = db.query_one("SELECT total_price FROM orders WHERE order_no = ?", (data["order_no"],))
    assert abs(row["total_price"] - round(price * 4, 2)) < 0.01, "订单金额与单价*数量不一致"


@pytest.mark.regression
def test_db_order_no_unique(api, auth_headers):
    r1 = api.post("/api/orders", json={"product_id": 2, "quantity": 1}, headers=auth_headers)
    r2 = api.post("/api/orders", json={"product_id": 2, "quantity": 1}, headers=auth_headers)
    assert r1.json()["data"]["order_no"] != r2.json()["data"]["order_no"], "订单号应唯一"


@pytest.mark.regression
def test_db_register_user_fields_persisted(api, db):
    api.post("/api/register", json={"username": "auto_db_002", "password": "Test123456", "phone": "13900000002"})
    row = db.query_one("SELECT username, phone FROM users WHERE username = ?", ("auto_db_002",))
    assert row is not None
    assert row["phone"] == "13900000002", "手机号字段与注册信息不一致"
