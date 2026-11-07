"""测试数据加载:测试数据(YAML)与测试代码分离。"""
import os

import yaml

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTDATA_DIR = os.path.join(ROOT_DIR, "testdata")


def load_yaml(filename: str) -> dict:
    path = os.path.join(TESTDATA_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
