"""阶段 9 测试：任务队列 + Worker 完整链路。

用法：python tests\\test_queue.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.queue.service import get_status, submit_task  # noqa: E402
from src.queue.task_queue import dequeue_task, get_task_status  # noqa: E402
from src.queue.worker import _execute_task  # noqa: E402


def main():
    # 1. 提交任务（同步 API 层：入队即返回）
    wid = submit_task("000001.SZ", "20250101", "20250630")
    print(f"[1] submit_task -> workflow_id={wid}")
    print(f"[2] 入队后状态: {get_task_status(wid)}")  # 期望 pending

    # 2. 出队（Worker 消费）
    task = dequeue_task(timeout=1)
    print(f"[3] dequeue_task -> ts_code={task['ts_code']}")

    # 3. 执行（完整三阶段，含 LLM 推理，较慢）
    result = _execute_task(task)
    print(f"[4] 执行后状态: {get_task_status(wid)}")  # 期望 completed
    rec = result.get("recommendation", {})
    print(f"[5] 推荐: action={rec.get('action')}, score={rec.get('score')}")

    # 4. 状态查询
    status = get_status(wid)
    print(f"[6] get_status: status={status['status']}, has_result={status['result'] is not None}")
    print("ALL OK")


if __name__ == "__main__":
    main()
