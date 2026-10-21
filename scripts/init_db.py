"""初始化数据库：执行 schema.sql 创建表与索引。"""
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，保证能导入 config 模块
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2  # noqa: E402

from config.settings import settings  # noqa: E402

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def init_db() -> None:
    """执行 schema.sql（幂等，可重复执行）。"""
    sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = psycopg2.connect(settings.database_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
    finally:
        conn.close()
    print("数据库表与索引创建完成")


if __name__ == "__main__":
    init_db()
