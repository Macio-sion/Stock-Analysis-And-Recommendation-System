"""SQLAlchemy ORM 模型（7 张表）。

对应《节点状态信息与运行时数据持久化设计》中的表结构。
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


class WorkflowInstance(Base):
    """工作流实例表（档案卡）。"""

    __tablename__ = "workflow_instances"

    workflow_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str | None] = mapped_column(String(32))  # pending/running/stage1_done/completed/failed
    current_phase: Mapped[str | None] = mapped_column(String(16))  # stage1/stage2/stage3
    strategy_type: Mapped[str | None] = mapped_column(String(32))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class AgentStateSnapshot(Base):
    """Agent 状态快照表（工作底稿）。"""

    __tablename__ = "agent_state_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[str] = mapped_column(String(64), ForeignKey("workflow_instances.workflow_id"))
    agent_name: Mapped[str | None] = mapped_column(String(32))
    phase: Mapped[str | None] = mapped_column(String(16))
    state_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    is_latest: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    """最终推荐报告表（结果）。"""

    __tablename__ = "recommendations"

    workflow_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("workflow_instances.workflow_id"), primary_key=True
    )
    symbol: Mapped[str | None] = mapped_column(String(16))
    action: Mapped[str | None] = mapped_column(String(16))  # buy/hold/sell
    score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    reasoning: Mapped[str | None] = mapped_column(Text)
    report_full: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class CustomAlgorithm(Base):
    """自定义算法脚本库。"""

    __tablename__ = "custom_algorithms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("workflow_instances.workflow_id"))
    algorithm_name: Mapped[str | None] = mapped_column(String(128))
    source_type: Mapped[str | None] = mapped_column(String(32))  # llm_generated/user_written
    code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow)


class AlgorithmExecution(Base):
    """算法执行记录。"""

    __tablename__ = "algorithm_executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    custom_algorithm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("custom_algorithms.id")
    )
    status: Mapped[str | None] = mapped_column(String(32))  # compiling/running/success/failed
    exit_code: Mapped[int | None] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    result_json: Mapped[dict | None] = mapped_column(JSONB)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class ExecutionLog(Base):
    """算法执行日志流。"""

    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("algorithm_executions.id")
    )
    seq: Mapped[int | None] = mapped_column(Integer)
    level: Mapped[str | None] = mapped_column(String(16))
    message: Mapped[str | None] = mapped_column(Text)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime)


class MetricSeries(Base):
    """算法执行指标序列。"""

    __tablename__ = "metric_series"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("algorithm_executions.id")
    )
    metric_name: Mapped[str | None] = mapped_column(String(64))
    step: Mapped[int | None] = mapped_column(Integer)
    value: Mapped[float | None] = mapped_column(Numeric(18, 6))
    timestamp: Mapped[datetime | None] = mapped_column(DateTime)
