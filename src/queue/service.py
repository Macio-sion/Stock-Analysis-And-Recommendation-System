"""任务提交服务（同步 API 层）：提交任务入队，立即返回 workflow_id。"""
import uuid

from src.persistence.database import SessionLocal
from src.persistence.repository import create_workflow
from src.queue.task_queue import enqueue_task, get_task_result, get_task_status


def submit_task(
    ts_code: str,
    start_date: str,
    end_date: str,
    symbol: str = "",
    strategy_type: str | None = None,
    strategy_config: dict | None = None,
) -> str:
    """提交推荐任务：创建 workflow 实例 + 入队，立即返回 workflow_id。"""
    workflow_id = uuid.uuid4().hex
    db = SessionLocal()
    try:
        create_workflow(db, workflow_id, ts_code, strategy_type)
    finally:
        db.close()

    task = {
        "workflow_id": workflow_id,
        "ts_code": ts_code,
        "symbol": symbol or ts_code,
        "start_date": start_date,
        "end_date": end_date,
        "strategy_type": strategy_type,
        "strategy_config": strategy_config,
    }
    enqueue_task(task)
    return workflow_id


def get_status(workflow_id: str) -> dict:
    """查询任务状态与结果。"""
    return {
        "workflow_id": workflow_id,
        "status": get_task_status(workflow_id),
        "result": get_task_result(workflow_id),
    }
