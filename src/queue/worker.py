"""Worker：消费任务队列，执行三阶段推荐工作流。"""
from src.persistence.database import SessionLocal
from src.persistence.repository import update_workflow_status
from src.queue.task_queue import dequeue_task, set_task_result, set_task_status
from src.workflow.graph import graph


def _execute_task(task: dict) -> dict:
    """执行单个任务：graph.invoke 三阶段工作流，并更新状态与结果。"""
    workflow_id = task["workflow_id"]
    set_task_status(workflow_id, "running")

    db = SessionLocal()
    try:
        update_workflow_status(db, workflow_id, "running")
        result = graph.invoke(
            {
                "workflow_id": workflow_id,
                "ts_code": task["ts_code"],
                "symbol": task.get("symbol") or task["ts_code"],
                "start_date": task["start_date"],
                "end_date": task["end_date"],
                "strategy_config": task.get("strategy_config") or {},
            }
        )
        set_task_result(workflow_id, result)
        set_task_status(workflow_id, "completed")
        update_workflow_status(db, workflow_id, "completed")
        return result
    except Exception as exc:  # noqa: BLE001
        set_task_status(workflow_id, "failed")
        set_task_result(workflow_id, {"error": str(exc)})
        update_workflow_status(db, workflow_id, "failed", error_message=str(exc))
        raise
    finally:
        db.close()


def run_worker() -> None:
    """Worker 主循环：永久阻塞消费队列，逐个执行任务。"""
    while True:
        task = dequeue_task(timeout=0)
        if task is None:
            continue
        try:
            _execute_task(task)
        except Exception:
            # 失败状态已在 _execute_task 中记录，继续处理下一条
            continue
