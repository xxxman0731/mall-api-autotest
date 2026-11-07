"""下单/订单接口测试:数据驱动 + 场景用例。"""
import pytest

from common.asserts import assert_biz_code, assert_status
from common.data_loader import load_yaml

order_cases = load_yaml("order.yaml")["cases"]


@pytest.mark.regression
@pytest.mark.parametrize("case", order_cases, ids=[c["case_id"] for c in order_cases])
def test_create_order(api, db, auth_headers, case):
    token = case.get("token")
    if token:
        headers = {"Authorization": "Bearer " + token}
    elif case.get("auth", True):
        headers = dict(auth_headers)
    else:
        headers = {}

    req = case["request"]
    expected = case["expected"]
    stock_before = None
    db_check = expected.get("db_check") or {}
    if db_check.get("stock_decrement"):
        stock_before = db.query_one("SELECT stock FROM products WHERE id = ?", (req["product_id"],))["stock"]

    resp = api.post("/api/orders", json=req, headers=headers)
    assert_status(resp, expected["status_code"])
    if "biz_code" in expected:
        assert_biz_code(resp, expected["biz_code"])

    if not db_check:
        return
    body = resp.json()
    order_no = body["data"]["order_no"]
    if db_check.get("order_record"):
        row = db.query_one("SELECT * FROM orders WHERE order_no = ?", (order_no,))
        assert row is not None, "下单成功后 orders 表应存在订单记录"
        assert row["product_id"] == req["product_id"], "订单商品与请求不一致"
        assert row["quantity"] == req["quantity"], "订单数量与请求不一致"
    if db_check.get("total_price"):
        price = db.query_one("SELECT price FROM products WHERE id = ?", (req["product_id"],))["price"]
        assert abs(body["data"]["total_price"] - round(price * req["quantity"], 2)) < 0.01, "订单金额计算错误"
    if db_check.get("stock_decrement"):
        stock_after = db.query_one("SELECT stock FROM products WHERE id = ?", (req["product_id"],))["stock"]
        assert stock_before - req["quantity"] == stock_after, "库存扣减数量不正确"


@pytest.mark.regression
def test_order_insufficient_stock(api, db, auth_headers):
    """库存不足:下单失败且库存不被扣减。"""
    db.execute("INSERT INTO products(name, price, stock, status) VALUES(?,?,?,1)", ("限量测试商品", 1.0, 1))
    product = db.query_one("SELECT id FROM products WHERE name = '限量测试商品'")
    resp = api.post("/api/orders", json={"product_id": product["id"], "quantity": 2}, headers=auth_headers)
    assert resp.status_code == 400
    assert resp.json()["code"] == 1009
    after = db.query_one("SELECT stock FROM products WHERE id = ?", (product["id"],))
    assert after["stock"] == 1, "库存不足时库存不应被扣减"


@pytest.mark.regression
def test_order_isolation_between_users(api, auth_headers):
    """订单隔离:只能查看自己的订单,越权访问他人订单返回 403。"""
    resp = api.post("/api/orders", json={"product_id": 2, "quantity": 1}, headers=auth_headers)
    order_no = resp.json()["data"]["order_no"]

    other = "auto_other_user"
    api.post("/api/register", json={"username": other, "password": "Test123456"})
    login_resp = api.post("/api/login", json={"username": other, "password": "Test123456"})
    other_headers = {"Authorization": "Bearer " + login_resp.json()["data"]["token"]}

    list_resp = api.get("/api/orders", headers=other_headers)
    order_nos = [item["order_no"] for item in list_resp.json()["data"]]
    assert order_no not in order_nos, "他人的订单不应出现在自己的订单列表中"

    detail_resp = api.get("/api/orders/" + order_no, headers=other_headers)
    assert detail_resp.status_code == 403
    assert detail_resp.json()["code"] == 1011


@pytest.mark.regression
def test_order_detail_success(api, db, auth_headers):
    resp = api.post("/api/orders", json={"product_id": 2, "quantity": 3}, headers=auth_headers)
    data = resp.json()["data"]
    detail = api.get("/api/orders/" + data["order_no"], headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["order_no"] == data["order_no"]
    assert detail.json()["data"]["quantity"] == 3
    row = db.query_one("SELECT quantity FROM orders WHERE order_no = ?", (data["order_no"],))
    assert row["quantity"] == 3, "订单详情与数据库记录不一致"


@pytest.mark.regression
def test_order_detail_not_found(api, auth_headers):
    resp = api.get("/api/orders/MALL_NOT_EXIST", headers=auth_headers)
    assert resp.status_code == 404
    assert resp.json()["code"] == 1010
