"""注册接口测试:数据驱动,用例定义在 testdata/register.yaml。"""
import pytest

from common.asserts import assert_biz_code, assert_msg_contains, assert_status
from common.data_loader import load_yaml
from common.encrypt import md5_password

register_cases = load_yaml("register.yaml")["cases"]


@pytest.mark.regression
@pytest.mark.parametrize("case", register_cases, ids=[c["case_id"] for c in register_cases])
def test_register(api, db, env_config, case):
    pre = case.get("pre_register")
    if pre:
        api.post("/api/register", json=pre)

    resp = api.post("/api/register", json=case["request"])
    expected = case["expected"]
    assert_status(resp, expected["status_code"])
    if "biz_code" in expected:
        assert_biz_code(resp, expected["biz_code"])
    if "msg_contains" in expected:
        assert_msg_contains(resp, expected["msg_contains"])

    db_check = expected.get("db_check")
    if db_check:
        row = db.query_one(db_check["sql"], tuple(db_check["params"]))
        if db_check.get("expect_exists"):
            assert row is not None, "注册成功后 users 表应存在该用户记录"
        if db_check.get("password_md5_of"):
            salt = env_config["password_salt"]
            assert row["password"] == md5_password(db_check["password_md5_of"], salt), "数据库密码应为加盐 MD5"
        if db_check.get("phone_equals") is not None:
            assert row["phone"] == db_check["phone_equals"], "数据库 phone 字段与注册信息不一致"
