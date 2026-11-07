"""商品接口测试:数据驱动,用例定义在 testdata/product.yaml。"""
import pytest

from common.asserts import assert_biz_code, assert_status
from common.data_loader import load_yaml

product_cases = load_yaml("product.yaml")["cases"]


@pytest.mark.regression
@pytest.mark.parametrize("case", product_cases, ids=[c["case_id"] for c in product_cases])
def test_product(api, db, case):
    req = case["request"]
    if req:
        resp = api.get("/api/products/{}".format(req["product_id"]))
    else:
        resp = api.get("/api/products")

    expected = case["expected"]
    assert_status(resp, expected["status_code"])

    body = None
    try:
        body = resp.json()
    except ValueError:
        body = None

    if "biz_code" in expected:
        assert_biz_code(resp, expected["biz_code"])
    if body is None:
        return

    data = body.get("data")
    if expected.get("list_min_length"):
        assert isinstance(data, list) and len(data) >= expected["list_min_length"], "商品列表长度不足"
    if expected.get("item_fields"):
        for field in expected["item_fields"]:
            assert field in data[0], "商品字段缺失: {}".format(field)
    if expected.get("contains_name"):
        assert any(item["name"] == expected["contains_name"] for item in data), "商品列表缺少指定商品"

    db_check = expected.get("db_check")
    if db_check:
        row = db.query_one(db_check["sql"], tuple(db_check["params"]))
        assert row is not None, "数据库中不存在该商品"
        for field in db_check["compare_fields"]:
            assert data[field] == row[field], "字段 {} 响应与数据库不一致".format(field)
