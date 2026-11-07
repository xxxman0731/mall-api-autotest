"""手动初始化数据库(也可直接运行 app.py,启动时会自动初始化)。"""
from app import init_db


if __name__ == "__main__":
    init_db()
    print("数据库初始化完成: mock_server/mall.db")
