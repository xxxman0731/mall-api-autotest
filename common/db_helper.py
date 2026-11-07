"""数据库操作封装:支持 SQLite(默认)与 MySQL(PyMySQL)。"""
import sqlite3


class DBHelper:
    def __init__(self, config: dict):
        db_type = config.get("type", "sqlite")
        if db_type == "mysql":
            import pymysql  # 延迟导入:不使用 MySQL 时无需安装

            mysql = config.get("mysql", {})
            self.conn = pymysql.connect(
                host=mysql.get("host", "127.0.0.1"),
                port=int(mysql.get("port", 3306)),
                user=mysql.get("user", "root"),
                password=mysql.get("password", ""),
                database=mysql.get("dbname", "mall"),
                charset=mysql.get("charset", "utf8mb4"),
            )
            self._mysql = True
        else:
            self.conn = sqlite3.connect(config.get("sqlite_path", "mock_server/mall.db"))
            self.conn.row_factory = sqlite3.Row
            self._mysql = False

    def _run(self, sql: str, params: tuple):
        if self._mysql:
            sql = sql.replace("?", "%s")
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor

    def query(self, sql: str, params: tuple = ()) -> list:
        cursor = self._run(sql, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in rows]

    def query_one(self, sql: str, params: tuple = ()):
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def execute(self, sql: str, params: tuple = ()) -> None:
        self._run(sql, params)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
