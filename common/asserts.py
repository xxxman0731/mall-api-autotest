"""通用断言封装,失败信息更直观。"""


def assert_status(resp, expected: int):
    assert resp.status_code == expected, (
        "HTTP 状态码不符:期望 {},实际 {},响应: {}".format(expected, resp.status_code, resp.text[:500])
    )


def assert_biz_code(resp, expected: int):
    body = resp.json()
    assert body.get("code") == expected, (
        "业务码不符:期望 {},实际 {},响应: {}".format(expected, body.get("code"), body)
    )


def assert_msg_contains(resp, keyword: str):
    body = resp.json()
    assert keyword in str(body.get("msg", "")), (
        "响应 msg 未包含 '{}',实际: {}".format(keyword, body.get("msg"))
    )
