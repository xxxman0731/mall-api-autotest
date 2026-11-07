"""慢 SQL 优化演示:为高频查询字段添加索引。

优化前:按 user_id / product_id 查询走全表扫描(EXPLAIN QUERY PLAN 显示 SCAN)
优化后:走索引(显示 SEARCH USING INDEX)

对比方式:
    EXPLAIN QUERY PLAN SELECT * FROM orders WHERE user_id = 1;
"""
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mall.db")


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_orders_product_id ON orders(product_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)")
    conn.commit()
    conn.close()
    print("索引创建完成: idx_orders_user_id / idx_orders_product_id / idx_products_name")


if __name__ == "__main__":
    main()
