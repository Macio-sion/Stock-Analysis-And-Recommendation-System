"""状态存储/读取操作。"""
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from src.persistence.models import AgentStateSnapshot, WorkflowInstance


def create_workflow(db: Session, workflow_id: str, ts_code: str, strategy_type: str | None = None) -> WorkflowInstance:
    """创建工作流实例。"""
    instance = WorkflowInstance(
        workflow_id=workflow_id,
        ts_code=ts_code,
        status="pending",
        strategy_type=strategy_type,
        started_at=datetime.utcnow(),
    )
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def save_snapshot(
    db: Session,
    workflow_id: str,
    agent_name: str,
    state: dict,
    phase: str | None = None,
) -> bool:
    """保存 Agent 状态快照，并将同 Agent 的旧快照 is_latest 置 False。"""
    db.execute(
        update(AgentStateSnapshot)
        .where(
            AgentStateSnapshot.workflow_id == workflow_id,
            AgentStateSnapshot.agent_name == agent_name,
        )
        .values(is_latest=False)
    )
    snapshot = AgentStateSnapshot(
        workflow_id=workflow_id,
        agent_name=agent_name,
        phase=phase,
        state_data=state,
        is_latest=True,
        created_at=datetime.utcnow(),
    )
    db.add(snapshot)
    db.commit()
    return True


def get_latest_snapshot(db: Session, workflow_id: str, agent_name: str) -> dict | None:
    """读取指定 Agent 的最新状态快照。"""
    stmt = (
        select(AgentStateSnapshot)
        .where(
            AgentStateSnapshot.workflow_id == workflow_id,
            AgentStateSnapshot.agent_name == agent_name,
            AgentStateSnapshot.is_latest.is_(True),
        )
        .order_by(AgentStateSnapshot.created_at.desc())
        .limit(1)
    )
    snapshot = db.execute(stmt).scalar_one_or_none()
    return snapshot.state_data if snapshot else None


def update_workflow_status(
    db: Session,
    workflow_id: str,
    status: str,
    error_message: str | None = None,
) -> bool:
    """更新工作流实例状态。"""
    db.execute(
        update(WorkflowInstance)
        .where(WorkflowInstance.workflow_id == workflow_id)
        .values(status=status, error_message=error_message)
    )
    db.commit()
    return True
