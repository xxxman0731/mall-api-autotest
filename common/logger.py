"""日志模块:统一控制台与文件日志输出。"""
import logging
import os
import sys
from datetime import datetime


def setup_logger(log_dir: str = "logs", name: str = "malltest") -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler = logging.FileHandler(
        os.path.join(log_dir, datetime.now().strftime("%Y%m%d.log")), encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger
