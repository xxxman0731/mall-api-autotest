"""加密工具:MD5 计算(教学演示用,生产环境请勿使用 MD5 存储密码)。"""
import hashlib


def md5_password(raw: str, salt: str = "mall-salt-2025") -> str:
    return hashlib.md5((salt + raw).encode("utf-8")).hexdigest()
