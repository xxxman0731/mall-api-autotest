"""冒烟测试:部署/提测后快速验证核心链路可用。

运行方式: pytest -m smoke
"""
import pytest


@pytest.mark.smoke
def test_health(api):
    resp = api.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["code"] == 0


@pytest.mark.smoke
def test_smoke_login_and_browse(api, login_user):
    resp = api.get("/api/products")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1


@pytest.mark.smoke
def test_smoke_create_order(api, auth_headers):
    resp = api.post("/api/orders", json={"product_id": 2, "quantity": 1}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["data"]["order_no"]
