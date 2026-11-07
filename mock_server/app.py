"""电商 Demo 被测系统:Flask + SQLite。

提供注册 / 登录 / 商品 / 下单 / 订单查询接口,供接口自动化测试练习使用。

启动方式: python mock_server/app.py
接口文档见 mock_server/README.md
"""
import hashlib
import os
import random
import re
import secrets
import sqlite3
import time
from datetime import datetime

from flask import Flask, g, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "mall.db")
SALT = "mall-salt-2025"
TOKEN_TTL = 7200  # token 有效期(秒)

app = Flask(__name__)
TOKENS = {}  # 内存 token 表: {token: {"user_id": int, "expire": float}}

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
PHONE_RE = re.compile(r"^\d{11}$")

SEED_PRODUCTS = [
    ("iPhone 15 Pro", 8999.0, 100),
    ("小米手环 9", 249.0, 500),
    ("罗技鼠标 MX Master 3S", 699.0, 200),
    ("机械键盘 K870", 399.0, 150),
    ("显示器 27寸 4K", 1999.0, 80),
]


def ok(data=None, msg="success", code=0):
    return jsonify({"code": code, "msg": msg, "data": data})


def fail(msg, code, status_code):
    return jsonify({"code": code, "msg": msg, "data": None}), status_code


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def md5_password(raw):
    return hashlib.md5((SALT + raw).encode("utf-8")).hexdigest()


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def issue_token(user_id):
    token = secrets.token_hex(16)
    TOKENS[token] = {"user_id": user_id, "expire": time.time() + TOKEN_TTL}
    return token


def current_user_id():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[len("Bearer "):]
    info = TOKENS.get(token)
    if not info or info["expire"] < time.time():
        return None
    return info["user_id"]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            status INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS orders(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            status INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );
        """
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO products(name, price, stock, status) VALUES(?,?,?,1)", SEED_PRODUCTS
        )
    conn.commit()
    conn.close()


@app.get("/")
def index():
    """商城前端页面(静态文件托管)。"""
    return app.send_static_file("index.html")


@app.get("/api/health")
def health():
    return ok({"status": "up", "time": now_str()})


@app.post("/api/register")
def register():
    body = request.get_json(silent=True) or {}
    username = body.get("username")
    password = body.get("password")
    phone = body.get("phone")
    if not username or not password:
        return fail("缺少必填参数 username/password", 400, 400)
    if not isinstance(username, str) or not USERNAME_RE.match(username):
        return fail("用户名需为3-20位字母数字下划线", 1001, 400)
    if not isinstance(password, str) or len(password) < 6:
        return fail("密码长度不能少于6位", 1002, 400)
    if phone is not None and (not isinstance(phone, str) or not PHONE_RE.match(phone)):
        return fail("手机号格式非法,需为11位数字", 1003, 400)
    db = get_db()
    exists = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if exists:
        return fail("用户名已存在", 1004, 409)
    cur = db.execute(
        "INSERT INTO users(username, password, phone, created_at) VALUES(?,?,?,?)",
        (username, md5_password(password), phone, now_str()),
    )
    db.commit()
    return ok({"user_id": cur.lastrowid, "username": username}, "注册成功"), 201


@app.post("/api/login")
def login():
    body = request.get_json(silent=True) or {}
    username = body.get("username")
    password = body.get("password")
    if not username or not password:
        return fail("缺少必填参数 username/password", 400, 400)
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if row is None or row["password"] != md5_password(password):
        return fail("用户名或密码错误", 1005, 401)
    return ok({"token": issue_token(row["id"]), "user_id": row["id"], "username": row["username"]}, "登录成功")


@app.get("/api/products")
def product_list():
    rows = get_db().execute("SELECT id, name, price, stock, status FROM products").fetchall()
    return ok([dict(r) for r in rows])


@app.get("/api/products/<int:pid>")
def product_detail(pid):
    row = get_db().execute(
        "SELECT id, name, price, stock, status FROM products WHERE id = ?", (pid,)
    ).fetchone()
    if row is None:
        return fail("商品不存在", 1006, 404)
    return ok(dict(row))


@app.post("/api/orders")
def create_order():
    user_id = current_user_id()
    if user_id is None:
        return fail("未登录或 token 无效", 1007, 401)
    body = request.get_json(silent=True) or {}
    product_id = body.get("product_id")
    quantity = body.get("quantity")
    if not isinstance(product_id, int) or isinstance(product_id, bool):
        return fail("product_id 必填且为整数", 1008, 400)
    if not isinstance(quantity, int) or isinstance(quantity, bool) or not (1 <= quantity <= 99):
        return fail("quantity 必填且为1-99的整数", 1008, 400)
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        return fail("商品不存在", 1006, 404)
    if product["stock"] < quantity:
        return fail("库存不足", 1009, 400)
    order_no = "MALL" + datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))
    total_price = round(product["price"] * quantity, 2)
    db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
    db.execute(
        "INSERT INTO orders(order_no, user_id, product_id, quantity, total_price, status, created_at) "
        "VALUES(?,?,?,?,?,1,?)",
        (order_no, user_id, product_id, quantity, total_price, now_str()),
    )
    db.commit()
    return ok({"order_no": order_no, "total_price": total_price, "quantity": quantity}, "下单成功"), 201


@app.get("/api/orders")
def order_list():
    user_id = current_user_id()
    if user_id is None:
        return fail("未登录或 token 无效", 1007, 401)
    rows = get_db().execute(
        "SELECT o.order_no, o.product_id, p.name AS product_name, o.quantity, o.total_price, "
        "o.status, o.created_at FROM orders o JOIN products p ON o.product_id = p.id "
        "WHERE o.user_id = ? ORDER BY o.id DESC",
        (user_id,),
    ).fetchall()
    return ok([dict(r) for r in rows])


@app.get("/api/orders/<order_no>")
def order_detail(order_no):
    user_id = current_user_id()
    if user_id is None:
        return fail("未登录或 token 无效", 1007, 401)
    row = get_db().execute("SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()
    if row is None:
        return fail("订单不存在", 1010, 404)
    if row["user_id"] != user_id:
        return fail("无权访问该订单", 1011, 403)
    return ok(dict(row))


if __name__ == "__main__":
    init_db()
    print("被测服务已启动: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
