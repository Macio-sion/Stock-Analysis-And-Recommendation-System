"""第一阶段持久化接口测试：可直接运行验证快照读写与缓存。

用法：.venv\\Scripts\\python.exe tests\\test_persistence.py
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.cache import cache_get, cache_set  # noqa: E402
from src.persistence import repository  # noqa: E402
from src.persistence.database import SessionLocal  # noqa: E402


def main() -> None:
    wid = f"wf_test_{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    try:
        # 1. 创建工作流
        repository.create_workflow(db, wid, "000001.SZ", "价值型")
        print("[1] create_workflow OK")

        # 2. 保存快照
        state = {"trend": "上涨", "score": 72, "indicators": {"rsi": 65}}
        repository.save_snapshot(db, wid, "technical", state, phase="stage1")
        print("[2] save_snapshot OK")

        # 3. 读取最新快照
        snapshot = repository.get_latest_snapshot(db, wid, "technical")
        assert snapshot == state, f"快照不一致: {snapshot}"
        print("[3] get_latest_snapshot OK ->", snapshot)

        # 4. 覆盖写入验证 is_latest
        state2 = {"trend": "下跌", "score": 55}
        repository.save_snapshot(db, wid, "technical", state2, phase="stage1")
        snapshot2 = repository.get_latest_snapshot(db, wid, "technical")
        assert snapshot2 == state2, f"最新快照应为 state2: {snapshot2}"
        print("[4] 覆盖写入 OK ->", snapshot2)

        # 5. Redis 缓存
        cache_set("test:key", "hello", ttl=60)
        val = cache_get("test:key")
        assert val == "hello", f"缓存读写失败: {val}"
        print("[5] cache OK ->", val)

        print("ALL OK")
    finally:
        db.close()


if __name__ == "__main__":
    main()
