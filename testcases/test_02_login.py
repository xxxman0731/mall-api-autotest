"""登录接口测试:数据驱动,用例定义在 testdata/login.yaml。"""
import pytest

from common.asserts import assert_biz_code, assert_status
from common.data_loader import load_yaml

login_cases = load_yaml("login.yaml")["cases"]


@pytest.mark.regression
@pytest.mark.parametrize("case", login_cases, ids=[c["case_id"] for c in login_cases])
def test_login(api, db, login_user, case):
    resp = api.post("/api/login", json=case["request"])
    expected = case["expected"]
    assert_status(resp, expected["status_code"])
    if "biz_code" in expected:
        assert_biz_code(resp, expected["biz_code"])
    body = resp.json()
    if expected.get("token_exists"):
        assert body["data"]["token"], "登录成功应返回非空 token"
    if expected.get("user_id_matches_db"):
        row = db.query_one("SELECT id FROM users WHERE username = ?", (case["request"]["username"],))
        assert row is not None
        assert body["data"]["user_id"] == row["id"], "响应 user_id 与数据库不一致"
