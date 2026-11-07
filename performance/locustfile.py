"""Locust 压测脚本:模拟用户登录后浏览商品、下单。

运行方式:
    locust -f performance/locustfile.py --host http://127.0.0.1:5000
    浏览器打开 http://127.0.0.1:8089 配置并发数与增速,开始压测
"""
from locust import HttpUser, between, task


class MallUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        username = "perf_user"
        password = "Test123456"
        with self.client.post(
            "/api/register", json={"username": username, "password": password}, catch_response=True
        ) as resp:
            if resp.status_code in (201, 409):
                resp.success()  # 409 表示压测账号已存在,属于正常分支
            else:
                resp.failure("压测账号注册失败: {}".format(resp.text))
        with self.client.post(
            "/api/login", json={"username": username, "password": password}, catch_response=True
        ) as resp:
            if resp.status_code != 200:
                resp.failure("压测账号登录失败: {}".format(resp.text))
            else:
                self.token = resp.json()["data"]["token"]
                self.headers = {"Authorization": "Bearer {}".format(self.token)}

    @task(3)
    def browse_products(self):
        with self.client.get("/api/products", catch_response=True) as resp:
            if resp.status_code != 200 or resp.json().get("code") != 0:
                resp.failure("商品列表接口异常: {} {}".format(resp.status_code, resp.text[:200]))

    @task(1)
    def create_order(self):
        with self.client.post(
            "/api/orders", json={"product_id": 2, "quantity": 1}, headers=self.headers, catch_response=True
        ) as resp:
            if resp.status_code == 400 and resp.json().get("code") == 1009:
                resp.success()  # 库存不足属于业务正常分支,不计为失败
            elif resp.status_code != 201:
                resp.failure("下单接口异常: {} {}".format(resp.status_code, resp.text[:200]))
