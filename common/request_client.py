"""HTTP 请求封装:统一日志、超时与 token 管理。"""
import json
import logging

import requests

log = logging.getLogger("malltest")

DEFAULT_HEADERS = {"Content-Type": "application/json"}


class ApiClient:
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def set_token(self, token: str) -> None:
        """设置 Bearer token,后续请求自动携带。"""
        self.session.headers["Authorization"] = "Bearer {}".format(token)

    def clear_token(self) -> None:
        self.session.headers.pop("Authorization", None)

    def request(self, method: str, path: str, **kwargs):
        url = self.base_url + path
        kwargs.setdefault("timeout", self.timeout)
        payload = kwargs.get("json") or kwargs.get("params") or {}
        log.info("请求 %s %s %s", method.upper(), url, json.dumps(payload, ensure_ascii=False))
        resp = self.session.request(method, url, **kwargs)
        try:
            body = resp.json()
        except ValueError:
            body = resp.text
        log.info("响应 %s %s", resp.status_code, json.dumps(body, ensure_ascii=False)[:500])
        return resp

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)
