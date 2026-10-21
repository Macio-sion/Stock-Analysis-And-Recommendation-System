"""Redis 任务队列：入队/出队 + 任务状态/结果管理。

使用 Redis List 作为 FIFO 队列（LPUSH 入队 / BRPOP 阻塞出队），
String 存储任务状态与结果。
"""
import json

from src.data.cache import get_redis

QUEUE_KEY = "task:queue"
STATUS_PREFIX = "task:status:"
RESULT_PREFIX = "task:result:"


def enqueue_task(task: dict) -> bool:
    """任务入队（LPUSH），并初始化状态为 pending。"""
    r = get_redis()
    workflow_id = task["workflow_id"]
    r.lpush(QUEUE_KEY, json.dumps(task, ensure_ascii=False))
    r.set(f"{STATUS_PREFIX}{workflow_id}", "pending")
    return True


def dequeue_task(timeout: int = 0) -> dict | None:
    """阻塞出队（BRPOP）。timeout=0 表示永久阻塞；单位秒。"""
    r = get_redis()
    item = r.brpop(QUEUE_KEY, timeout=timeout)
    if not item:
        return None
    _, raw = item
    return json.loads(raw)


def set_task_status(workflow_id: str, status: str) -> None:
    """设置任务状态（pending/running/completed/failed）。"""
    get_redis().set(f"{STATUS_PREFIX}{workflow_id}", status)


def get_task_status(workflow_id: str) -> str | None:
    """查询任务状态。"""
    return get_redis().get(f"{STATUS_PREFIX}{workflow_id}")


def set_task_result(workflow_id: str, result: dict) -> None:
    """保存任务结果（JSON 序列化）。"""
    get_redis().set(f"{RESULT_PREFIX}{workflow_id}", json.dumps(result, ensure_ascii=False))


def get_task_result(workflow_id: str) -> dict | None:
    """读取任务结果。"""
    raw = get_redis().get(f"{RESULT_PREFIX}{workflow_id}")
    return json.loads(raw) if raw else None
